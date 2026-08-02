# Feature spec: supersession authority

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v2)** — submitted 2026-08-02 04:33 UTC. **All eight findings closed.** The
> authority tables are now **generated from `specs/ladder.py`**, which is the
> fix for finding 1: v1 wrote them out and inverted two of four. The matrix
> covers the **full 400-row `(author, derived_from)` product** including the 80
> rows where capping changes the answer; entitlement is **scoped by subject
> class**; **every retirement path** including absorption goes through one
> authority operation; `correct()` preserves the **complete** trust basis; and
> inactive-edge routing is a **table, not a sentence**.

*Fill this in **before** implementing. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v2** — *re-read before editing; quote the version you approve.* v1 deferred at first external review (8 findings). |
| **Status** | *see `Spec-Status:` at the top — canonical.* Ladder adopted by research; **Q1/Q2 answered 2026-08-01**; I7 shipped (`362f474`); external review not sent. |
| **Internal reviewers** | research — **ladder already ADOPTED** (`proposals/supersession-authority-review.md`); two sub-decisions open, see §10 |
| **External review** | required — full spec (`graph.py`, `gate.py`, `mcp_server.py`) · not yet sent |
| **Decision + date** | — |
| **Path** | full |

> **No advisory.** The technical rationale is the one that carries it:
> **exploitation requires third-party content to be ingested and then a
> functional-relation collision — it is not automatic**, and the
> automatic-versus-invoked distinction is the same line that governed 0.4.4.
> *Deployment count is release context, not a security rationale* — v1 led with
> "no real external users", which would not survive the first real one.

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
| **host `derived_from`** | none | rejected | **rejected — raises** | omitted where it should cap | I7 ✅ shipped; capping-only unchanged (0.1.7). **Now also load-bearing for supersession** — it is the cap in `effective` (§3), so an omitted `derived_from` overstates authority as well as disclosure. |
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

> **A functional supersession is permitted only when the incoming edge's
> *effective* authority is ≥ the prior edge's**, where
>
> ```python
> effective = min(AUTH[author_of_evidence], AUTH[derived_from or author_of_evidence])
> ```

**The authority is capped, not raw** — research's Q2 answer, and it is the whole
reason `SYSTEM` can keep rung 2 without splitting the enum. `SYSTEM` means two
different things today: host state veracium derived itself, and a summary of
somebody else's content. Capping separates them **using machinery that already
exists** rather than a new class:

| edge | raw | `derived_from` | **effective** | consequence |
|---|---|---|---|---|
| host-state `SYSTEM` | 2 | — | **2** | keeps rung 2; may retire a third-party claim |
| **`SYSTEM` summary of an attacker's email** | 2 | `THIRD_PARTY` | **0** | **retires nothing** — the door Q2 was about |
| `USER` repeating something they read | 3 | `THIRD_PARTY` | **0** | consistent with it rendering `third-party-derived` under Q5 |
| `ASSISTANT` inference over user testimony | 1 | `USER` | **1** | `min` — capping never raises |

**This makes the ladder the fifth instance of the one shape, not an exception to
it:** `derived_from` may cap never raise · configuration may narrow never widen ·
maintenance may narrow never widen · **supersession authority is capped by
provenance, never raised by it** · supersession by an equal-or-better-entitled
party, never a lesser one.

<!-- GENERATED:matrix -->
`USER 3 > SYSTEM 2 > ASSISTANT 1 > THIRD_PARTY 0`

| prior | incoming | result | |
|---|---|---|---|
| `user` | `user` | allow | same class |
| `user` | `system` | **BLOCK** |  |
| `user` | `assistant` | **BLOCK** |  |
| `user` | `third_party` | **BLOCK** |  |
| `system` | `user` | allow |  |
| `system` | `system` | allow | same class |
| `system` | `assistant` | **BLOCK** |  |
| `system` | `third_party` | **BLOCK** |  |
| `assistant` | `user` | allow |  |
| `assistant` | `system` | allow |  |
| `assistant` | `assistant` | allow | same class |
| `assistant` | `third_party` | **BLOCK** |  |
| `third_party` | `user` | allow |  |
| `third_party` | `system` | allow |  |
| `third_party` | `assistant` | allow |  |
| `third_party` | `third_party` | allow | same class |
<!-- /GENERATED:matrix -->

**Generated from `specs/ladder.py`.** v1 wrote this table by hand and inverted
two of four `ASSISTANT` cases, including `assistant → third_party` — the unsafe
direction, which would have let assistant-generated content retire a
third-party record. **The document it was transcribed from had all four right.**

<!-- GENERATED:coverage -->
**The rule reads `min(author, derived_from)`, so the matrix is over the full product: 400 rows, not 16.** **80 of them give a different answer than authorship alone**, and those are exactly the rows an attacker reaches by omitting `derived_from`.

| prior author/derived | incoming author/derived | result | |
|---|---|---|---|
| `user`/`—` | `user`/`system` | **BLOCK** | differs from the author-only answer |
| `user`/`—` | `user`/`assistant` | **BLOCK** | differs from the author-only answer |
| `user`/`—` | `user`/`third_party` | **BLOCK** | differs from the author-only answer |
| `user`/`user` | `user`/`system` | **BLOCK** | differs from the author-only answer |
| `user`/`user` | `user`/`assistant` | **BLOCK** | differs from the author-only answer |
| `user`/`user` | `user`/`third_party` | **BLOCK** | differs from the author-only answer |

*(first 6 of 80; the test enumerates all 400)*
<!-- /GENERATED:coverage -->

**The nine non-`ASSISTANT` pairs were measured against the running code.**
Assertability ordering and like-for-like+user-override both score 8/9, **failing
on different cases**, which is the diagnostic: disclosure answers *may this be
asserted*, supersession asks *who may declare this stale*. Different axis.

⚠️ **The `ASSISTANT` row was never measured**, and v1's prose implied it had
been. It is now generated, so the claim and the table cannot diverge again.

**Extends to `ASSISTANT` with no new concept**, and **v2 must generate that row
from the constants rather than write it out.** v1 wrote it out and inverted two
of four — `assistant → user` and `assistant → third_party` — while the source it
was copied from had all four right. The rule is one line of arithmetic
(`AUTH[incoming] >= AUTH[prior]`); **restating its consequences in prose is what
introduced the only normative contradiction in this spec.**

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

## 1b. The same defect on a second path — `correct()` (was `0002` M7)

**Moved here from `specs/0002` on 2026-08-01, and moving it found a hole in
this spec.** M7 was filed as a maintenance-provenance finding because that is
where the audit ran. It is not one. **`correct()` is a supersession path**, and
therefore this spec's subject.

**The hole, measured — the two sets are disjoint:**

```
$ grep -rn "apply_supersession" --include=*.py src/veracium/
ingest.py:131          <- the ONLY caller
$ grep -rn "supersedes=" --include=*.py src/veracium/
__init__.py:616        <- the ONLY place a supersession is recorded
```

**`correct()` is the only code that supersedes a fact, and it never calls the
function this spec guards.** So the ladder as specified in §3 — a check inside
`apply_supersession` — **would have shipped with an uncovered bypass**, and
because `correct()` hardcodes `author_of_evidence=USER` (`__init__.py:618`) it
is a **maximum-authority** bypass: it passes any ladder check by construction.

**This is the third instance today of one shape**, and that is now the argument
for treating it as a class rather than three incidents: `_AUTHOR`'s
`.get(author, USER)` default, rung 1 without I5, and now this. **A visible rule
stays green while an invisible dependency carries the risk.** In each case the
rule was correct and the test for it would have passed.

### The finding, as originally recorded

**Found while rebuilding the enumeration.** `correct()` builds its replacement
edge with **hardcoded `author_of_evidence=EvidenceAuthor.USER`**, regardless of
the `actor` argument, and applies it to *any active edge*. Reproduced starting
from a third-party, `use_only`, non-assertable edge:

```
correct(user_id, edge_id, "CEO", actor="system")
  → author=user  disclosure=mentionable  assertable=True
```

**A system actor turned an unverified third-party claim into a user-authored
assertable fact.**

**The asymmetry is the defect, and it is self-evident once both are read
together.** `confirm()` guards exactly this and says why:

> *"Only assertable facts can be confirmed: elevating a quarantined claim or
> third-party inference by 'confirmation' would be a laundering vector — if the
> user affirms a claim, that affirmation is new user-authored evidence and
> belongs in `remember()`."*

`correct()` is the same shape of operation with the same laundering potential
and **no such guard**. `record_outcome` even validates actor↔outcome pairing;
`correct()` accepts `actor="system"` silently.

**⚠️ Correction: `actor` has ZERO effect on trust.** Verified — it appears
exactly twice, in the signature and in the episode summary f-string. A caller
passing `actor="system"` is **silently ignored where it matters**, so my
original framing (a system actor producing user-authored facts) named the wrong
vector. `source_type=STATED` is also hardcoded, so a third-party claim becomes
*stated by the user*. **An argument that looks like it sets authorship and does
not is its own hazard.**

**⚠️ My severity reasoning was also wrong, and research's replacement is
better.** I wrote "host-facing only, so a design gap not an active exploit
path". The realistic path was never an attacker calling `correct()` — it is **a
host implementing the obvious feature (*let the user fix a wrong memory*) and
calling it on whatever edge the user points at**, including a third-party claim
rendered in the UNVERIFIED block. Intent: *fix this text*. Effect: *adopt this
as my own testimony*. **No attacker, no misuse, ordinary operation.** On
reachability alone M7 is **broader than 0.4.4**, which did get an advisory and
required `maintain()` + ≥8 mixed cold episodes + >30 days + trusted-first
ordering.

**What actually justifies no advisory — and this is the reusable line:**
**0.4.4 fired automatically during routine maintenance; M7 requires an explicit
operator-initiated call on a specific edge. Automatic-versus-invoked is the
distinction**, not host-facing-versus-not. Residual risk goes in the release
note rather than being left implied.

**OBSOLETE proposed fix**, retained so the change of direction is legible: v1
proposed *refusing* `correct()` on a non-assertable edge, mirroring `confirm()`.
**Q5 resolved the opposite way** — a correction is an *edit*, so the replacement
inherits the corrected edge's trust basis. See §Q5 and I10.

### What moving it resolves — `0002` Q5

**Q5 is resolved: a correction is an *edit*.** The replacement inherits the
corrected edge's **complete trust basis** — `author_of_evidence`,
**`derived_from`**, `disclosure`, and a source type of `CORRECTED` rather than
`STATED`.

**v1 resolved it as "inherit the class" and that was two fields short.**
`derived_from` is half of `effective()`, so a replacement preserving
`author=USER, disclosure=USE_ONLY` while dropping `derived_from=THIRD_PARTY`
moves from effective authority **0 to 3** — and could then retire edges the
original was never entitled to touch. **Inheriting "the class" was exactly the
kind of partial preservation the capping rule exists to prevent.**

`source_type=STATED` was hardcoded, which turned third-party material into user
testimony on correction. **`CORRECTED` is a new source type**, because neither
`STATED` nor `INFERRED` is true of an edited value.

**Consequence for the implementation:** the ladder check cannot live only in
`apply_supersession`. **It belongs where a supersession is recorded**, and both
paths must reach it — see I9.

---

## 3a. Entitlement is scoped by subject — the ladder alone is overbroad

**First external review, finding 6, and it is not a corner case.** A global
author ladder says a `USER` assertion may retire **any** prior, including
sourced third-party evidence about another person, an organisation, or a
document. **The user is authoritative about their own testimony, not about every
subject in the graph.**

> **Entitlement is `(author, derived_from, subject_class)`, not author alone.**
>
> | subject class | who may retire | rationale |
> |---|---|---|
> | **user-self** — the user's own preferences, attributes, testimony | the ladder, unmodified | the motivating `works_as` case; the user is the source of record |
> | **assistant/system state** — tool results, derived state, run records | `SYSTEM` or `USER` | nobody outside the system observed it |
> | **external-world** — another person, an organisation, a public event, a document | **no cross-author retirement.** Both remain active and **contention is surfaced** | user testimony does not erase sourced evidence about a third party |

**The third row is a deliberate refusal to decide**, and it is the conservative
answer: *surface the tension, never reconcile it* is this project's existing
rule for exactly this situation, and it is what the fallback in Q3 already
proposed. **A wrong retirement destroys evidence; a surfaced contradiction is
additive and inspectable.**

**Subject class is derived from the relation registry**, not guessed per edge —
`MemoryConfig.relations` already carries the relation set, so classification is
a property of a declared relation rather than a heuristic over a subject string.
**Relations without a declared class fall into `external-world`**, which is the
narrowest treatment.

**This narrows the spec's claim, and the narrowing is the honest part.** v1's
"9/9 correct" meant *internally consistent with the chosen ladder*, not
*semantically correct across the graph*.

---

## 3c. Every retirement path, not only functional supersession

**Finding 4.** The ladder was scoped to the functional-supersession loop, leaving
**absorption** guarded by disclosure-class equality (`graph.py:94`) — which §1 of
this same spec argues is inadequate **because `USER` and `SYSTEM` share
`MENTIONABLE`**.

**So a `SYSTEM` edge can absorb a `USER` edge**, setting `active = False` and
removing it from recall. *"Absorption, not supersession"* is a distinction in
our vocabulary and not one in the consequence.

> **Every operation that retires an edge because another edge arrived must
> satisfy the ladder** — functional supersession, absorption, and any future
> path. Where the ladder blocks a merge, **both edges stay active** and the
> contention is surfaced.

**I9 is widened accordingly**: it covered writers of `supersedes=`, which is a
syntactic property. The authority check moves into **one operation**
(§4a) so no future path can retire an edge without passing it.

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

## 4a. One authority operation, and a trusted ingress

**Centralising the check** — the review's amendment, and the reason I9's
set-equality test is not enough. A future path could retire an edge through
`model_copy`, deserialisation, a helper, or a new store method without ever
writing `supersedes=`.

> **`supersede_edge(prior, replacement, context)` is the only way an edge is
> retired because another arrived.** Ingest and `correct()` both call it.
> **`store.invalidate_edge(..., reason="superseded" | "absorbed_duplicate")`
> requires an authorisation result**, so the store refuses a retirement that
> did not come through the check.

**Finding 3 — provenance is host-supplied, and the ladder reads it.** I7 closed
the model-facing route: MCP cannot request `SYSTEM`, and an unknown author
raises. **It establishes nothing about the other entry points.** Nothing today
guarantees that third-party content receives `derived_from=THIRD_PARTY`, and
**omitting it overstates authority** — which this spec says and did not guard.

> **I11 — trusted ingress.** Every edge-construction path must establish its
> evidence source from the **call path**, not from a caller-selected enum.
> Content arriving through a third-party/tool/document ingress receives the
> corresponding derivation cap **by construction**, and a path that cannot
> establish a source gets the **least** favourable one.

**This is `0008`'s principle generalised:** *an act through a dedicated entry
point is evidence; a field asserting what happened is not.* **Without I11 the
ladder is a rule about labels**, and the claim that third-party content can no
longer retire a user's facts holds only as far as the labels are honest.

**The edge-construction paths are enumerated mechanically**, from the
`@store_mutator` call sites already in `specs/generated/0002-audit-manifest.md`,
so a new one cannot be added without appearing in that manifest.

---

## 4b. Inactive-edge routing — which history reaches the model

**Finding 7. I5 said superseded edges must reach the model and never said
which block, which disclosure classes, or which invalidation reasons.**
**Making previously invisible attacker-controlled text visible is an exposure
change**, so §7's *"no new attack surface"* was unsupported as written.

| reason | disclosure | visible? | block | marker |
|---|---|---|---|---|
| `superseded` | mentionable | **yes** | grounded, as history | `SUPERSEDED` |
| `superseded` | use_only | **yes** | **unverified only** | `SUPERSEDED` + third-party origin |
| `superseded` | quarantined | **no** | — | — |
| `absorbed_duplicate` | any | **no** | — | the surviving edge carries the value |
| `corrected` | mentionable | **yes** | grounded, as history | `CORRECTED` |
| `corrected` | use_only / quarantined | **no** | — | — |
| `disputed` | any | **no** | — | a user rejection is not history to re-surface |
| `lapsed` · `decayed` | any | **no** | — | absence of evidence, not superseded evidence |

**Two rules generate the table**, and stating them is what stops the next row
being guessed: **quarantined content never becomes visible by being retired** —
retirement is not a laundering path — and **only reasons meaning *"something
replaced this"* produce history.** `disputed`, `lapsed` and `decayed` do not.

**I5 tests every cell**, not the one benign user-to-user case v1 used.

---

## 4c. Active-first retrieval, with a bounded history budget

**Finding 8: I6 froze a fixture, not a policy**, and Q4 still asked whether
history needed its own cap — which means the general property was unfrozen while
a test asserted an instance of it.

> **Active edges are selected first.** Superseded history is drawn from a
> **separate bounded budget** and **may never displace an active edge of equal
> query relevance.** Trust partitioning holds inside the history budget exactly
> as outside it.

**Q4 is resolved by this** rather than left pre-release. R2 measured the
displacement risk at rank 34 of a 40-edge budget; **a policy that keeps history
in its own budget makes that measurement irrelevant rather than marginal.**

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
| **I1** effective authority ≥ prior, over the **full 400-row product** of `(author, derived_from)` on both sides | `test_supersession_authority_matrix` — **generated from `specs/ladder.py`**, so the test and the table cannot disagree; includes the **80 rows where capping changes the answer** | CI |
| **I2** a functional relation does not exempt the rule | `test_functional_relation_does_not_bypass_authority` | CI |
| **I3** a blocked supersession leaves **both** edges intact and visible | `test_blocked_supersession_keeps_both` | CI |
| **I4** the user correction path (`third_party → user`) still works | `test_user_can_correct_third_party` — the permission, not the prohibition | CI |
| **I5** superseded edges render with the SUPERSEDED marker **through the gate** | `test_superseded_reaches_the_model` | CI — **PRECONDITION, see below** |
| **I6** active-first selection with a **separate** history budget (§4c) | `test_history_never_displaces_an_active_edge` — the **policy**, plus the 200/40 fixture as one instance of it | CI |
| **I7** the MCP surface refuses `system` **and fails closed on unknown** | `test_the_mcp_surface_refuses_system_authorship` · `test_an_unrecognised_author_fails_closed_not_to_user` | CI ✅ **SHIPPED `362f474`** |
| **I8** injection ladder + trust canaries unchanged | existing bench `--compare` | bench gate |
| **I9** **every retirement path** goes through `supersede_edge` — supersession **and absorption** | `test_no_edge_is_retired_outside_the_authority_check` — the store refuses `reason=superseded\|absorbed_duplicate` without an authorisation result, so a **new** path fails at runtime rather than passing a syntactic test | CI |
| **I10** `correct()` preserves the **complete** trust basis — `author_of_evidence` · **`derived_from`** · `disclosure` · source type | `test_correction_preserves_the_whole_trust_basis` — asserts **effective authority is unchanged**, not that two fields match | CI |
| **I10b** a corrected third-party claim is not converted into user testimony | `test_correction_does_not_become_stated` — `source_type` becomes **`CORRECTED`**, never `STATED` | CI |
| **I11** every edge-construction path establishes its source from the **call path**, not a caller-supplied enum | `test_no_ingress_can_assert_authority_it_did_not_earn` — enumerated from the `@store_mutator` call sites in `0002`'s manifest | CI |
| **I12** entitlement is scoped by subject class (§3a) | `test_user_cannot_retire_external_world_evidence` — the permission *and* the prohibition | CI |
| **I13** inactive-edge routing matches §4b exactly | `test_inactive_routing_matrix` — every `(reason × disclosure)` cell, not one benign case | CI |

**I9 is written as a set-equality test on purpose, not as two cases.** Two cases
would pass today and say nothing about tomorrow — and the defect it guards is
exactly *a supersession path nobody remembered to guard*. The check must fail
when someone adds a third writer, which a hand-listed test cannot do.

**I5 is a PRECONDITION of the ladder shipping, not a sibling invariant** —
research's Q1 answer, and the ordering matters. Rung 1 lets `ASSISTANT` retire a
`THIRD_PARTY` claim. If I5 regresses, that stops being *suppression the user can
see* and becomes **a silent suppression primitive — and nothing in the ladder
itself would fail.** The visible rule stays green while an invisible dependency
carries the risk, which is the same shape as the `_AUTHOR` trap I7 just closed:
the map looked like a whitelist and the `.get(…, USER)` default was doing the
damage. **So I5 lands first and is verified before rung 1 is enabled**, rather
than both going in together and the dependency living only in this paragraph.

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
- **Reversibility.** **The implementation is rollbackable; the data consequences
  are not.** Reverting restores the old behaviour, and **historical illegitimate
  retirements cannot be automatically repaired** — we cannot tell, after the
  fact, which retirements the ladder would have blocked. v1 called this "fully
  reversible" while also saying prior retirements were unrepairable.
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

## 12. First external review, 2026-08-02 — disposition

**Ladder direction approved. Eight findings, all verified against the spec and
the code.**

### Finding 1 — I inverted two of four ASSISTANT cases

**WITHDRAWN wording**, quoted so the correction is legible: §3 said
*"`assistant → user` block … `assistant → third_party` allow"*. Under
the spec's own rule — supersession permitted when **incoming effective authority
≥ prior** — with `USER 3 > SYSTEM 2 > ASSISTANT 1 > THIRD_PARTY 0`:

```
assistant -> user          incoming 3 >= prior 1   allow   (spec says block)
user      -> assistant     incoming 1 >= prior 3   BLOCK   (spec agrees)
third_party -> assistant   incoming 1 >= prior 0   allow   (spec agrees)
assistant -> third_party   incoming 0 >= prior 1   BLOCK   (spec says allow)
```

**Two of four are backwards, and `assistant → third_party: allow` is the unsafe
direction** — it lets assistant-generated content retire a third-party record.

**The source I was copying from had it right.** Research's
`proposals/cross-class-supersession.md:95` reads *"`assistant → user` allow ·
`user → assistant` block · `third_party → assistant` allow · `assistant →
third_party` block"* — correct on all four. **I inverted two while transcribing,
and the sentence I wrote around them — *"extends with no new concept"* — is what
made it read as derived rather than asserted.** §3's "measured 9/9" covers the
nine non-`ASSISTANT` pairs; **the `ASSISTANT` row was never measured, and the
prose implied it had been.**

| # | finding | verified |
|---|---|---|
| 1 | ASSISTANT cases contradict the ladder | **yes** — arithmetic above |
| 2 | the matrix tests a simpler rule than the one specified | **yes** — I1 enumerates author pairs; the rule is on `min(author, derived_from)`, so the product includes every `derived_from` **including absent**, and the cases where raw and effective authority differ are exactly the interesting ones |
| 3 | host provenance is not pinned | **yes** — I7 closes the MCP route only. Nothing establishes that third-party content always receives `derived_from=THIRD_PARTY`, and **omitting it overstates authority**, which the spec says and does not guard |
| 4 | absorption also retires edges and is not covered | **yes** — `graph.py:94` filters priors on **disclosure equality**, and this spec's own §1 argues that is inadequate because `USER` and `SYSTEM` share `MENTIONABLE`. **A `SYSTEM` edge can absorb and retire a `USER` edge.** I9 covers writers of `supersedes=`, not every path that invalidates because another edge arrived |
| 5 | `correct()` carries two conflicting fixes | **yes** — `:262` still states the **withdrawn** option (*refuse on a non-assertable edge*) as a live "Proposed fix" while `:267` and Q5 resolve it the other way. And **I10 preserves `author_of_evidence` and `disclosure` but not `derived_from`**, so a corrected edge can move from effective authority **0 → 3** |
| 6 | a global ladder ignores the subject | **yes, and it is not a corner case** — under this rule a user assertion can always retire sourced third-party evidence about another person, an organisation or a document. The user is authoritative about their own testimony, not about every subject in the graph |
| 7 | I5's visibility routing is under-specified | **yes** — it says superseded edges must reach the model and never says **which block, which disclosure classes, or which invalidation reasons**. **Making previously invisible attacker-controlled text visible is an exposure change**, and §7's "no new attack surface" is unsupported as written |
| 8 | I6 is a fixture, not a policy | **yes** — Q4 still asks whether superseded edges need a separate budget, which means the general property is unfrozen |

**Method note, since finding 1 is the second transcription error this week.**
The `_cover` docstring, the `valid_from` changelog, and now this: **a claim
restated in a second document, correct in the first.** The withdrawn-phrase lint
would not catch it — nothing was retracted. What would is deriving the matrix
from the ladder constants rather than writing it out, which is what v2 must do.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~**Q1**~~ | **ANSWERED 2026-08-01 20:56 — yes, rung 1.** *And the conditional was the right one:* **I5 becomes a precondition of shipping, not a sibling** (§6). | resolved | research | — |
| ~~**Q2**~~ | **ANSWERED 2026-08-01 20:56 — `SYSTEM` keeps rung 2, but the ladder uses CAPPED authority** (§3). Do not split the enum; `min(author, derived_from)` already distinguishes host state from a summary of someone else's content. **Sufficient post-I7**, since `system` is no longer reachable through the MCP tool. | resolved | research | — |
| **Q2a** | **Recorded trigger, not an open question:** if the CLI is ever agent-driven, `cli.py:180` becomes the same surface I7 just closed and rung 2 needs re-adjudicating. | `watch` | dev | on any CLI automation |
| **Q3** | Fallback if the ladder proves wrong: never supersede cross-class, keep both, surface contention (Q1(3)'s diagnostic). | `deferred` | research | — |
| ~~**Q5**~~ | **RESOLVED: a correction is an edit.** The replacement inherits the **complete** trust basis — v1 said "class", meaning two fields, and **`derived_from` was not among them**, so a corrected edge could move from effective authority 0 → 3. I10/I10b. | resolved | research | — |
| ~~**Q6** `actor`~~ | **RESOLVED: `actor` is removed from `correct()`.** It reached only an episode f-string, so it looked like it set authority and set nothing. **The third option — "give it an authorisation role" — is refused**: authority comes from the call path (I11), and adding a parameter that grants it would rebuild the defect I7 closed. Correction authorship is the corrected edge's, inherited. | resolved | dev | — |
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
