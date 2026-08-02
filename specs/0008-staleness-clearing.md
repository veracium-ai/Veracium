# Feature spec: what may clear `needs_confirmation`

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v2)** — submitted 2026-08-02 18:07 UTC. **The clearing rule was approved at the
> first external review; the spec was not.** The blocking finding is one I had
> not seen: **closing the path that *clears* the flag left open the path that
> stops it being set** — reinforcement advances `observed_at` unconditionally,
> so repeated third-party restatement suppresses the warning entirely.
> **Measured (§3d).** C3a closes it. Also: the matrix now separates *clears* from
> *advances liveness*, C1 gains a structural writer check, the `confirm()`
> guarantee is **conditional on stated host obligations**, the field's meaning is
> narrowed to what the mechanism proves, and the audit record resolves C-Q1
> rather than deferring it.

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v2** — *re-read before editing; quote the version you approve.* v1 deferred at first external review (7 findings); the clearing rule was approved. |
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
| `Edge.needs_confirmation` | set by `expire()`; **cleared by `confirm()` only, after this change** | "an **authorised principal** must explicitly reaffirm this edge through `confirm()`" — v1 said *"the party who stated this should re-affirm it"*, which the mechanism does not establish (§6a) | **restored** — currently cleared by parties that did not state it |
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

**Two effects, not one.** v1 wrote a single **BLOCK** column, which was
ambiguous: a restatement blocked from *clearing* the flag still advanced
liveness, and that decides whether the flag is ever **set** (§3d).

| candidate | clears the flag? | advances liveness? |
|---|---|---|
| **`confirm()`** — host API, not model-reachable | **yes** | yes |
| `remember(author="user")`, same value | **no** | **only if entitled** (C3a) |
| `remember(author="system")`, same value | **no** | **only if entitled** (C3a) |
| third-party restatement | **no** | **no** — not entitled |
| cross-class restatement | no *(0.4.5)* | no |
| `expire()` · consolidation · dedup · wiki | **no** | no — maintenance never refreshes |
| same `source_id` *(future, `0006`)* | **no** | **no** — grouping is not authentication |

> **The governing principle:** *an act through a dedicated entry point is
> evidence; a field asserting who acted is not.* **Add an entry point, not a
> parameter.**

**And a distinction integrators mistake:** a user who agrees with a third-party
claim has produced **new user evidence**, which belongs in `remember()`.
`confirm()` is not a mechanism for adopting untrusted content — it reaffirms
what is already there, at the trust it already has.


## 3d. Clearing is not the only way to defeat the flag

**First external review, finding 1, and it is measured.** This spec closes the
path that *clears* `needs_confirmation`. It left open the path that stops the
flag from ever being **set** — and that path is reachable by the same untrusted
content.

`expire()` ages a fact against `observed_at` (`lifecycle.py:41`), and
reinforcement advances `observed_at` unconditionally (`graph.py:107`). So a
repeated restatement keeps a fact permanently fresh:

```
SLOW relation, lifetime 120 days, edge 200 days old

control, no restatement          -> needs_confirmation = True
4 THIRD_PARTY restatements       -> needs_confirmation = False
                                    observed_at pushed forward each time
```

**The restatements are `THIRD_PARTY`** — the class this spec's own §1 treats as
adversarial. **A party that cannot clear the flag does not need to: it can
prevent the flag appearing.** Closing one and not the other leaves the boundary
open while the document claims it is shut.

> **C3a — reinforcement that is not entitled to reaffirm an edge may not
> postpone that edge's confirmation deadline.** The incoming observation is
> stored as its own evidence; **its currency is not transferred onto the prior
> assertion.**

**This is deliberately narrower than "reinforcement may not refresh liveness".**
Same-source, same-authority restatement is the case the liveness rule exists for
and C3 still protects it. **The entitlement test is the one this spec already
uses** — recorded effective authority, per `specs/0003` — so no new concept is
introduced.

**The lapse argument still holds and is why C3 stays.** A fact stated once and
never again should lapse; a fact genuinely re-observed should not. **What was
wrong was treating *any* repetition as re-observation.**

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
| **C1** no value of any provenance field clears `needs_confirmation` | **two checks, because one cannot establish this.** `test_no_provenance_value_clears_staleness` — behavioural, over **every** provenance input (`author_of_evidence` · `derived_from` · `source_type` · `evidence_ref` · `disclosure` · `confidence`), not `EvidenceAuthor` alone · `test_only_confirm_writes_the_flag_false` — **structural**, an AST inventory of every site assigning `needs_confirmation = False`, whose expected set is `{confirm()}` | CI |
| **C2** `confirm()` clears it | `test_confirm_clears_staleness` | CI |
| **C2a** `actor` is audit metadata and grants nothing | `test_actor_metadata_does_not_grant_confirmation_authority` — authority comes from the protected call path; v1's name (*"clears regardless of actor label"*) read as normalising arbitrary labels | CI |
| **C3** **entitled** reinforcement still refreshes liveness | `test_entitled_reinforcement_still_advances_observed_at` — **the permission, not the prohibition**; without it the fix looks correct and quietly breaks lapse behaviour |
| **C3a** un-entitled reinforcement **may not postpone the confirmation deadline** | `test_third_party_repetition_cannot_suppress_the_flag` — the measured §3d reproduction becomes the fixture: control flags, four third-party restatements must still flag | CI |
| **C4** maintenance never clears | `test_no_maintenance_op_clears_staleness` — property-based over random op sequences, and **asserts its operation registry against the `@store_mutator` surface**, so a newly added maintenance operation cannot stay invisible to it | CI |
| **C5** the flag reaches the model when set | `test_stale_marker_renders` | CI |
| **C6** the 0.4.5 reproducer stays fixed | `test_cross_author_restatement_does_not_clear` — regression, cross-class was the half 0.4.5 got right | CI |

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

> **Every `confirm()` writes a content-free record:**
> ```
> principal · edge_id · confirmed_at · call-path identity · correlation_id
> ```
> **No edge content.** Same shape and erasure policy as `0003`'s refusal record.

**Repeated confirmation is allowed without limit and audited.** Rate limiting is
host policy — veracium cannot tell a legitimate re-affirmation from an
automated one, and **guessing a limit would substitute our judgement for the
host's while still not detecting misuse.** The record is what makes misuse
*visible*, which is the part we can actually provide.

**C-Q1 is resolved by this**, not deferred.

---

## 7. Failure modes and reversibility

**Failure mode is a caveat that outstays its welcome** — a fact stays marked
`[possibly stale]` until someone calls `confirm()`. Additive and visible,
against silent removal of a caveat that should have stayed.

**Reversibility, corrected.** v1 said *"no data is written or destroyed;
existing values stay exactly as they are"* and that was wrong in a way that
matters:

> **No schema or migration change is required. The implementation is
> rollbackable, but behaviour during deployment changes persisted edge state**,
> and reverting does not reconstruct the counterfactual the old rule would have
> produced.

Before, reinforcement wrote `needs_confirmation=False`; after, it leaves `True`
persisted. **After a rollback we cannot tell which flags the old behaviour would
have cleared during the intervening period** — the safer flags simply remain set
until a later `confirm()` or entitled reinforcement changes them. **That is the
right direction to fail, and it is still not "no data changes".**


## 8. Claims and limits

**Claim:** *only an explicit `confirm()` clears `needs_confirmation`, and
reinforcement that is not entitled to reaffirm an edge cannot postpone its
confirmation deadline.*

**The second clause is new in v2 and it is the one that makes the first worth
having.** Closing the clearing path alone left the flag suppressible by anyone
who could repeat a fact — measured in §3d, using the `THIRD_PARTY` class this
spec calls adversarial.

**What this does NOT establish:**

- **Not that a user confirmed anything.** veracium sees a call, not a person.
  **The guarantee is conditional on the host obligations in §6a** — and if the
  host exposes `confirm()` to a model, this spec buys nothing.
- **Not per-author staleness.** `needs_confirmation` is one boolean for the
  whole edge; `0002` Q4 would dissolve this structurally rather than fence it.
- **Not why the flag was set.** `expire()`'s CONFIRM behaviour is untouched.
- **Not source identity.** Entitlement is recorded effective authority, and
  whether the labels are honest is `0011` E4.


## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~**C-Q1**~~ | **RESOLVED in §6b, not deferred.** Every `confirm()` writes a content-free audit record; repeated confirmation is allowed without limit, because veracium cannot distinguish a legitimate re-affirmation from an automated one and **a guessed limit would substitute our judgement for the host's while still not detecting misuse.** The record makes misuse visible, which is the part we can provide. | resolved | dev | — |
| ~~C-Q2~~ | **RULED 2026-08-01 (Quentin): no release-note correction.** The 0.4.5 note is accurate as written — cross-author clearing *was* closed. The residual same-class case is this spec's subject and ships as its own fix. **Not blocking.** | resolved | Quentin | — |
