# Feature spec: outcome authorship is append-only history

Spec-Status: in review
Spec-Requires: 0007, 0013

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v4)** — rounds 1–3 all **approved the append-only-history architecture**;
> round 3 also **approved Option A** (deprecate the scalars in place) and the
> deprecate-not-remove product call. Round 3 deferred on 4 compatibility/import gaps +
> 3 corrections (closed v4, §13): `OutcomeJudgmentDraft` now carries the **complete**
> caller payload incl. `corrected_value`, and omitted `context_ref` **inherits** (§4a);
> the v2→v3 migration **refuses duplicate chain identities** rather than making two roots
> (§4f); the same honest conversion covers **legacy portable imports** (§4f-ii, H13);
> import is a **whole-file preflight** so H5's no-partial-write holds (§4c); plus
> `judgment_time_known` in both version rows, the stale "scalars derive from heads" line
> removed, and the §2c-ii coordinates corrected. Split from `0002` M4. **Open questions
> ruled**; **both `Spec-Requires:` prerequisites (`0007`, `0013`) accepted AND
> implemented** (§9).

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v4 |
| **Status** | *see `Spec-Status:` — canonical.* Split from `0002` §M4/§7a. |
| **Internal reviewers** | research — pending |
| **External review** | required — `__init__.py` is guarded; **`0002`'s second review required head/concurrency semantics before acceptance** |
| **Decision + date** | **rounds 1–3 returned 2026-08-07: architecture approved all three; v2/v3/v4 closed them (§11/§12/§13); round 3 = 4 gaps + 3 corrections** |
| **⚠ product call for Quentin** | v4 **deprecates** `Edge.last_outcome`/`last_outcome_at` in place (Option A). **The round-3 reviewer endorsed deprecate-not-remove** as the better migration path. Still open only: **if an external consumer relies on either as a cross-chain scalar**, say so and I'll restore a properly-contracted Option B — otherwise Option A stands. |
| **Path** | full |
| **Prerequisite** | **`specs/0007`** + **`specs/0013`** — both accepted + implemented, see §9 |

---

## 1. Problem and motivation

**`record_outcome` still erases the authorship it was fixed to preserve.**

0.4.5 shipped M4 as *"outcome authorship is no longer overwritten"*. What it
actually does (`__init__.py:587-591`) is append a phrase to the episode summary
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
| **`Episode.seq`** | **NEW**, optional, **outcome-only**, store-assigned per-chain int | **per-chain authority ordering.** Set **only** when `kind == "outcome"` (Correction A, round 1): required positive int on an outcome episode (root `seq = 1`), `None` on every non-outcome episode. Never host-supplied — §4. **The only store-assigned ordering field (Option A, round 2 — `committed_seq` is removed).** |
| `Episode.outcome` | unchanged | the judgment |
| **`Episode.judgment_time_known`** | **NEW**, optional, migration-compat | `True` (or unset) on any outcome episode written on/after v3 — its `date` is the real judgment time (H1). **`False` on a legacy root** migrated from a pre-v3 in-place record, whose `date` is the original use date, not the judgment time (§4f, H12). Never fabricate a judgment time; label it unknown instead |
| `Edge.outcome_counts` / `times_used` | unchanged in meaning | derived from the **head** of each chain; `times_used` counts distinct `(edge_id, evidence_ref)` chains. Neither needs a cross-chain order (a set of heads suffices) |
| `Edge.last_outcome` / `last_outcome_at` | **DEPRECATED (Option A, round 2)** | **No cross-chain recency contract.** A single scalar "the most recent judgment across all uses" would need a store-wide order the per-chain `seq` deliberately withholds; round 1's Option B built one (`committed_seq`) to preserve these fields, but they are **not recall-rendered** (`compile.py` emits no edge outcome field), so B's machinery is dropped. The fields remain on `Edge` for wire back-compat but are **not authoritative** and carry no cross-chain guarantee; a real cross-chain "latest judgment" is a separate future spec that must first freeze a proper store-commit order. See §4b + the ⚠ product call. |
| **`SCHEMA_VERSION`** (on-disk) | **current → next** | on-disk store shape (`PRAGMA user_version`) — the new `Episode` fields (`seq`, `supersedes_episode`, **`judgment_time_known`**) land here. **This is what `0013` migrates** (§4f policy, §9a) |
| **`FORMAT_VERSION`** (export wire) | **2 → 3** | portable JSONL representation — exports gain `seq`/`supersedes_episode`/**`judgment_time_known`** (no `committed_seq` — Option A). **A migrated legacy root MUST export `judgment_time_known = False`**, or re-import would again mistake its use `date` for a known judgment time (§4f-ii). **`0007` §8: a namespace independent of `SCHEMA_VERSION`** (both `2` today by coincidence). §9a |

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
| the note is rebuilt each upgrade | read `__init__.py:572,591` | `summary = f"..."` then `prior.summary = summary` |
| the structured field is overwritten | `__init__.py:590` | `prior.provenance.author_of_evidence = author` |
| `record_outcome` is not an MCP tool | `grep -n "@server.tool" src/veracium/mcp_server.py` | absent — host API |
| episodes tolerate unknown fields | `Episode.model_config.get("extra")` | **`None`** (no explicit policy) → Pydantic **default is `ignore`**, so unknown `seq`/`supersedes_episode` are dropped — see §9 |

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
> chain is the episode with the **highest store-assigned per-chain `seq`**.
> `outcome_counts` and `times_used` derive from chain heads; `last_outcome` and
> `last_outcome_at` are **deprecated compatibility fields, not authoritative** and with
> no cross-chain guarantee (Option A, §4b — this replaces the stale Option-B line that
> said the scalars "derive from heads").

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
>     draft: OutcomeJudgmentDraft,
> ) -> AppendedEpisode | HeadMoved
> ```
> **`OutcomeJudgmentDraft` structurally excludes every store-owned field (round-2
> Correction B), and carries the COMPLETE caller payload (round-3 finding 1).** It
> excludes `seq`, `supersedes_episode`, and any caller-controlled episode `id` — making
> "store-assigned" a property of the *type*, so a caller-supplied `seq`/`id` cannot turn
> an append into a replace. But it must also carry everything `record_outcome` persists
> today, or the Store path silently drops shipped data:
> ```
> OutcomeJudgmentDraft:
>     author
>     event_timestamp
>     outcome
>     summary        # built by Memory.record_outcome BEFORE the Store boundary,
>                    #   INCLUDING corrected_value → "(true value: …)" (today
>                    #   __init__.py:571) — v2's draft dropped this, a data loss
>     context_ref    # inherit-on-omit, see below
> ```
> `corrected_value` is not store-owned; `Memory.record_outcome(corrected_value=…)`
> composes the summary and passes it in the draft. The store still owns `seq`/`id`.
>
> The **store**, in ONE atomic operation: (1) resolves the exact
> `(user_id, edge_id, evidence_ref)` chain; (2) verifies `expected_head_id` is
> still its head (else returns `HeadMoved`); (3) for a **non-root** append, resolves
> `context_ref`: **omitted (`None`) → inherit the chain's** (the public API reads
> omission as "leave the use metadata unchanged" — round-3 finding 1); a **non-`None`**
> value must **equal the chain's**, else reject (a judgment revises an outcome, not which
> use it was — §4d; clearing is never a valid chain op);
> (4) assigns the next per-chain `seq` **and mints a fresh episode `id`**;
> (5) **INSERTs** the new episode — never replaces; (6) sets
> `supersedes_episode = expected_head_id`; (7) **advances the user's `store_version` in
> the same transaction** (H10, round-2 finding 4 — see below). The caller **retries on
> `HeadMoved`.** **H3 tests this primitive with concurrent callers**, not merely the
> Python loop.

> **`append_outcome_if_head` MUST advance `store_version` atomically (round 2, finding
> 4 — H10).** An outcome episode is ordinary compiled-wiki input (it is not
> third-party-only), and `outcome_counts` feed rendered edge state, so a committed
> append **changes memory a later recall/compile reads**. `@store_mutator` is only an
> audit-manifest marker — it does **not** bump the counter (the same distinction the
> `0010` review drew: `set_wiki` is a mutator that deliberately does not `_bump`).
> Existing `add_episode` bumps `store_version` explicitly; this custom primitive must
> do the same, in the same atomic transaction, or a cached wiki stays "fresh" after its
> source changed. If a persisted `Edge` aggregate cache is refreshed in the same
> transaction, one counter advance covers the whole logical mutation.

**The authoritative `Edge` aggregates are a DERIVED view, not a second source of
truth.** `Edge.outcome_counts` and `times_used` are **recomputed from chain heads**
(H-Q2) — the chain is authoritative and any persisted copy is a **cache** carrying
H-Q2's reconcile-or-refuse obligation. So there is no independent aggregate to fall
out of sync: a crash after the insert leaves the chain as the single truth and the
next read recomputes. **If an optimisation keeps the persisted copy, its refresh MUST
be in this same atomic operation** (`append_outcome_if_head`, which also advances
`store_version`), or it can disagree with the committed chain after a crash — the exact
denormalisation the M4 defect was. (`last_outcome`/`last_outcome_at` are deprecated
under Option A, §4b — not part of the authoritative derived set.)

### 4b. Cross-chain recency: Option A — deprecate the scalar (round 2, finding 1)

`outcome_counts` (count each chain head's outcome) and `times_used` (count distinct
`(edge_id, evidence_ref)` chains) are well-defined from an **unordered** set of heads —
no cross-chain order is needed. **A single `Edge.last_outcome` scalar is different:**
with two chains whose heads are `confirmed` (use-A `seq 2`) and `challenged` (use-B
`seq 1`), the per-chain `seq` values are deliberately incomparable (H-Q1), so "which is
last?" has no answer without a *store-wide* order the authority model withholds.

**Round 1 chose Option B** — a new store-wide `committed_seq` — to keep the scalar.
**Round 2 withdraws B for Option A**, for two reasons the round-2 review established:

1. **B's motivation was factually wrong.** B was justified as preserving a
   "recall-surfaced" field, but `last_outcome`/`last_outcome_at` are **not rendered by
   recall** — `compile.py` emits no edge outcome field; the scalar is written
   (`__init__.py:604`) and lives on the `Edge` model, but no recall/compile path reads
   it. They are shipped **API** state, not shown state.
2. **B was not closed under its own surfaces.** A store-wide order has to survive
   **portable import** (an imported `committed_seq` would let the *source file* decide
   destination recency — §1a), **concurrent cross-chain commits** (max-integer ≠
   commit-order unless allocation is commit-linearized — §1b), and **legacy migration**
   (the old in-place representation records no historical commit order to backfill —
   §4g). That is a large contract for a field nothing displays.

> **Frozen: Option A.** **`committed_seq` is removed.** `Edge.last_outcome` and
> `last_outcome_at` are **DEPRECATED**: they remain on the `Edge` model for wire
> back-compat but carry **no cross-chain recency guarantee** — the spec makes no claim
> about which chain's judgment they reflect, and no store-wide order is introduced to
> define one. **The append path MAY continue to set them best-effort to the
> just-appended judgment** (as `__init__.py:604` does today — a within-call
> convenience), but **no reader may rely on a cross-chain meaning**; they are not in
> the authoritative derived set and are candidates for removal in a later major
> version. `outcome_counts` and `times_used` (which need no order) remain the
> authoritative derived aggregates. **If a genuine "latest judgment across all uses" is
> ever required, it is a separate spec** that must first freeze a proper store-commit
> order (destination-local import reallocation, concurrent commit-linearization, and
> honest legacy backfill — everything B would have owed). See the ⚠ product call: this
> is safe on the evidence in this snapshot; only an undocumented external consumer of
> the scalar would change it.

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

> **Frozen: validate-or-refuse, WHOLE-IMPORT preflight before the first write (round 3,
> finding 4).** H5 promises "no partial write," which per-chain preflight does not give:
> a file with a valid chain A and a malformed chain B could write A, then reject B,
> leaving A persisted. So the **entire import plan** is parsed, remapped and validated
> **before any persistent write** — Edges too (an imported Edge could otherwise land
> before a later chain fails):
> ```
> 1. parse all Edge and Episode records
> 2. construct remapped ids (cross-user, § B below)
> 3. convert legacy FORMAT_VERSION-2 outcome records (§4f-ii)
> 4. validate all referenced Edges exist and belong to the target user
> 5. validate every incoming chain's topology (below)
> 6. validate every COMBINED destination chain (below)
> 7. ONLY THEN begin writing
> ```
> A "chain" is the set of **outcome** episodes (`kind == "outcome"`) sharing one
> `(user_id, edge_id, evidence_ref)`; non-outcome episodes carry no
> `seq`/`supersedes_episode` (§4d, H8). Per-chain topology — all must hold, else the
> **whole import refuses, writing nothing:**
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
> recomputing a derived value from valid source is not "repair." (This satisfies H5's
> no-partial-write without a cross-backend transaction API — it is a preflight, not a
> rollback.)

> **Validate the COMBINED destination graph, not just the incoming chain (round 2,
> finding 3).** A v2 preflight that checks only the incoming topology can still branch
> the destination: an incoming chain valid in isolation (`I1`, `seq 1`, root) merged
> into a destination that already has a chain for the same `(edge_id, evidence_ref)`
> (`D1`, `seq 1`, root) yields **two roots / two heads** — H3 false, from two
> individually-valid sources. So the check is against the **post-import** chain for each
> identity:
> ```
> destination has no chain for this identity   → a valid incoming chain may be inserted
> destination chain is an exact prefix          → idempotent records skipped; an incoming
>                                                 suffix is allowed ONLY if its first new
>                                                 link extends the current destination head
> any competing root / predecessor / divergent suffix → REFUSE
> ```
> (The conservative alternative — refuse every non-identical import into an existing
> chain identity — is also acceptable; v3 freezes the prefix-extend rule above.) The
> "identity" is compared **after** any cross-user remap: a cross-user import mints a
> fresh `edge_id`, so it forms a brand-new chain with no existing destination
> counterpart, and the combined-graph check applies to **same-user** re-import/merge.
> **And every outcome chain's `edge_id` MUST resolve to an existing `Edge` owned by the
> target user** — v2 proved links stay on one `edge_id` but never that the `Edge`
> exists at all. A chain referencing a missing or foreign-user `Edge` is refused.

> **Cross-user import remaps `supersedes_episode` (round 1, Correction B).** A
> cross-user import is a COPY that mints fresh ids and remaps references; today
> `portability` remaps `edge.supersedes` and `episode.edge_id` but **not** the new
> episode→episode ref. A v3 export imported under a different `user_id` MUST remap
> `Episode.supersedes_episode` through the same id-map, or the copied child points
> back at the *source* store's episode id. **H4 includes a cross-user remap fixture.**
> (Under Option A there is no `committed_seq` to reallocate on import — one of the
> import complications Option B would have added, §4b.)

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

### 4e. The rewrite preserves `record_outcome`'s existing side effects (round 2, correction A)

`record_outcome` is being rewritten around the chain, so its **existing** behaviour —
not part of the new feature but part of the function — must be preserved, or a
clean-room H1–H9 implementation could silently drop it:

> **Frozen (behaviour preserved, H11).**
> - **`challenged` sets `needs_confirmation`.** `outcome == challenged →
>   edge.needs_confirmation = True` (today `__init__.py:609`, an existing surface). This
>   flag update is written **in the same atomic transaction** as the challenged
>   judgment (via the append primitive's edge-cache refresh, §4a) — the durable chain
>   must never say "challenged" while its review flag is missing.
> - **actor/outcome pairing is unchanged:** `confirmed`/`corrected` require
>   `actor="user"`; `challenged`/`concurred` require `actor="system"` (today
>   `__init__.py:560-563`). A mispaired call still raises.

### 4f. The v2→v3 legacy migration policy (round 2, finding 2)

`0013` supplies the migration *mechanism*; this spec must supply the *transformation*.
The legacy representation is lossier than v2 admitted: the old in-place upgrade path
mutates `prior.outcome`/`author`/`summary` but **not `prior.date`**
(`__init__.py:577-593`), and writes the new judgment's time only to the **edge-wide**
`edge.last_outcome_at`. So a legacy episode physically holds the **original use date**
alongside the **latest** outcome/author, and earlier chains' judgment times are simply
gone.

> **Frozen: migration policy (on-disk `SCHEMA_VERSION`).**
> - **Group every existing outcome by `(user_id, edge_id, evidence_ref)` FIRST
>   (round-3 finding 2).** The pre-v3 store does **not** enforce one outcome per chain
>   identity — the importer dedups by episode `id` only (`portability.py:77,127`), so a
>   legal old store can hold two outcome episodes with the same `(edge_id,
>   evidence_ref)`. Rooting each at `seq=1` would create **two roots / two heads** — the
>   exact H3 violation the runtime forbids. So per group:
>   ```
>   exactly one outcome  → seq = 1, supersedes_episode = None, judgment_time_known = False
>   more than one        → REFUSE the migration — there is no trustworthy information to
>                          reconstruct which duplicate superseded which; do not invent an
>                          order or silently branch
>   ```
>   A refusal **aborts the migration and leaves the store at its prior version** (`0013`'s
>   migration-failure contract — nothing is partially converted); the operator resolves
>   the duplicate identities before retrying. Refusing is honest; branching is not.
> - **`date` is NOT reinterpreted as the judgment time.** A migrated legacy episode's
>   `date` is the original use date, which the old path never updated — so it is carried
>   forward unchanged and marked **`judgment_time_known = False`**. v3 must not present
>   the use date as though it were the known judgment timestamp; H1's "this episode
>   carries **this judgment's** event timestamp" holds for records written **on or
>   after** v3, and legacy roots are honestly labelled unknown-judgment-time.
> - **No synthetic ordering is fabricated.** Under Option A there is no `committed_seq`
>   to backfill — a concrete simplification the B→A switch buys.
> This is the feature-specific transformation `0013` provides machinery for but cannot
> invent on `0009`'s behalf. Invariant **H12**.

### 4f-ii. The SAME honest conversion for legacy FORMAT_VERSION-2 portable imports (round 3, finding 3)

§4f is the on-disk `SCHEMA_VERSION` transformation; **portable import is a different
namespace** (§9a). The existing importer accepts older `FORMAT_VERSION`s, and a
`FORMAT_VERSION-2` outcome record carries none of `seq` / `supersedes_episode` /
`judgment_time_known`. v3 bumped the format but never said how such a record converts
on import — leaving incompatible choices (reject all v2 exports? `seq=None`? `seq=1`
with a *known* date?), only one of which is consistent with H8/H12.

> **Frozen.** A legacy (`FORMAT_VERSION-2`) outcome record imported into a v3 store gets
> the **same honest conversion** as the on-disk migration:
> ```
> seq = 1 · supersedes_episode = None · judgment_time_known = False
> ```
> and is subject to the **same duplicate-chain-identity refusal** (§4f): a v2 export can
> contain two outcome records for one `(edge_id, evidence_ref)`, and that import refuses
> rather than branching. **This needs its own portability test** — the `SCHEMA_VERSION`
> migration tests never exercise the import path. Invariant **H13**.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **H1** no episode's `author_of_evidence` is ever overwritten | `test_outcome_authorship_is_never_overwritten` — the measured `system → user → system` case becomes the fixture | CI |
| **H2** `seq` decides the head; a host `date` cannot reorder | `test_a_backdated_judgment_does_not_become_the_head` | CI |
| **H3** exactly one head per `(edge_id, evidence_ref)` — enforced **at the Store primitive** | `test_append_outcome_if_head_is_atomic` — **N concurrent callers of `append_outcome_if_head`** (not the Python loop) branch nothing; losers get `HeadMoved` and retry (finding 1) | CI |
| **H4** a valid chain imports preserved, head re-derived; a cross-user import remaps `supersedes_episode`; import validates the **combined** destination graph and the referenced `Edge` exists | `test_import_preserves_the_outcome_chain` + `test_cross_user_import_remaps_supersedes_episode` + `test_two_valid_chains_same_identity_refuses` (a valid incoming chain merged onto an existing destination chain refuses, not branches — round-2 finding 3) + `test_import_refuses_missing_or_foreign_edge` | CI |
| **H5** malformed import **refuses before persisting anything** — WHOLE-import preflight (all Edges + all chains + combined + legacy conversions validated before the first write) | `test_malformed_import_refuses_atomically` — parametrised over **branch, cycle, missing parent, cross-chain link, duplicate `seq`, non-increasing `seq`, no root, two leaves, competing-destination-root, divergent-suffix**; **`test_valid_chain_A_not_written_when_later_chain_B_is_malformed`** (no partial write across chains — round-3 finding 4) | CI |
| **H6** the authoritative aggregates follow heads | `test_edge_aggregates_follow_heads` — `times_used` + `outcome_counts` recomputed from chain heads (no cross-chain order needed). `last_outcome`/`last_outcome_at` are deprecated (Option A) and out of scope | CI |
| **H7** history is **structurally queryable**, not prose | `test_prior_authorship_is_queryable_without_parsing_a_summary` — asserts against fields; **a passing prose note must fail this** | CI |
| **H8** `seq`/`supersedes_episode` are **outcome-only** | `test_non_outcome_episode_has_no_seq` — a plain episode round-trips with both `None`; a root outcome is `seq == 1`, `supersedes_episode is None` (round-1 correction A) | CI |
| **H9** the CAS draft **excludes store-owned fields but carries the complete caller payload** | `test_outcome_draft_has_no_store_owned_fields` (no `seq`/`supersedes_episode`/`id`) + `test_corrected_value_survives_the_store_boundary` — a `corrected_value` reaches the durable summary via the draft (round-2 correction B + round-3 finding 1) | CI |
| **H10** `append_outcome_if_head` **advances `store_version`** in the same atomic transaction | `test_append_outcome_bumps_store_version` — a cached wiki compiled before the append must not read fresh after it (round-2 finding 4; `@store_mutator` alone does not bump) | CI |
| **H11** the rewrite preserves the existing side effects incl. `corrected_value` and omitted-`context_ref` inheritance | `test_challenged_sets_needs_confirmation` (same txn) + `test_actor_outcome_pairing_still_raises` + `test_corrected_value_persisted` + `test_omitted_context_ref_inherits_not_rejects` — a non-root append with `context_ref=None` inherits the chain's, not a mismatch (round-2 correction A + round-3 finding 1) | CI |
| **H12** the v2→v3 migration is honest about legacy time AND refuses duplicate identities | `test_legacy_outcome_becomes_root_with_unknown_judgment_time` (`seq==1`, `supersedes_episode is None`, `judgment_time_known == False`, `date` not relabelled) + `test_migration_refuses_duplicate_chain_identity` — two pre-v3 outcomes for one `(edge_id, evidence_ref)` **refuse**, never become two roots (round-2 finding 2 + round-3 finding 2) | CI |
| **H13** legacy `FORMAT_VERSION-2` portable imports get the same honest conversion + duplicate refusal | `test_legacy_portable_outcome_import` — a v2 export outcome record imports as `seq==1`/`supersedes_episode==None`/`judgment_time_known==False`; a v2 export with a duplicate chain identity refuses (round-3 finding 3; a distinct path from the `SCHEMA_VERSION` migration) | CI |

**H7 is written to fail the shipped fix.** `0002`'s N5 said *"retains the prior
value"*, which the note technically satisfies — the second review flagged that
wording as broad enough to permit another note. **H7 closes it by asserting on
structure.**

---

## 7. Failure modes and reversibility

**Not reversible in the data**: once chains exist, reverting the code leaves
episodes an older build reads as unrelated records — it ignores
`supersedes_episode` and `seq` (`extra="ignore"`) and treats every
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
None              # no explicit policy set → Pydantic's DEFAULT applies, which is "ignore"
>>> Episode.model_validate({... , "seq": 7, "supersedes_episode": "ep-1"})
parses fine, both unknown fields silently dropped   # measured, not assumed
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
> on-disk shape change this spec adds (`seq`, `supersedes_episode`,
> `judgment_time_known`) lands through the accepted **`SCHEMA_VERSION`** v→v+1
> migration path (with the §4f transformation policy), not a naked `ALTER`. Both
> `Spec-Requires:` deps are met.

### 9a. Two version namespaces, not one (round 1, finding 4)

**`SCHEMA_VERSION` and `FORMAT_VERSION` are different counters and `0009` changes
both.** v1 wrote "`FORMAT_VERSION 2→3` / schema change ... lands through `0013`" — but
`0007` §8 holds these are **independent** namespaces and `0013` migrates the
**on-disk** one:

| counter | what it versions | source | `0009`'s change | who migrates it |
|---|---|---|---|---|
| **`SCHEMA_VERSION`** | on-disk store shape (`PRAGMA user_version`) | `store/schema_version.py` (`= 2`) | the new `Episode` columns (`seq`, `supersedes_episode`, `judgment_time_known`) | **`0013`** (offline `v→v+1`, §4f policy) |
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

---

## 12. Review closure — round 2 (2026-08-07)

Round-2 external review: **"append-only-history architecture remains approved; v3
deferred on four load-bearing design gaps plus two contract corrections."** The
reviewer confirmed all seven round-1 closures hold. The findings cluster on Option B's
`committed_seq` and on import/migration closure. Each was reproduced against source or
spec text first.

### The headline decision: Option B → Option A

Round 2 **recommended dropping the scalar (Option A)**, and supplied the evidence that
round 1's rationale for B was wrong: `Edge.last_outcome`/`last_outcome_at` are **not
recall-rendered** (`compile.py` emits no edge outcome field — verified), so B built an
entire store-wide ordering contract to preserve a field nothing displays. **v3 adopts
Option A** (§4b): `committed_seq` removed; the scalars deprecated with no cross-chain
guarantee. This **dissolves round-2 blocker 1 entirely** (1a import-reallocation, 1b
commit-linearization, 1c the false rationale) and **shrinks blocker 2** (no synthetic
legacy order to backfill). The one caveat only Quentin can close is recorded as the ⚠
product call: if an external consumer depends on the scalar, a properly-contracted B
returns.

### Blocking findings

| # | finding | root fix in v3 |
|---|---|---|
| **F1 (B1)** | `committed_seq` was not a coherent store-owned order: an imported value would let the source file decide destination recency (1a), max-integer ≠ commit-order under concurrency (1b), and its "recall-surfaced" motivation was false (1c) | **Option A** (§4b): remove `committed_seq`; deprecate the scalar. The whole surface disappears rather than being patched. |
| **F2 (B2)** | the v2→v3 migration had no data-transformation policy, and the legacy in-place record is lossy (`prior.date` was never updated; per-chain judgment times are gone) | §4f freezes the policy: legacy episode → root `seq=1`/`supersedes_episode=None`; its `date` is **not** relabelled the judgment time — marked `judgment_time_known=False` (new compat field) rather than fabricated. Invariant H12. |
| **F3 (B3)** | import validated only the incoming chain, so two individually-valid chains for one identity could merge into a branched destination (H3 false) | §4c validates the **combined** post-import graph (prefix-extend-or-refuse) and requires the referenced `Edge` to exist and belong to the target user. H4/H5 extended. |
| **F4 (B4)** | `append_outcome_if_head` had no `store_version` obligation, though an outcome episode feeds compiled recall — a cached wiki could stay "fresh" after an append | §4a freezes: the primitive **advances `store_version` in its atomic transaction** (`@store_mutator` alone does not bump — the `0010` distinction). Invariant H10. |

### Contract corrections

| # | correction | v3 |
|---|---|---|
| **A** | the rewrite must preserve `record_outcome`'s existing side effects — `challenged → needs_confirmation=True` and actor/outcome pairing — absent from the H1–H9 surface | §4e freezes both (the flag set in the same txn as the challenged judgment). Invariant H11. |
| **B** | the CAS input `judgment_without_seq` was an ordinary `Episode` with fields omitted by convention — a caller-set `seq`/`id` could turn append into replace | §4a replaces it with `OutcomeJudgmentDraft`, structurally excluding `seq`/`supersedes_episode`/`id`. Invariant H9 (repurposed). |

**Not changed:** append-not-mutate, per-chain authority `seq`, the derived head,
no-branching, linearize-not-reconcile, structural H7, cross-user `supersedes_episode`
remap, the same-chain payload, and the `SCHEMA_VERSION`/`FORMAT_VERSION` split. The
reviewer's v3 acceptance bar is items 1–7; all are closed here (with Option A as the
recommended resolution of item 1).

---

## 13. Review closure — round 3 (2026-08-07)

Round-3 external review: **"append-only-history architecture and Option A remain
approved; v4 deferred on four compatibility/import gaps plus three contract
corrections."** The reviewer **endorsed the deprecate-in-place product call** (keep
`last_outcome`/`last_outcome_at` for a compatibility cycle, remove only in a later
API-breaking release) — that design question is settled; only the "external consumer?"
fact remains Quentin's. Each finding was reproduced against source or spec text first.

### Blocking findings

| # | finding | root fix in v4 |
|---|---|---|
| **F1** | `OutcomeJudgmentDraft` dropped shipped payload: it carried no `summary`/`corrected_value` (today `record_outcome` persists `corrected_value` into the summary, `__init__.py:571`), and it turned an **omitted** `context_ref` on a non-root upgrade into a *mismatch* refusal | §4a: the draft carries `summary` (built by `Memory.record_outcome`, incl. `corrected_value`, before the Store boundary) while still excluding `seq`/`supersedes_episode`/`id`; a non-root `context_ref=None` **inherits** the chain's, non-`None` must equal it. H9/H11 extended. |
| **F2** | the migration rooted **every** legacy outcome at `seq=1`, but the pre-v3 store does not enforce one outcome per `(edge_id, evidence_ref)` (the importer dedups by episode `id` only, `portability.py:77,127`) — so duplicates become **two roots**, an H3 violation | §4f: group legacy outcomes by `(user_id, edge_id, evidence_ref)` first; exactly one → root; **more than one → REFUSE** (no trustworthy order to reconstruct). H12 extended. |
| **F3** | the honest legacy conversion existed only for the on-disk `SCHEMA_VERSION` migration, not for **`FORMAT_VERSION-2` portable imports** (a different namespace) — an old-format outcome record has no `seq`/`supersedes_episode`/`judgment_time_known` and v3 didn't say how it converts | §4f-ii: the **same** conversion (`seq=1`, `supersedes_episode=None`, `judgment_time_known=False`) + the same duplicate-identity refusal, with its **own** portability test. Invariant **H13**. |
| **F4** | H5 promised "no partial write," but §4c preflighted **one chain at a time**, so a valid chain A could persist before a malformed chain B was rejected | §4c: the **whole import plan** (all Edges + all chains + combined graphs + legacy conversions) is parsed/remapped/validated **before the first persistent write**. H5 extended. |

### Contract corrections

| # | correction | v4 |
|---|---|---|
| **A** | `judgment_time_known` (new persisted field) was missing from the §2 `SCHEMA_VERSION` **and** `FORMAT_VERSION` rows — and a legacy root exported without it would re-import as a *known* judgment time, the exact H12 falsehood | Added to both §2 rows, with the export-must-carry-it note. |
| **B** | the §4 intro still said the deprecated scalars "derive from heads" (stale Option-B text) | Rewritten: `outcome_counts`/`times_used` derive from heads; `last_outcome`/`last_outcome_at` are deprecated, non-authoritative. |
| **C** | §2c-ii cited drifted coordinates (`:554,573`/`:572`) and claimed `model_config["extra"] == "ignore"`, but the measured value is `None` (Pydantic *default* is `ignore`) | Corrected to `:572,591`/`:590` and `model_config.get("extra") → None` (default `ignore` drops unknown fields); §9 block fixed too. |

**Not changed:** the immutable chain, per-chain `seq`, derived head, CAS append,
linearize-not-reconcile, and Option A (`committed_seq` stays removed). The reviewer's v4
acceptance bar is items 1–9 (incl. keep-Option-A, keep-deprecate-in-place); all are
closed here.
