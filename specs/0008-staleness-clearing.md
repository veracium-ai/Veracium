# Feature spec: what may clear `needs_confirmation`

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — split out of `0002` M3 on 2026-08-01. **The rule is frozen by two
> rulings (R2, R3) and one external review**; what remains is acceptance and
> implementation. **The fix that shipped in 0.4.5 is inadequate and this is the
> spec that replaces it.**

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 |
| **Status** | *see `Spec-Status:` — canonical.* Split from `0002` §M3/§7b. **`0002` is a retrospective and must be closeable; this is a proposal and is not.** |
| **Internal reviewers** | research — **R2** (fail-closed rule) and **R3** (strict; not temporary) |
| **External review** | required — `graph.py` is guarded; **second review of `0002` found the hole this spec closes** |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

**A staleness flag addressed to the user can be cleared by something that is not
the user.**

`needs_confirmation` renders as `[possibly stale — confirm before relying on
it]` (`graph.py:358`). It is **a question addressed to the party who stated the
fact.** `graph.py:119-121` clears it whenever reinforcing evidence carries the
same `EvidenceAuthor` **class**:

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
| `Edge.needs_confirmation` | set by `expire()`; **cleared by `confirm()` only, after this change** | "the party who stated this should re-affirm it" | **restored** — currently cleared by parties that did not state it |
| `Provenance.author_of_evidence` | read by the rule being **removed** | authorship of evidence | **unchanged** — this spec stops *relying* on it for authority, it does not alter it |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant |
|---|---|---|---|---|---|
| **host/model `author`** on `remember` | enum-rejected | enum-rejected | enum-rejected | **`author="user"` on model-authored text** — and `remember` is `@server.tool()`, so **the model reaches this directly** | **C1** — no value of `author` clears the flag |
| **`source_id`** (future, `0006`) | — | — | — | host reuses one id across unrelated sources | **C1** — no field clears the flag, whatever it is |
| **`actor`** on `confirm()` | defaults `user` | — | — | mislabelled | **C2** — `actor` is recorded, never load-bearing; the **call** is the evidence |
| **call frequency** | — | — | — | repeated `confirm()` to hold a fact fresh forever | ⚠️ **no invariant.** A host with API access can do this by design; stated so it is not mistaken for covered |

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

---

## 3. Trust-class matrix — REQUIRED, blocking

**The matrix is one column wide, and that is the finding.**

| clearing candidate | today | after | why |
|---|---|---|---|
| explicit `confirm()` (host API) | clears | **clears** | an authorised act through a dedicated entry point |
| `remember(author="user")`, same class | **clears** | **BLOCKS** | `remember` is model-reachable; the model can set `author` |
| `remember(author="system")`, same class | **clears** | **BLOCKS** | two unrelated `SYSTEM` processes are both `SYSTEM` |
| third-party restatement, same class | **clears** | **BLOCKS** | repetition is not renewed observation |
| cross-class restatement | blocks | blocks | unchanged (0.4.5) |
| `expire()` / consolidation / dedup / wiki | blocks | blocks | maintenance never clears — `0002` N4 |
| same `source_id` (future) | n/a | **BLOCKS** | R3 — grouping is not authentication |

> **The governing principle, and it generalises past this spec:**
> **an act through a dedicated entry point is evidence; a field asserting who
> acted is not. Add an entry point, not a parameter.**

**Why that distinction is real rather than nominal:** `author="user"` rides on
`remember`, which is an `@server.tool()` — **the model calls it**. `confirm()`
is host-API only: not an MCP tool, not a CLI verb. **It is the only candidate
whose evidence the model cannot fabricate.**

---

## 4. Behaviour

Delete the conditional at `graph.py:119-121`. Reinforcement continues to refresh
**liveness** (`observed_at`) and to retain confidence per `0002` M5 T1; it stops
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
| **C1** no value of any provenance field clears `needs_confirmation` | `test_no_author_value_clears_staleness` — table-driven over the **full `EvidenceAuthor` product**, not the two cases we happen to worry about | CI |
| **C2** `confirm()` clears it; `actor` does not change that either way | `test_confirm_clears_regardless_of_actor_label` | CI |
| **C3** reinforcement still refreshes liveness | `test_reinforcement_still_advances_observed_at` — **the permission, not the prohibition**; without this the fix looks correct and quietly breaks lapse behaviour | CI |
| **C4** maintenance never clears | `test_no_maintenance_op_clears_staleness` — property-based over random op sequences (`0002` N4 family) | CI |
| **C5** the flag reaches the model when set | `test_stale_marker_renders` | CI |
| **C6** the 0.4.5 reproducer stays fixed | `test_cross_author_restatement_does_not_clear` — regression, cross-class was the half 0.4.5 got right | CI |

**C3 is the one to write first.** The change is a deletion, and a deletion that
over-reaches would remove liveness refresh along with the flag clearing — which
no test currently distinguishes.

---

## 7. Failure modes and reversibility

**Failure mode is a caveat that outstays its welcome.** Reversible by reverting
one conditional; no data is written or destroyed, and no stored field changes
meaning. **Nothing needs migrating** — existing `needs_confirmation` values stay
exactly as they are.

---

## 8. Claims and limits

**Claim:** only an explicit confirmation clears a staleness flag.

**Limits:**

- **Not authentication.** We do not verify a user is present, only that the
  **host API** was used rather than a model-reachable tool. A host that calls
  `confirm()` in a loop defeats it, by design and by its own authority.
- **Does not make `needs_confirmation` per-author** — carried as `0002` Q4, and
  it would dissolve this problem structurally rather than fence it.
- **Does not address why the flag was set.** `expire()`'s CONFIRM behaviour is
  out of scope.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **C-Q1** | Should `confirm()` be **rate-limited or audited** given §8's first limit? It is the one remaining path and we have no record of how often it is used. | `pre-release` | dev | before release |
| ~~C-Q2~~ | **RULED 2026-08-01 (Quentin): no release-note correction.** The 0.4.5 note is accurate as written — cross-author clearing *was* closed. The residual same-class case is this spec's subject and ships as its own fix. **Not blocking.** | resolved | Quentin | — |
