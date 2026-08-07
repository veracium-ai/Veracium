# Feature spec: outcome authorship is append-only history

Spec-Status: in review
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v2)** — round-1 external review **approved the append-only-history
> direction** and deferred on 4 design gaps + 3 corrections; v2 closes all seven at
> root (§11): an atomic Store CAS chain-append primitive (§4a), a separately-named
> store commit order for cross-chain `last_outcome`/`last_outcome_at` (§4b), import
> that **validates-or-refuses** (never repairs) with a full topology preflight (§4c),
> the `SCHEMA_VERSION`/`FORMAT_VERSION` namespace split (§9a), `seq` made outcome-only
> (§2/§4), cross-user remap of `supersedes_episode` (§4c), and the frozen
> same-chain invariant payload (§4d). Split out of `0002` M4 on 2026-08-01. **All open
> questions ruled** (H-Q1 per-chain `seq`; H-Q2 head DERIVED; H-Q3 no release note),
> and **both `Spec-Requires:` prerequisites (`0007`, `0013`) accepted AND implemented**
> (§9).

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v2 |
| **Status** | *see `Spec-Status:` — canonical.* Split from `0002` §M4/§7a. |
| **Internal reviewers** | research — pending |
| **External review** | required — `__init__.py` is guarded; **`0002`'s second review required head/concurrency semantics before acceptance** |
| **Decision + date** | **round 1 returned 2026-08-07: direction approved, deferred on 4 gaps + 3 corrections; v2 closes all seven (§11)** |
| **Path** | full |
| **Prerequisite** | **`specs/0007`** + **`specs/0013`** — both accepted + implemented, see §9 |

---

## 1. Problem and motivation

**`record_outcome` still erases the authorship it was fixed to preserve.**

0.4.5 shipped M4 as *"outcome authorship is no longer overwritten"*. What it
actually does (`__init__.py:568-573`) is append a phrase to the episode summary
and then **overwrite the structured field anyway**:

```python
was = prior.provenance.author_of_evidence
if was != author:
    summary += f" [prior judgment was {was.value}-authored]"
prior.provenance.author_of_evidence = author
```

**`summary` is rebuilt from scratch on every upgrade**, so the note is
overwritten rather than accumulated. Measured:

```
initial (system)      author=system  (system) unreviewed: use of 'works_as: CFO'
after challenged      author=system  (system) challenged: ...
after corrected(user) author=user    (user) corrected: ... [prior judgment was system-authored]
after 2nd challenged  author=system  (system) challenged: ... [prior judgment was user-authored]
```

**`system → user → system` reduces to *"prior was user"*.** The chain of custody
survives exactly one hop, and the structured field never survives at all.

**Two things are wrong, and only one was reported.** The known one: a note is
prose — it cannot be queried, gated on, exported as structure, or read by a
later maintenance operation, **in a system whose stated principle is
supersession-never-erasure.** The one found by demonstrating it: **the note is
destroyed by construction on the next upgrade**, so even the prose claim is
false beyond one step.

**Severity, stated honestly:** the host supplies `actor` in both directions, so
this is **provenance destruction, not escalation** — nobody gains trust they
should not have. It is a *history* defect. That is why it carried no advisory
and should not now.

**Alternatives rejected.**

- **The note** (shipped). Above.
- **A `prior_author` field on the episode.** One hop of history in a fixed slot;
  the same defect with a schema change attached.
- **Never upgrade — always append.** Close to the answer, and it loses the
  `(edge_id, evidence_ref)` identity that makes `times_used` meaningful. **The
  chain keeps both** by making the head explicit.

---

## 2. Field contracts touched

| field | change | contract |
|---|---|---|
| `Episode.provenance.author_of_evidence` | **stops being overwritten** | who made **this** judgment — now true of every episode in the chain |
| **`Episode.supersedes_episode`** | **NEW**, optional | the episode this judgment revises; forms the chain. `None` on a chain root and on every non-outcome episode |
| **`Episode.seq`** | **NEW**, optional, **outcome-only**, store-assigned per-chain int | **per-chain authority ordering.** Set **only** when `kind == "outcome"` (Correction A): required positive int on an outcome episode (root `seq = 1`), `None` on every non-outcome episode. Never host-supplied — §4 |
| **`Episode.committed_seq`** | **NEW**, optional, **outcome-only**, store-assigned **store-wide** monotonic int | **cross-chain recency ONLY** (B2) — a *separately named* order, distinct from the per-chain authority `seq`, used solely to define `Edge.last_outcome`/`last_outcome_at`. Does not widen `seq`'s contract (H-Q1 pre-authorised "a separately named append log, not a widened `seq`") |
| `Episode.outcome` | unchanged | the judgment |
| `Edge.outcome_counts` / `times_used` | unchanged in meaning | derived from the **head** of each chain; `times_used` counts distinct `(edge_id, evidence_ref)` chains |
| `Edge.last_outcome` / **`last_outcome_at`** | **redefined** (B2) | **both** derived from the head of the chain whose head has the greatest `committed_seq`; `last_outcome_at` is that head's event timestamp. Ordered by store `committed_seq`, never host `date` |
| **`SCHEMA_VERSION`** (on-disk) | **current → next** | on-disk store shape (`PRAGMA user_version`) — the new `Episode` fields land here. **This is what `0013` migrates.** §9a |
| **`FORMAT_VERSION`** (export wire) | **2 → 3** | portable JSONL representation — exports gain `seq`/`supersedes_episode`/`committed_seq`. **`0007` §8: a namespace independent of `SCHEMA_VERSION`** (both `2` today by coincidence). §9a |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **host `date`** on `record_outcome` | defaults today | `_event_dt` → now | — | **back- or future-dated to win ordering** | **H2 — `seq`, not `date`, decides the head.** A host timestamp must never decide authority |
| **host `actor`** | defaults `system` | — | validated against outcome | mislabelled judgment | recorded per-episode and **never overwritten** — H1 |
| **`evidence_ref`** | required | — | — | reused across unrelated uses to force a merge into one chain | ⚠️ **no invariant** — `(edge_id, evidence_ref)` is the identity by design; a host colliding them merges its own records |
| **imported chain** | — | rejected | — | **two episodes claiming the same head**, a branch, or a cycle | **H4/H5** — import **validates or refuses; it never repairs** (B3): a valid chain is preserved exactly and its head re-derived; any structural ambiguity is refused **before any chain record is persisted** (§4c) |

> **Per the §2c rule** *(research, 2026-08-01)*: this spec relies on **`(edge_id,
> evidence_ref)`** from that table. It is safe to rely on here because it selects
> *which chain* and never *who wins within one* — that is `seq`, which the host
> cannot set.

## 2c-ii. Assertions about reach

| assertion | command | result |
|---|---|---|
| the note is rebuilt each upgrade | read `__init__.py:554,573` | `summary = f"..."` then `prior.summary = summary` |
| the structured field is overwritten | `__init__.py:572` | `prior.provenance.author_of_evidence = author` |
| `record_outcome` is not an MCP tool | `grep -n "@server.tool" src/veracium/mcp_server.py` | absent — host API |
| episodes tolerate unknown fields | `Episode.model_config["extra"]` | **`ignore`** — see §9 |

---

## 3. Trust-class matrix

**No trust class changes**, and the matrix is recorded rather than omitted
because the omission is what let this look small. **Every author class must be
preserved identically** — the defect is class-independent, and a fix that
preserved only `user` authorship would pass a naive test.

| chain | after |
|---|---|
| `system → user` | both retained, head `user` |
| `user → system` | both retained, head `system` |
| `third_party → user` | both retained, head `user` |
| any → any, 3+ links | **all** retained — the case the shipped note fails |

---

## 4. Behaviour

> The original outcome episode is **never mutated**. A judgment writes a **new**
> episode carrying its own `author_of_evidence`, event timestamp and outcome,
> with `supersedes_episode` set to the episode it revises. The **head** of a
> chain is the episode with the **highest store-assigned per-chain `seq`**;
> `outcome_counts` and the scalar `last_outcome`/`last_outcome_at` derive from heads.

**The head is DERIVED, never materialised (H-Q2).** There is no head pointer on
the edge; the aggregates are computed from the max-`seq` episode of each chain at
read time. The chain is the single source of truth, so the head can never silently
disagree with it — the failure this spec exists to prevent.

**`seq` is per-chain — scoped to one `(edge_id, evidence_ref)`** — and **assigned
by the store, never by the host.** The second external review's requirement, and it
is the same rule as `0008`'s: *a host-controlled timestamp must not decide
authority.* Two hosts with skewed clocks would otherwise reorder each other's
judgments.

### 4a. The atomic head transition is a Store primitive, not a Python loop (round 1, finding 1)

The compare-and-set head transition is load-bearing (H3: no branching under
concurrency) — but the current `Store` interface has only `add_episode` /
`episodes` / `delete_episode`, and the SQLite `add_episode` is `INSERT OR REPLACE`
(a one-row upsert). **That cannot atomically establish** that the observed head is
still current, that `seq` is the chain's next value, that the new row *inserts* (not
replaces), and that no concurrent sibling appeared. Leaving it to a higher-level
Python read-then-write is exactly the "SQLite trick" the reviewer guide forbids — a
second writer can interleave between the read and the insert and branch the chain.

> **Frozen: a new `Store` primitive, `@store_mutator`.**
> ```
> append_outcome_if_head(
>     user_id, edge_id, evidence_ref,
>     expected_head_id,          # None ⇒ this is the chain's first link
>     judgment_without_seq,      # author, event ts, outcome, ...
> ) -> AppendedEpisode | HeadMoved
> ```
> The **store**, in ONE atomic operation: (1) resolves the exact
> `(user_id, edge_id, evidence_ref)` chain; (2) verifies `expected_head_id` is
> still its head (else returns `HeadMoved`); (3) assigns the next per-chain `seq`
> **and** the next store-wide `committed_seq`; (4) **INSERTs** the new episode —
> never replaces; (5) sets `supersedes_episode = expected_head_id`. The caller
> **retries on `HeadMoved`.** **H3 tests this primitive with concurrent callers**,
> not merely the Python loop.

**The stored `Edge` aggregate fields are a DERIVED view, not a second source of
truth.** `Edge.outcome_counts`, `last_outcome`, `last_outcome_at` and `times_used`
exist on the `Edge` model today, but under this spec they are **recomputed from chain
heads** (H-Q2) — the chain is authoritative and any persisted copy is a **cache**
carrying H-Q2's reconcile-or-refuse obligation. So there is no independent aggregate
to fall out of sync: a crash after the insert leaves the chain as the single truth
and the next read recomputes. **If an optimisation keeps the persisted copy, its
refresh MUST be in this same atomic operation** (`append_outcome_if_head`), or it can
disagree with the committed chain after a crash — the exact denormalisation the M4
defect was.

### 4b. Cross-chain recency needs a separately named store order (round 1, finding 2)

`outcome_counts` (count each chain head's outcome) and `times_used` (count distinct
`(edge_id, evidence_ref)` chains) are well-defined from an unordered set of heads.
**A single `Edge.last_outcome` is not** — with two chains whose heads are `confirmed`
(use-A `seq 2`) and `challenged` (use-B `seq 1`), the per-chain `seq` values are
deliberately incomparable (H-Q1), so nothing says which is "last." Today's field
means "the outcome of the most recent `record_outcome` call" — a cross-chain order
the per-chain `seq` cannot supply. `Edge.last_outcome_at` has the identical problem
and v1 did not mention it at all.

> **Frozen (Option B — chosen; A and C recorded as rejected).** The store assigns a
> **store-wide monotonic `committed_seq`** to every outcome episode as it commits —
> a *separately named* order, **distinct from the authority-bearing per-chain
> `seq`** (H-Q1 explicitly reserves "a separately named append log" for exactly a
> store-wide order). Then:
> ```
> last_outcome    = outcome of the head whose head.committed_seq is greatest
> last_outcome_at = that same head's event timestamp
> ```
> Ordering is by store `committed_seq`, **never by host `date`** — the same rule that
> keeps `date` from deciding within-chain authority. **Rejected: (A)** dropping the
> scalar — it is a shipped, recall-surfaced field; **(C)** ordering by event time —
> the host controls `date`. `committed_seq` widens no authority: it decides only
> *recency of display*, never *who wins within a chain*.

**Counters follow the head, not the chain length.** A chain of five judgments about
one use is still one use. **This is the part most likely to regress**, since today's
upgrade path mutates counters in place.

### 4c. Import validates or refuses — it never repairs (round 1, finding 3)

v1 said a malformed import "repairs to a single head or refuses," contradicting H5's
"refuses rather than guessing." **H5 is the correct rule.** A branch
(`root → A`, `root → B`) is not a stale cache to repair — picking the max-`seq` leaf
leaves the durable graph still branched at `root`; a genuine "repair" would have to
**delete**, **relink**, or **invent** a joining judgment, each of which mutates or
fabricates supposedly append-only history. A cycle is less repairable still. Because
the head is derived (H-Q2), there is no materialised head pointer to "fix."

> **Frozen: validate-or-refuse, preflight before persist.** A "chain" here is the set
> of **outcome** episodes (`kind == "outcome"`) sharing one `(user_id, edge_id,
> evidence_ref)`; non-outcome episodes carry no `seq`/`supersedes_episode` (§4d, H8)
> and are not part of any chain. Import runs a full topology check on each incoming
> chain **before writing any of its records** (the current importer writes
> sequentially, so a bad later record could otherwise commit after earlier ones). A
> chain is accepted only if **all** hold; any failure **refuses the whole chain,
> writing nothing:**
> ```
> every episode in the chain has kind == "outcome"
> every non-root supersedes_episode exists
> predecessor is same user AND same (edge_id, evidence_ref) chain
> exactly one root within the chain (supersedes_episode == None)
> no cycle · no branch · exactly one leaf/head
> seq unique within the chain
> seq strictly increases along every supersession edge
> the max-seq record is the unique leaf
> ```
> A valid chain is **preserved exactly** and its head/counters **recomputed** —
> recomputing a derived value from valid source is not "repair."

> **Cross-user import remaps `supersedes_episode` (Correction B).** A cross-user
> import is a COPY that mints fresh ids and remaps references; today `portability`
> remaps `edge.supersedes` and `episode.edge_id` but **not** the new episode→episode
> ref. A v3 export imported under a different `user_id` MUST remap
> `Episode.supersedes_episode` through the same id-map, or the copied child points
> back at the *source* store's episode id. **H4 includes a cross-user remap fixture.**

### 4d. What makes every link "the same chain" — the frozen invariant payload (round 1, correction C)

For a chain to remain **one use**, the structural fields that define that use must
not drift link-to-link. A later judgment is a new episode with its own
`author_of_evidence`, event timestamp, `outcome`, and `supersedes_episode` — but the
following are **invariant across the whole chain** and are what import (§4c) and the
CAS primitive (§4a) check to decide a link belongs to one use:

```
user_id             identical throughout the chain
edge_id             identical throughout the chain
evidence_ref        identical throughout the chain   (provenance.evidence_ref)
supersedes_episode  the predecessor IN THIS chain (or None at the root)
```

`context_ref` is **root/use metadata**: it is set at the chain root and **inherited
unchanged** by every later judgment (a judgment revises the *outcome* of a use, not
which use it was). A later link presenting a different `context_ref` is a malformed
chain and is refused by §4c.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **H1** no episode's `author_of_evidence` is ever overwritten | `test_outcome_authorship_is_never_overwritten` — the measured `system → user → system` case becomes the fixture | CI |
| **H2** `seq` decides the head; a host `date` cannot reorder | `test_a_backdated_judgment_does_not_become_the_head` | CI |
| **H3** exactly one head per `(edge_id, evidence_ref)` — enforced **at the Store primitive** | `test_append_outcome_if_head_is_atomic` — **N concurrent callers of `append_outcome_if_head`** (not the Python loop) branch nothing; losers get `HeadMoved` and retry (finding 1) | CI |
| **H4** a valid chain imports preserved, head re-derived; a cross-user import remaps `supersedes_episode` | `test_import_preserves_the_outcome_chain` + `test_cross_user_import_remaps_supersedes_episode` (correction B) | CI |
| **H5** malformed imported topology **refuses before persisting anything** | `test_malformed_import_refuses_atomically` — parametrised over **branch, cycle, missing parent, cross-chain link, duplicate `seq`, non-increasing `seq`, no root, two leaves**; asserts **no partial write** (finding 3) | CI |
| **H6** all four aggregates are correct | `test_all_edge_aggregates_follow_heads` — `times_used`, `outcome_counts`, `last_outcome`, **`last_outcome_at`**; the last two ordered by `committed_seq` across chains (finding 2) | CI |
| **H7** history is **structurally queryable**, not prose | `test_prior_authorship_is_queryable_without_parsing_a_summary` — asserts against fields; **a passing prose note must fail this** | CI |
| **H8** `seq`/`supersedes_episode`/`committed_seq` are **outcome-only** | `test_non_outcome_episode_has_no_seq` — a plain episode round-trips with all three `None`; a root outcome is `seq == 1`, `supersedes_episode is None` (correction A) | CI |
| **H9** cross-chain recency is store-ordered, not date-ordered | `test_last_outcome_uses_committed_seq_not_date` — a back-dated judgment in a newer-committed chain still wins `last_outcome`; per-chain `seq` values across chains stay incomparable (finding 2) | CI |

**H7 is written to fail the shipped fix.** `0002`'s N5 said *"retains the prior
value"*, which the note technically satisfies — the second review flagged that
wording as broad enough to permit another note. **H7 closes it by asserting on
structure.**

---

## 7. Failure modes and reversibility

**Not reversible in the data**: once chains exist, reverting the code leaves
episodes an older build reads as unrelated records — it ignores
`supersedes_episode`, `seq` and `committed_seq` (`extra="ignore"`) and treats every
link as a separate outcome, **inflating `outcome_counts`**. This is exactly why the
change lands behind `0007`'s `SCHEMA_VERSION` stamp (§9): an older build **refuses**
the newer store rather than silently flattening it. See §9.

**Failure mode of the change itself** is a mis-picked head — a stale current
outcome, visible and correctable — against today's **silent loss of authorship**.

---

## 8. Claims and limits

**Claim:** who made each judgment is recorded and never overwritten.

**Limits:**

- **Not verification.** The host supplies `actor`; we record it faithfully and
  do not authenticate it. **`0008`'s principle applies:** this is a record, not
  an authority — and nothing keys authority on it.
- **Not conflict resolution.** One head wins; genuinely concurrent contradictory
  judgments are ordered, not reconciled. Surfacing that contention is
  `0002` Q1(3)'s territory.
- **Not retroactive.** Existing single episodes become one-link chains; the
  authorship already destroyed is not recoverable.

---

## 9. Prerequisite: `specs/0007`

**Verified, not assumed:**

```
>>> Episode.model_config.get("extra")
'ignore'          # pydantic default
>>> Episode.model_validate({... , "seq": 7, "supersedes_episode": "ep-1"})
parses fine, both fields silently dropped
```

**So an older build opening a store written by this change does not fail — it
succeeds and reads a flattened history**, treating each link as an independent
outcome. **That is worse than refusing**, because it presents an incorrect
outcome record as a complete one.

**`0007` (on-disk `PRAGMA user_version`) is what makes that refuse instead.**
This is the second spec to need it — `0006` was the first — and it is a
**stronger** argument than `0006`'s, because here the silent-misread path is
demonstrated rather than hypothetical.

> **UPDATE 2026-08-07: the prerequisite is SATISFIED.** `0007` is `accepted`
> (2026-08-03) **and implemented** — a store carries `PRAGMA user_version`, so an
> older build opening a newer store refuses (`newer`) instead of silently
> misreading. `0013` (migrations) is `accepted` (2026-08-07) **and its offline
> migration operation is implemented** (`0008` was its first production use), so the
> on-disk shape change this spec adds (`seq`, `supersedes_episode`, `committed_seq`)
> lands through the accepted **`SCHEMA_VERSION`** v→v+1 migration path, not a naked
> `ALTER`. Both `Spec-Requires:` deps are met.

### 9a. Two version namespaces, not one (round 1, finding 4)

**`SCHEMA_VERSION` and `FORMAT_VERSION` are different counters and `0009` changes
both.** v1 wrote "`FORMAT_VERSION 2→3` / schema change ... lands through `0013`" — but
`0007` §8 holds these are **independent** namespaces and `0013` migrates the
**on-disk** one:

| counter | what it versions | source | `0009`'s change | who migrates it |
|---|---|---|---|---|
| **`SCHEMA_VERSION`** | on-disk store shape (`PRAGMA user_version`) | `store/schema_version.py` (`= 2`) | the new `Episode` columns (`seq`, `supersedes_episode`, `committed_seq`) | **`0013`** (offline `v→v+1`) |
| **`FORMAT_VERSION`** | portable export/import wire format | `portability.py` (`= 2`) | the same new fields in a `.jsonl` export | `portability.py` version guard |

They are **coincidentally both `2` today**; that is not identity. The `0013` migration
prose refers to **`SCHEMA_VERSION`**, never `FORMAT_VERSION`.

**Each namespace shares with `0010` conditionally, per-namespace** (the sibling
consolidation spec changes the same two counters). For **each** version space a spec
changes, independently: **if `0009` and `0010` co-implement in one release**, they
compose into **one** `SCHEMA_VERSION` step **and** one `FORMAT_VERSION` revision; **if
either ships first**, it owns the next value in each space it changes and the sibling
takes the following value; **a released value in either namespace is never redefined
in place.** `0010` is a sibling, not a prerequisite.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~H-Q1~~ | **RULED 2026-08-01: per-chain.** *Global invites reuse as a general clock, which is how a field acquires an unintended contract* — and per-chain is **structurally un-repurposable**, since values from different chains are not comparable. A store-wide audit order, if ever needed, is a **separately named append log**, not a widened `seq`. **Live precedent:** `confidence` is a lifetime parameter that reads like a belief strength, and putting it in the scorer would retroactively change every merge rule. **A global `seq` is the same trap one field over.** | resolved | research | — |
| ~~H-Q2~~ | **RULED 2026-08-07 (dev): DERIVED.** The head is the episode with the highest `seq` in a chain, computed by query — there is NO materialised head pointer. A pointer would be a SECOND place the head-truth lives, and reconciling two sources of truth is exactly the denormalisation class of bug this spec exists to close: the shipped M4 defect was a counter mutated *in place* precisely because the value was stored where it was read instead of derived. Deriving keeps ONE truth — the chain — so the head cannot silently disagree with it. The cost is negligible at veracium's scale (per-user stores ~120 edges; per-`(edge_id, evidence_ref)` chains are a handful of judgments), and the head query is bounded by chain length, not store size. **If profiling ever shows the head lookup is hot, a materialised pointer is a later optimisation that MUST carry an explicit reconcile-or-refuse obligation (the pointer and the max-`seq` must be proven equal on every read that trusts the pointer) — it is not the default and is not needed now.** | resolved | dev | — |
| ~~H-Q3~~ | **RULED 2026-08-01 (Quentin): no release-note correction**, answered once for both specs. The gap is recorded here and in `0002` §11; the fix ships as this spec. **Not blocking.** | resolved | Quentin | — |

---

## 11. Review closure — round 1 (2026-08-07)

Round-1 external review: **"append-only-history direction approved; v2 deferred on
four load-bearing design gaps plus three contract corrections."** The reviewer
approved both requested design judgments (concurrent contradictory judgments are
*linearized, not reconciled*; and — narrowed — malformed imports **validate or
refuse**, never repair). The append-only architecture carries forward unchanged. v2
closes all seven at root; each was reproduced against source or spec text first.

### Blocking findings

| # | finding | root fix in v2 |
|---|---|---|
| **F1** | the atomic head transition had **no Store primitive** able to implement it — the interface has only `add_episode`/`episodes`/`delete_episode`, and SQLite `add_episode` is `INSERT OR REPLACE`, which cannot CAS the head, allocate `seq`, and insert-not-replace atomically | §4a freezes `append_outcome_if_head(...) -> AppendedEpisode | HeadMoved`: one atomic store op that resolves the chain, verifies the expected head, allocates per-chain `seq` + store-wide `committed_seq`, INSERTs, and sets `supersedes_episode`. H3 now tests the primitive under concurrency. |
| **F2** | per-chain `seq` cannot order the scalar `Edge.last_outcome` across chains (values from different chains are deliberately incomparable), and `last_outcome_at` was unmentioned entirely | §4b chooses **Option B**: a separately-named store-wide `committed_seq` (distinct from authority `seq`, pre-authorised by H-Q1) orders cross-chain recency; both `last_outcome` and `last_outcome_at` derive from the head with the greatest `committed_seq`. A and C rejected in text. H6 covers all four aggregates; H9 pins store-order-not-date. |
| **F3** | "repair or refuse" for malformed imports contradicted H5 and would require deleting/relinking/inventing append-only history | §4c freezes **validate-or-refuse, preflight before persist**: a full topology check (root/branch/cycle/leaf/`seq`/predecessor) runs before any record is written; a valid chain is preserved and its head re-derived, an invalid one refuses whole. H5 parametrised over every malformed shape + asserts no partial write. |
| **F4** | `FORMAT_VERSION` (export wire) and `SCHEMA_VERSION` (on-disk, what `0013` migrates) were conflated — `0007` §8 holds them independent; `0009` changes both | §9a splits them with a per-namespace conditional-`0010` share rule; `0013` prose refers to `SCHEMA_VERSION`. Verified `schema_version.py:167=2`, `portability.py:36=2`. |

### Contract corrections

| # | correction | v2 |
|---|---|---|
| **A** | `Episode.seq` was an unconditional field, but most episodes are not outcome judgments | §2/§4/§4d: `seq`, `supersedes_episode`, `committed_seq` are **outcome-only** — `None` on non-outcome episodes; a root outcome is `seq == 1`, `supersedes_episode is None`. Invariant H8. |
| **B** | cross-user import must remap the new `Episode.supersedes_episode` (today `portability` remaps `edge.supersedes` + `episode.edge_id` only) | §4c requires remapping `supersedes_episode` through the same id-map; H4 adds a cross-user fixture. |
| **C** | "same chain" was undefined, so import/CAS could not tell whether a link belongs to one use | §4d freezes the invariant payload: `user_id`/`edge_id`/`evidence_ref` identical throughout, `supersedes_episode` the in-chain predecessor, `context_ref` root-inherited (a differing later link is refused). |

**Not changed:** append-not-mutate, one immutable authorship per judgment, one chain
per `(edge_id, evidence_ref)`, store-assigned (not host-date) authority, per-chain
`seq`, derived head, no branching, linearize-not-reconcile, structural H7. The reviewer's
own v2 acceptance bar is F1–F4 + A–C; all seven are closed here.
