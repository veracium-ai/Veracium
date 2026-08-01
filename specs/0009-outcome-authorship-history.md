# Feature spec: outcome authorship is append-only history

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — split out of `0002` M4 on 2026-08-01. **The fix that shipped in
> 0.4.5 does not hold**, demonstrated below. The second external review of
> `0002` accepted the append-only direction and required the ordering semantics
> this spec adds.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | *see `Spec-Status:` — canonical.* Split from `0002` §M4/§7a. |
| **Internal reviewers** | research — pending |
| **External review** | required — `__init__.py` is guarded; **`0002`'s second review required head/concurrency semantics before acceptance** |
| **Decision + date** | — |
| **Path** | full |
| **Prerequisite** | **`specs/0007`** — see §9 |

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
| **`Episode.supersedes_episode`** | **NEW**, optional | the episode this judgment revises; forms the chain |
| **`Episode.seq`** | **NEW**, store-assigned monotonic integer | **authority ordering.** Never host-supplied — see §4 |
| `Episode.outcome` | unchanged | the judgment |
| `Edge.outcome_counts` / `last_outcome` | unchanged in meaning | derived from the **head** of each chain |
| `FORMAT_VERSION` | **2 → 3** | export/import must round-trip the chain |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **host `date`** on `record_outcome` | defaults today | `_event_dt` → now | — | **back- or future-dated to win ordering** | **H2 — `seq`, not `date`, decides the head.** A host timestamp must never decide authority |
| **host `actor`** | defaults `system` | — | validated against outcome | mislabelled judgment | recorded per-episode and **never overwritten** — H1 |
| **`evidence_ref`** | required | — | — | reused across unrelated uses to force a merge into one chain | ⚠️ **no invariant** — `(edge_id, evidence_ref)` is the identity by design; a host colliding them merges its own records |
| **imported chain** | — | rejected | — | **two episodes claiming the same head**, or a cycle | **H4/H5** — import repairs to a single head or refuses |

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
> chain is the episode with the **highest store-assigned `seq`**; `outcome_counts`
> and `last_outcome` derive from heads.

**`seq` is per-chain — scoped to one `(edge_id, evidence_ref)`** — and **assigned by the store, never by the host.** The second external
review's requirement, and it is the same rule as `0008`'s: *a host-controlled
timestamp must not decide authority.* Two hosts with skewed clocks would
otherwise reorder each other's judgments.

**Head transition is atomic.** A new episode is linked by compare-and-set on the
current head: if the head moved since it was read, the write is retried against
the new head. **Branching is prohibited** — one head per `(edge_id,
evidence_ref)`.

**Counters follow the head, not the chain length.** `times_used` still counts
distinct `(edge_id, evidence_ref)` pairs; a chain of five judgments about one
use is still one use. **This is the part most likely to regress**, since today's
upgrade path mutates counters in place.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **H1** no episode's `author_of_evidence` is ever overwritten | `test_outcome_authorship_is_never_overwritten` — the measured `system → user → system` case becomes the fixture | CI |
| **H2** `seq` decides the head; a host `date` cannot reorder | `test_a_backdated_judgment_does_not_become_the_head` | CI |
| **H3** exactly one head per `(edge_id, evidence_ref)` | `test_no_branching_under_concurrent_upgrade` — N threads judging one use | CI |
| **H4** import preserves the chain and produces one head | `test_import_preserves_the_outcome_chain` | CI |
| **H5** malformed imported history refuses rather than guessing | `test_a_cyclic_or_headless_chain_is_rejected` | CI |
| **H6** counters are unchanged in meaning | `test_times_used_counts_uses_not_judgments` — **regression**, the most likely casualty | CI |
| **H7** history is **structurally queryable**, not prose | `test_prior_authorship_is_queryable_without_parsing_a_summary` — asserts against fields; **a passing prose note must fail this** | CI |

**H7 is written to fail the shipped fix.** `0002`'s N5 said *"retains the prior
value"*, which the note technically satisfies — the second review flagged that
wording as broad enough to permit another note. **H7 closes it by asserting on
structure.**

---

## 7. Failure modes and reversibility

**Not reversible in the data**: once chains exist, reverting the code leaves
episodes an older build reads as unrelated records — it ignores
`supersedes_episode` and `seq` (`extra="ignore"`) and treats every link as a
separate outcome, **inflating `outcome_counts`**. See §9.

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

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~H-Q1~~ | **RULED 2026-08-01: per-chain.** *Global invites reuse as a general clock, which is how a field acquires an unintended contract* — and per-chain is **structurally un-repurposable**, since values from different chains are not comparable. A store-wide audit order, if ever needed, is a **separately named append log**, not a widened `seq`. **Live precedent:** `confidence` is a lifetime parameter that reads like a belief strength, and putting it in the scorer would retroactively change every merge rule. **A global `seq` is the same trap one field over.** | resolved | research | — |
| **H-Q2** | Should the **head be materialised** on the edge (a pointer) or derived by query? Materialised is faster and adds a second place for truth to live. **Dev leans derived.** | `pre-release` | dev | before implementation |
| ~~H-Q3~~ | **RULED 2026-08-01 (Quentin): no release-note correction**, answered once for both specs. The gap is recorded here and in `0002` §11; the fix ships as this spec. **Not blocking.** | resolved | Quentin | — |
