# Feature spec: supersession authority

Spec-Status: draft

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **draft** — ladder adopted by research; Q1/Q2 blocking; external review not sent

*Fill this in **before** implementing. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 — *re-read before editing; quote the version you approve* |
| **Status** | *see `Spec-Status:` at the top — canonical.* Ladder adopted by research; **Q1/Q2 blocking**; external review not sent. |
| **Internal reviewers** | research — **ladder already ADOPTED** (`proposals/supersession-authority-review.md`); two sub-decisions open, see §10 |
| **External review** | required — full spec (`graph.py`, `gate.py`, `mcp_server.py`) · not yet sent |
| **Decision + date** | — |
| **Path** | full |

> **Quentin ruled no advisory** — no real external users yet, only tyre-kickers.
> This is design work, not a hotfix.

---

## 1. Problem and motivation

**Third-party content can retire a user-asserted fact and erase it from recall.**

`apply_supersession` guards *merges* with the same-disclosure-class filter added
in 0.4.1 (`graph.py:94`). The **functional-supersession loop below it**
(`graph.py:139`) uses `store.edges(...)` with **no filter**. Measured: an email
extracted as `works_as: unemployed` retires the user's own
`works_as: CFO at Acme`, leaving

```
GROUNDED:   (empty)
UNVERIFIED: works_as: unemployed [third-party-reported; unconfirmed]
```

**Three of nine author pairs are unsafe today.** An attacker cannot make their
own claim assertable — they do not need to; deleting the user's is enough.

**A second, independent defect makes it total.** `render_edges` has a
`SUPERSEDED` branch, but `gate.partition_parts` routes `e.assertable` (requires
`active`) to grounded and `quarantined or (active and use_only)` to unverified —
**an inactive edge falls through both.** Measured on the *benign* case of a user
superseding their own fact: not shown. **So supersession-never-erasure holds in
the store and not in what the model reads**, which is the only place it protects
anything.

**If we do nothing:** the write path — the one place we have always claimed is
well defended — contains a silent-deletion primitive reachable by any
third-party ingest.

**Alternatives rejected.**

- **Reuse 0.4.1's same-disclosure-class equality.** The obvious fix, and it
  scores **6/9 — identical to no guard.** `USER` and `SYSTEM` share
  `MENTIONABLE`, so it still permits a host-written `system` edge to retire a
  user fact, **and** it blocks the user correcting a third-party claim.
- **Block all cross-class supersession.** Blocks legitimate user corrections;
  same failure as above.
- **Never supersede; always keep both and surface contention.** Consistent with
  *"surface the tension, never reconcile it"*, but it changes functional-relation
  semantics wholesale and leaves no current value. **Kept as the fallback if the
  ladder proves wrong** — see §10 Q3.

---

## 2. Field contracts touched

| field | read / written | documented contract | consumers | preserved? |
|---|---|---|---|---|
| `Edge.active` | `invalidate_edge`; read everywhere | "false = retired, retained as history" | `assertable`, `gate.partition_parts`, `render_edges`, `store.edges(active_only)` | **NO today** — history is retained but unreachable through the gate. Restored by this change. |
| `Edge.invalidation_reason` | `apply_supersession` | why an edge retired: `superseded` · `absorbed_duplicate` · `lapsed` · `decayed` · `disputed` · `corrected` | `render_edges` (SUPERSEDED marker), `introspect` | Yes — gains a *reader*, since the marker currently never renders through the gate. |
| `Provenance.author_of_evidence` | `ingest`; **`mcp_server:_AUTHOR`** | "who authored the evidence — the core injection-resistance signal" | `_disclosure_for`, gate routing, this spec's ladder | **Extended in meaning**: it now also determines *entitlement to retire*, not only disclosure. Recorded as a real widening of the field's role. |

**Enumerated mechanically** — from the interface, not from recall (the method
that missed three surfaces in `specs/0002`):

```
$ grep -nE "def (add_|invalidate_|delete_|forget_|set_)" src/veracium/store/base.py
$ grep -rn "invalidate_edge\|partition_parts\|render_edges" src/veracium/ | grep -v ingest.py
```

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| **host/model `author`** (`mcp_server`) | rejected | rejected | **rejected — raises** | **model declares itself `SYSTEM`** to climb the ladder | **I7**: `_AUTHOR` has no `system` key **and** the lookup raises rather than defaulting |
| **extractor `object` value** | no supersession | no supersession | — | **any differing value on a functional relation triggers supersession** — this is the attack vector | **I1/I2**: supersession requires authority ≥ prior |
| **extractor `relation`** | — | unknown relation → non-functional → no supersession | — | extractor picks a *functional* relation for third-party content | **I2** — authority is checked regardless of relation |
| **host `derived_from`** | none | rejected | **rejected — raises** | omitted where it should cap | I7; capping-only is unchanged (0.1.7) |
| **older-version store data** | — | pydantic rejects unknown enum | — | — | ⚠️ **no invariant** — carried from `0001` Q3 (`PRAGMA user_version`); a gate on that spec, not this one |

## 2c-ii. Assertions about reach

| assertion | command | result |
|---|---|---|
| the supersession loop is unfiltered | `sed -n '136,142p' src/veracium/graph.py` | `store.edges(...)`, no disclosure test |
| 3 of 9 author pairs unsafe | drive `apply_supersession` over the enum product | user→system, user→3p, system→3p retire |
| inactive edges reach neither block | `gate.partition(edges, [])` with a superseded edge | absent from both |
| `remember` is a model-facing tool | `grep -n "@server.tool" src/veracium/mcp_server.py` | `:88` `remember` |
| `SYSTEM` is host-settable | `grep -n "_AUTHOR" src/veracium/mcp_server.py` | mapped `"system"` → `SYSTEM` (removed by I7) |
| `confidence` does not affect ranking | read `subgraph_for_query`'s scorer | overlap · active · `observed_at` only |

---

## 3. Trust-class matrix — REQUIRED, blocking

**Directional, because supersession is.** Authority ladder, adopted by research:

```
USER 3  >  SYSTEM 2  >  ASSISTANT 1  >  THIRD_PARTY 0
```

> **A functional supersession is permitted only when the incoming edge's author
> authority is ≥ the prior edge's.**

| prior → incoming | today | after | rationale |
|---|---|---|---|
| user → user | allow | allow | the user revises their own fact |
| **user → system** | **allow** | **BLOCK** | our own inference must not retire user testimony |
| **user → third_party** | **allow** | **BLOCK** | **the attack** |
| system → user | allow | allow | the user corrects our inference |
| system → system | allow | allow | same class |
| **system → third_party** | **allow** | **BLOCK** | untrusted content must not retire our derivation |
| third_party → user | allow | allow | **the `I3b` correction path** |
| third_party → system | allow | allow | our maintenance may retire an unverified claim |
| third_party → third_party | allow | allow | same class |

**Measured 9/9 correct** — the only candidate rule that is. Assertability
ordering and like-for-like+user-override both score 8/9, **failing on different
cases**, which is the diagnostic: disclosure answers *may this be asserted*,
supersession asks *who may declare this stale*. Different axis.

**Extends to `ASSISTANT` with no new concept** — `assistant → user` block,
`user → assistant` block, `third_party → assistant` allow, `assistant →
third_party` allow. **The rule does not need revisiting when `0001` lands.**

**Answering the required questions.**
- *Can a user-asserted fact become non-assertable?* **Today yes — that is the
  defect.** After: only by a party of equal or greater authority.
- *Can non-user content gain user-grade authority?* No. This change only
  **removes** the ability to retire; it grants nothing.
- *Can it clear `needs_confirmation`?* No path added.
- *Does it merge, drop or overwrite provenance?* No. Blocked supersessions leave
  both edges intact, which is the additive-noise side of the asymmetry.

**Write-time or maintain-time?** **Write-time** — `apply_supersession` runs at
ingest. Note this is the *first* trust defect we have found in the write path;
0.4.1 and 0.4.4 were both maintenance.

---

## 3b. Authorization and scope

Single-`user_id` throughout; no tenant boundary crossed. **The visibility change
is a widening within one user's own store**: superseded edges become visible in
recall where today they are invisible. That is the intent, and §7 covers the
one case where it could surprise.

---

## 4. Behaviour

| | before | after |
|---|---|---|
| email claims a different job | user's fact **retired and invisible** | user's fact **stays current**; the claim shows in UNVERIFIED |
| user states a new job | old retired, **invisible** | old retired, **shown as SUPERSEDED** |
| model calls `remember(author="system")` | accepted → `SYSTEM` | **raises** |
| `remember(author="typo")` | **silently became `USER`** | **raises** |

**Exact rendering change** — superseded edges now reach the grounded block via
the existing branch, unchanged in wording:

```
works_as: CFO at Acme (SUPERSEDED 2026-01-15→2026-05-02)
```

**Interfaces:** MCP `remember` no longer accepts `author="system"` — a
**narrowing** of what a caller may claim, adding no capability. **Migration:**
none; no stored data changes.

---

## 5. Regime analysis

- **Scale.** Superseded edges accumulate forever. A long-lived store with a
  volatile functional relation could hold many, and they now compete for the
  subgraph budget. **This is the regime that matters and no fixture reaches it**
  — the same shape as the query-blind-recall defect, which needed ~1,700 facts.
- **Thresholds:** `max_subgraph_edges` (40) — and R2 just measured what budget
  pressure does: an item whose answer sat at rank 34/40 lost it entirely when
  the head shrank. **Adding superseded edges to the candidate pool is budget
  pressure of exactly that kind.**
- **Do the tests reach it?** **Not yet — I6 below is the gate.** Release class
  is **stable**, so an unreachable regime blocks.
- **Cold vs warm:** no difference; both changes are per-write or per-render.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **I1** authority ≥ prior, over all 9 pairs (16 with `ASSISTANT`) | `test_supersession_authority_matrix` — table-driven over the enum product | CI |
| **I2** a functional relation does not exempt the rule | `test_functional_relation_does_not_bypass_authority` | CI |
| **I3** a blocked supersession leaves **both** edges intact and visible | `test_blocked_supersession_keeps_both` | CI |
| **I4** the user correction path (`third_party → user`) still works | `test_user_can_correct_third_party` — the permission, not the prohibition | CI |
| **I5** superseded edges render with the SUPERSEDED marker **through the gate** | `test_superseded_reaches_the_model` | CI |
| **I6** superseded accumulation does not displace current facts | `test_superseded_do_not_crowd_out_current` — frozen: 200 superseded + 40 current, fixed queries, **every current fact retrieved at baseline must still be retrieved** | CI |
| **I7** the MCP surface refuses `system` **and fails closed on unknown** | `test_the_mcp_surface_refuses_system_authorship` · `test_an_unrecognised_author_fails_closed_not_to_user` | CI ✅ *written* |
| **I8** injection ladder + trust canaries unchanged | existing bench `--compare` | bench gate |

**I6 carries a frozen acceptance rule deliberately** — `specs/0002`'s I6 said
only *"user facts still reach the subgraph"*, and R2 proved an unfrozen
threshold is worth nothing.

**Reproducer retention:** the email-retires-CFO case and the benign
user-supersedes-own-fact case both become fixtures.

---

## 7. Failure modes and reversibility

- **Silent failure.** A blocked supersession leaves a stale fact current. The
  symptom is a *wrong but confidently-held* answer, and the contradicting claim
  is visible in UNVERIFIED — additive, inspectable. **The asymmetry is deliberate
  and is the same one that keeps T1 narrow:** a missed supersession is visible
  noise, a false one destroys.
- **The surprise case:** a user whose world genuinely changed, where only a third
  party knows, now keeps a stale current value. **We prefer that**, and §8 says
  so rather than hiding it.
- **Reversibility.** Fully reversible: no stored data changes. Edges retired by
  the old behaviour stay retired — **not repaired**, and unrepairable, since we
  cannot know which retirements were illegitimate.
- **New attack surface?** None added. This removes a capability and makes
  retained history visible.

---

## 8. Claims and limits

- **What we will say:** *"A fact may only be superseded by evidence from a party
  entitled to supersede it. Third-party content can no longer retire a user's
  own facts, and superseded history remains visible in recall."*
- **What this does NOT establish.**
  - **Not that the write path is now safe** — it establishes that *this* defect
    is closed. It is the first write-path trust defect we have found, and we
    found it by measurement, not review.
  - **Not that the ladder is right.** `ASSISTANT`'s position and whether
    `SYSTEM` outranks `THIRD_PARTY` are judgements (§10).
  - **Not that stale facts are prevented** — the change *prefers* staleness to
    silent deletion.
  - Nothing about non-functional relations, which accumulate and never
    supersede.
- **Measurements cited:** the 9-pair matrix and 6/9 vs 8/9 vs 9/9 comparison are
  from `proposals/cross-class-supersession.md`, run against `graph.py` at
  `787007b`.

---

## 9. Brief for the external reviewer

- **Least sure of:** (1) that **authority** is the right axis at all, rather than
  *entitlement per subject* — a third party may legitimately know more about a
  non-user subject than the user does, and the ladder ignores the subject
  entirely. (2) `SYSTEM` at rung 2 when `mcp_server` makes it host-settable — a
  narrower `SYSTEM` might deserve rung 2 while a host-declared one does not.
  (3) Whether making superseded edges visible is a **read-cost regression** we
  have not measured at scale.
- **Where we suspect overstatement:** §1's "three of nine unsafe" counts author
  pairs, not real-world frequency. We have no data on how often functional
  relations collide across classes in a live store.
- **What would change our minds:** a case where a lower-authority party
  *must* be able to retire a higher-authority fact and the contradiction in
  UNVERIFIED is genuinely insufficient.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| **Q1** | `ASSISTANT` at rung 1 — my proposal, not a measurement. It may **suppress** a `THIRD_PARTY` claim, harmless only if I5 holds. | **blocking** | research | before implementation |
| **Q2** | Should `SYSTEM` outrank `THIRD_PARTY` given `SYSTEM` is host-settable? A narrower `SYSTEM` may deserve it; a host-declared one may not. | **blocking** | research | before implementation |
| **Q3** | Fallback if the ladder proves wrong: never supersede cross-class, keep both, surface contention (Q1(3)'s diagnostic). | `deferred` | research | — |
| **Q4** | Should superseded edges be **budget-capped** in the subgraph, given R2's rank-34 result? | `pre-release` | dev | before release |

---

## Reviewer checklist

- [ ] §3 has no unanswered cells, and is **directional**
- [ ] §3's classes were read from the enums, not copied
- [ ] Prohibitions AND permissions both tested (**I1 and I4**)
- [ ] Every default fails **closed** (**I7** — the `get(..., USER)` trap)
- [ ] §2c has no empty invariant cell
- [ ] §2c-ii claims carry commands, not assurances
- [ ] §5's regime is reachable by a test (**I6**), with a frozen threshold
- [ ] §8 states what this does *not* establish
- [ ] I have said where the **author's conclusion** is wrong
- [ ] §9 brief written and external review sent
