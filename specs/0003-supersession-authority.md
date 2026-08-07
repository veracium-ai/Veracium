# Feature spec: supersession authority

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v7)** — re-issued 2026-08-07 for round 6. **v7 corrects v6's
> review-history bookkeeping (the header round count and §12); there is NO design
> change.** v6 (submitted 2026-08-02 17:58 UTC) **closed all seven fifth-review findings:**
> The duplicated sections are gone and a structural check now catches
> them; `ladder.py` derives from the **shipped** enum and imports production
> disclosure, giving 144/44/8 — your independent numbers. **§4e freezes what a
> contention group is and states plainly that it reorders pre-existing
> contentions**; **§4f makes the refusal log one atomic store operation** with
> erasure, retention and import semantics; **§7a lists the real surfaces** and
> withdraws the WITHDRAWN "one guard in one loop" framing. I6/I6a are parameterised over the product
> and cover all three selection stages.

*Fill this in **before** implementing. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v7** — *re-read before editing; quote the version you approve.* Narrow design approved at rounds 3 and 4; round 5 deferred on cleanup only, now closed. **v7 is v6 with review-history bookkeeping corrected — no design change.** |
| **Status** | *see `Spec-Status:` at the top — canonical.* **Narrowed at v3; the narrow design was approved at external rounds 3 and 4.** Review counts, findings and open questions are generated into `specs/STATUS.md` — this row states none of them. |
| **Internal reviewers** | research — ladder adopted; R3 and the M5/Q5 rulings applied |
| **External review** | required — the narrow design was approved at r3 and r4 and affirmed at r5 (deferred on cleanup only). Round counts and findings are generated into `specs/STATUS.md` from `specs/reviews.py` — this row states none of them. |
| **Decision + date** | — |
| **Path** | full |

> **Advisory disposition is not made here.** v2 argued exploitation *"is not
> automatic"*; §8 establishes that is false for this defect — once third-party
> content reaches extraction the retirement fires with no further privileged
> call. **The automatic/invoked distinction belongs to `correct()`, not to
> ingest**, so this spec offers no technical argument either way and the
> decision rests on deployment and exposure.

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

## 1b. `correct()` is a second path, and it is out of scope

**`correct()` is the only code that writes `supersedes=`, and it never calls
`apply_supersession`** — the two sets are disjoint, so a guard in the functional
loop does not cover it.

**Recorded as a known gap, not designed here.** The fix — one authorised
replacement operation covering supersession, absorption and correction — is
**`specs/0011` E5**.

**Why deferring it is defensible:** `correct()` requires an operator to select a
specific edge and invoke it. The functional loop fires **automatically** on
ingested content, and the reported attack is the automatic one.

## 2. Field contracts touched

| field | read / written | documented contract | consumers | preserved? |
|---|---|---|---|---|
| `Edge.active` | `invalidate_edge`; read everywhere | "false = retired, retained as history" | `assertable`, `gate.partition_parts`, `render_edges`, `store.edges(active_only)` | **Unchanged.** History is retained and still unreachable through the gate — **this change does not restore it** (`0011` E6). It creates *fewer* inactive edges, not more reachable ones. |
| `Edge.invalidation_reason` | `apply_supersession` | why an edge retired | `render_edges`, `introspect` | **Unchanged.** This change writes it **less often** and adds no reader — the `SUPERSEDED` marker still never renders through the gate (`0011` E6). |
| `Provenance.author_of_evidence` | `ingest` | "who authored the evidence — the core injection-resistance signal" | `_disclosure_for`, gate routing, **this guard** | **Read in one more place**; its writers are unchanged. `mcp_server`'s `_AUTHOR` narrowing shipped separately in 0.4.5 and is not part of this change. |

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
`USER 3 > THIRD_PARTY 0 > SYSTEM 2`

| prior | incoming | result | |
|---|---|---|---|
| `user` | `user` | allow | same class |
| `user` | `third_party` | **BLOCK** |  |
| `user` | `system` | **BLOCK** |  |
| `third_party` | `user` | allow |  |
| `third_party` | `third_party` | allow | same class |
| `third_party` | `system` | allow |  |
| `system` | `user` | allow |  |
| `system` | `third_party` | **BLOCK** |  |
| `system` | `system` | allow | same class |
<!-- /GENERATED:matrix -->

**Generated from `specs/ladder.py`.** v1 wrote this table by hand and inverted
two of four `ASSISTANT` cases, including `assistant → third_party` — the unsafe
direction, which would have let assistant-generated content retire a
third-party record. **The document it was transcribed from had all four right.**

<!-- GENERATED:coverage -->
**The rule reads `min(author, derived_from)`, so the matrix is over the full product: 144 rows over the shipped enum, not 9.** **26 of them give a different answer than authorship alone.** Those are the decisions that *depend on* the derivation cap: omitting `derived_from` collapses them toward the author-only result — verified, **zero** of the 26 have the cap absent on both sides.

| prior author/derived | incoming author/derived | result | |
|---|---|---|---|
| `user`/`—` | `user`/`third_party` | **BLOCK** | differs from the author-only answer |
| `user`/`—` | `user`/`system` | **BLOCK** | differs from the author-only answer |
| `user`/`user` | `user`/`third_party` | **BLOCK** | differs from the author-only answer |
| `user`/`user` | `user`/`system` | **BLOCK** | differs from the author-only answer |
| `user`/`third_party` | `third_party`/`—` | allow | differs from the author-only answer |
| `user`/`third_party` | `third_party`/`user` | allow | differs from the author-only answer |

*(first 6 of 26; the test enumerates all 144)*
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
  defect.** After: only by a party of equal or greater **recorded effective** authority.
- *Can non-user content gain user-grade authority?* No. This change only
  **removes** the ability to retire; it grants nothing.
- *Can it clear `needs_confirmation`?* No path added.
- *Does it merge, drop or overwrite provenance?* No. Blocked supersessions leave
  both edges intact, which is the additive-noise side of the asymmetry.

**Write-time or maintain-time?** **Write-time** — `apply_supersession` runs at
ingest. Note this is the *first* trust defect we have found in the write path;
0.4.1 and 0.4.4 were both maintenance.

---

## 3a. Scope: the functional-supersession loop, and nothing else

**v2 tried to specify the whole entitlement model and two reviews showed that is
a larger design than the defect.** The classifier it proposed did not work — a
relation cannot tell you whose fact it is. **So this spec narrows to the
reported attack**, and the breadth moves to **`specs/0011`**.

| in scope | out of scope — `specs/0011` |
|---|---|
| the functional-supersession loop, `graph.py:139` | `correct()` · absorption |
| refusing a retirement by a lower-authority edge | subject-scoped entitlement |
| keeping both edges when refused | trusted-ingress capabilities |
| one contention case (§4d) | a distinct history partition |
| | contested functional-relation semantics |

**The narrowing is safe because blocking does not destroy evidence.** This spec
only **refuses** retirements the code currently permits; it grants no authority
and hides nothing.

**It is not consequence-free for `0011`, and v3 overstated that.** A refusal
leaves two active values where a later subject-aware model might have permitted
the retirement — and §8 notes legitimate `SYSTEM` updates to `USER` facts are
plausible. **Those contentions accumulate**, and `0011` will have to either
retain them or reconcile them explicitly; changing the forward rule does not
repair them retroactively.

**§4b's refusal record is what makes that tractable** — it carries the relation
and both effective authorities, so the accumulated set can be re-evaluated
without logging memory content.

**What it therefore does not claim** — stated here and again in §8: it does not
stop a user retiring third-party evidence about someone else, it does not
authenticate provenance labels, and it does not fix `correct()`. **Those were
true before this change and remain true after it.**

---

## 3c. Absorption is out of scope, and why that is acceptable

**v2 brought absorption under the ladder.** It is a real gap — `graph.py:94`
filters on disclosure equality, and `USER`/`SYSTEM` share `MENTIONABLE`, so a
`SYSTEM` edge can absorb a `USER` edge.

**It is deferred to `0011` rather than fixed here, and the distinction is
worth stating.** Absorption fires only when one value **subsumes** the other —
the surviving edge still carries the absorbed content. **Functional supersession
fires on any differing value and the prior content is gone from recall.** The
reported attack is the second; the first is a narrower loss.

**Recorded as a known gap** (`0011` E5), not as covered.


## 4. Behaviour

| | before | after |
|---|---|---|
| email claims a different job | user's fact **retired and invisible** | user's fact **stays active and stays retrievable** (§4d); the claim shows in UNVERIFIED |
| a `SYSTEM` inference contradicts a `USER` fact | user's fact retired | **both active**, user's first — one of 44 same-partition states (§4c) |
| user states a new job | old retired, invisible | **unchanged** — still retired, still invisible (`0011` E6) |

**Three things change, across three layers.** v5's WITHDRAWN framing called
this *"one guard in one loop"*, and the fifth review was right that the phrase
hid two load-bearing dependencies — **which is the original defect's own shape: a correct local guard
whose read and persistence dependencies were treated as invisible.**

| # | change | layer | where |
|---|---|---|---|
| 1 | refuse a retirement by lower recorded effective authority | **write** | `graph.apply_supersession` |
| 2 | permute contention groups by authority | **read** | `graph.subgraph_for_query` (+ `relations`), `Memory.recall` |
| 3 | durable, atomic refusal records | **storage** | `Store.add_edge_with_refusals`, SQLite, `forget_user` |

## 7a. Surfaces touched — the honest list

- `src/veracium/graph.py` — `apply_supersession`, `subgraph_for_query`
- `src/veracium/__init__.py` — `Memory.recall` passes the relation registry
- `src/veracium/store/base.py` — one new `@store_mutator` method
- `src/veracium/store/sqlite.py` — a refusal table, its erasure, its atomicity

**Interfaces:** `subgraph_for_query` gains a keyword parameter. It is
re-exported from `veracium`, so this is a **public signature change**, albeit
additive with a default.

**Schema:** **yes** — a new refusal table. No existing table or field changes,
and no stored edge or episode is migrated.

**Migration:** the table is created on open like the rest of `_SCHEMA`. **An
older build opening a newer store ignores it and loses the inventory silently**
— the `0007` problem again, and the fourth spec to meet it.

**Not changed:** `correct()`, absorption, ingest labelling, disclosure routing,
history visibility, and the MCP author narrowing — which shipped in 0.4.5 and is
listed here only because v2 wrongly claimed it as an effect of this change.

---

## 4a. The change, in full

**One guard, in one loop.** `apply_supersession`'s functional branch currently
retires every prior with a differing value, unconditionally:

```python
for prior in store.edges(user_id, subject=..., relation=...):
    if prior.id != edge.id and _value_key(prior.object) != same:
        store.invalidate_edge(prior.id, edge.valid_from, "superseded")
```

> **It retires a prior only when the incoming edge's effective authority is
> greater than or equal to the prior's.** Otherwise **the prior stays active**,
> the incoming edge is stored, and both are visible.

`effective` is `min(AUTH[author_of_evidence], AUTH[derived_from or author])`,
from `specs/ladder.py` — **the same module the tables are generated from**, so
the rule the code runs and the rule the document states are one object.

**Nothing else changes.** No new field, no schema change, no store signature,
no enum value, no API narrowing. `correct()`, absorption, ingest labelling and
recall are untouched.

---

## 4b. Refusal is not silent

**A refusal must be observable or it is indistinguishable from a bug.**

> When a retirement is refused, `apply_supersession` records a **durable,
> content-free** entry:
>
> ```
> refusal_id · user_id · prior_edge_id · incoming_edge_id · relation
> prior_effective · incoming_effective · rule_version · timestamp
> ```
>
> plus a `supersessions_refused` counter. **Opaque edge ids are not memory
> content** — no subject, object or note is recorded.

**v4 recorded only the relation and two authority levels, and §3a claimed that
made later reconciliation tractable. It did not** — many refusals share a
relation and an authority pair, so the record could not identify *which* edges
contended. **`0011` cannot re-evaluate an inventory it cannot enumerate.**

**The counter is per-store and durable**, not process-local: a process-local
count is telemetry, and this needs to be an inventory.

**This is how a host discovers that the guard is doing something**, and it is
the only way we will learn whether legitimate updates are being blocked in real
deployments — which §8 lists as this change's main risk.

---

## 4c. What a refusal leaves behind

**Blocking means two active edges on a functional relation.** For most refused
states the existing gate already separates them — the incoming edge is
`use_only` or `quarantined` and routes to the unverified block.

<!-- GENERATED:contention -->
**44 of the 144 states are refused. 8 of those put both edges in the SAME read partition** — the cases a reader sees as two competing values. The rest are already separated by the existing gate.

| author shape | states | partition |
|---|---|---|
| `user` → `system` | 6 | both `mentionable` |
| `user` → `user` | 2 | both `mentionable` |

**Derived from the SHIPPED enum** (`user, third_party, system`) and the **production** `_disclosure_for`. v5 hard-coded four classes including `assistant`, which does not exist in `EvidenceAuthor`, and reimplemented disclosure — so its 256 extra states modelled a rule the runtime cannot execute. **When `0001` lands and the enum gains `ASSISTANT`, these tables regenerate with no edit here.**
<!-- /GENERATED:contention -->

**In those same-partition cases recall renders both values**, the
higher-authority one first (§4d).

**That is a real change in what a host sees, and it is the correct direction.**
Today the lower-authority edge **replaces** the prior and the model sees one
wrong value. After this it sees two, one of which is right, and the
contradiction is visible. *Surface the tension, never reconcile it.*

**Stated as a limit, not solved:** a functional relation with two active values
has no unique current value, and a consumer that assumes one will take the
first. **Contested-relation semantics are `0011` E3.**

## 4d. Keeping the edge is not keeping the fact

**The motivating defect is recall-level erasure, not store-level retirement.**
Refusing the retirement leaves the prior `active`; it does **not**, on its own,
guarantee the prior still reaches the model. **Measured, on the motivating
case:**

```
prior    USER        "CFO at Acme"      effective 3
incoming THIRD_PARTY "unemployed"       effective 0   -> refused

max_edges=2   ['incoming', 'prior']    prior kept
max_edges=1   ['incoming']             prior GONE
```

`subgraph_for_query` scores relevance, adds `+1` for `active`, and **breaks ties
on `observed_at` — recency.** Authority is not an input. So the refused edge,
being newer, outranks the fact it failed to retire, and at any budget where the
pair straddles the cutoff the user's fact is evicted anyway. **The guard alone
would have closed the store-level symptom and left the reported behaviour
intact.**

> **The rule, corrected:** within one **active functional-contention group** —
> the active edges sharing a `(subject, relation)` key — **recorded effective
> authority dominates, ahead of relevance and recency.** Ordering *between*
> unrelated edges is unchanged.

**v4 said "among edges of equal relevance, authority before recency", and that
does not deliver I6a.** The tie-break only fires on a tie, and the refused edge
can simply be more relevant. **Measured:**

```
prior    USER        "CFO"                       relevance lower
incoming THIRD_PARTY "unemployed job work role"  relevance higher, refused

max_edges=1  ['incoming']   -> the authority tie-break is never reached
```

**Scoping it to the contention group is what keeps the change small.** Authority
does **not** become a global ranking term — two unrelated edges of equal
relevance are ordered exactly as before. It applies only where the guard has
already established that one edge failed to retire another.

**This is a recall change, and v3 claimed there was none.** That claim was wrong
and is withdrawn — the guard needs this clause to deliver what it promises. It
is still small: one sort key, no schema, no new field, and it is **conservative
in the same direction as the guard** (it can only prefer higher-authority
evidence).

**It is not the `0011` retrieval model.** No separate history budget, no
partition, no contested state — those stay deferred. This orders two edges that
are already both active and already both candidates.

---

## 4e. What a contention group is, and how it is reordered

**Fifth review, finding 4: v5 said *"active edges sharing a `(subject,
relation)` key"* and that does not establish the group arose from a refusal.**
A store can already hold several active edges under one key — cross-disclosure
duplicates, legacy rows, imports, host behaviour.

> **Frozen: a contention group is all active edges sharing a key whose relation
> is `functional`.** Not "edges linked by a refusal record".

**And the consequence is stated rather than avoided: this reorders pre-existing
contentions the guard did not create.** That is a retroactive read change. It is
accepted because the reordering is **conservative in the same direction as the
guard** — higher recorded authority first — and because the alternative,
consulting the refusal inventory during retrieval, puts a durable log on the
read path to answer a question the relation registry already answers.

**Non-functional relations are untouched.** They accumulate by design; ordering
them by authority would be a general retrieval change, and this is not one.

### The reordering algorithm, stated mechanically

A global sort key cannot both make authority dominate *within* a group and leave
unrelated ordering untouched. **So it is a permutation, not a sort:**

1. compute the existing relevance order, unchanged;
2. locate the positions occupied by each contention group's members;
3. **permute those members across exactly those positions** — authority, then
   relevance, then recency;
4. every unrelated edge keeps its original position.

**Step 4 is the property that makes this narrow**, and `test_unrelated_edges_keep_their_positions` pins it.

### The plumbing this needs

`subgraph_for_query` **receives no relation registry today**, so it cannot tell
whether a relation is functional. It gains a `relations` parameter, supplied by
`Memory.recall` from `self.config.relations` — the same registry `ingest`
already uses. **An internal signature change on a function re-exported from
`veracium`**, which §7a now names.

---

## 4f. The refusal record is a store operation

**Fifth review, finding 5: v5 said "Schema: none" and then introduced a durable
per-store record.** That was false, and the record as described could not do the
job §3a claims for it.

> **New `Store` method, `@store_mutator`:**
> ```
> add_edge_with_refusals(edge, refusals) -> None     # ONE commit
> ```
> The incoming edge and every refusal it produced are written **atomically**.

**Why atomicity is not optional here.** The store commits per call today, so
two calls give two failure modes: **a refusal recorded for an edge that was
never written** (a ghost), or **an edge written with its refusal lost** (an
unobservable refusal). **An inventory with either is not an inventory**, and
`0011`'s reconciliation is exactly the thing that would trust it.

**Frozen semantics:**

| question | answer |
|---|---|
| failure | **rejects the whole ingest** — the edge is not written either |
| idempotency | keyed on `(prior_edge_id, incoming_edge_id, rule_version)`; a repeat is a no-op |
| `forget_user()` | **deletes the user's refusals** — they are user-linked metadata, so erasure covers them |
| export / import | **excluded.** A refusal is a fact about *this store's* history, not about the memory; importing one would assert a contention that never happened here |
| retention | kept while **either** edge exists; dropped when both are gone |
| the counter | **derived** from the records, never stored — a second copy of a count is the drift this project has spent a week removing |

**`user_id` and edge ids are content-free but user-linked**, so they follow the
erasure policy rather than the telemetry policy. **No subject, object or note is
ever recorded.**

---

## 5. Regime analysis

**The regime is ordinary ingest**, which every test reaches — no simulated
clock, no accumulation. A functional-relation collision between two authors is
one `remember()` call apart.

**The regime that is NOT reached, and is the reason §8 lists a risk:** a real
deployment where legitimate updates cross authority. We have no measurement of
how often a host's own `SYSTEM` writes legitimately update a `USER` fact, so
**§4b's refusal counter exists to produce that measurement** rather than to
assume it is zero.

**v2's regime section discussed superseded-history accumulation competing for
the recall budget.** That belonged to the history-visibility design, which is
now `0011` E6. **This change creates no superseded edges that were not created
before** — it only creates fewer.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **I1** a retirement is refused when the incoming effective authority is lower | `test_supersession_authority_matrix` — **generated from `specs/ladder.py`**, which derives its classes from the **shipped** `EvidenceAuthor` — the full `(author, derived_from)` product over that enum, so the test, the table and the runtime cannot disagree | CI |
| **I2** a functional relation does not exempt the rule | `test_functional_relation_does_not_bypass_authority` | CI |
| **I3** a refused retirement leaves **both** edges active | `test_refused_supersession_keeps_both` — the measured email-retires-CFO case becomes the fixture | CI |
| **I4** the permitted directions still work | `test_user_authored_ingest_can_supersede_third_party` · `test_same_author_update_still_supersedes` — **the permissions, not only the prohibitions.** A guard drawn too broadly passes every prohibition test | CI |
| **I5** a refusal is recorded | `test_a_refused_supersession_is_counted_and_logged` — content-free | CI |
| **I6** **every** same-partition contention state renders both values, higher authority first | `test_contention_matrix` — **parameterised from `specs/ladder.py`** over the shipped enum's product, so a new enum member extends the test rather than leaving a fixture green | CI |
| **I6a** **a refusal must not reduce the prior's recall visibility**, holding query, configuration, budgets and pre-existing store fixed and adding **only** the refused edge and its record | `test_refusal_does_not_evict_the_prior` — parameterised over the same product, and over **all three selection stages**: plain top-k, `_cover`'s temporal reserve, and `Memory._fit_to_budget`'s token truncation | CI |
| **I6b** unrelated edges keep their positions | `test_unrelated_edges_keep_their_positions` — the property that makes §4e a permutation rather than a global re-sort | CI |
| **I7** the MCP surface refuses `system` and fails closed on unknown | `test_the_mcp_surface_refuses_system_authorship` · `test_an_unrecognised_author_fails_closed_not_to_user` | CI ✅ **SHIPPED `362f474`** |
| **I8** injection ladder + trust canaries unchanged | existing bench `--compare` | bench gate |

**I4 is the one to write first.** The change is a refusal, and a refusal drawn
too broadly passes every prohibition test while breaking legitimate updates.
`test_same_author_update_still_supersedes` is what catches that.

**I6a is the one that decides whether this change is worth making.** Everything
else can hold while a query at the budget still evicts the fact the guard
preserved — see §4d.

**Release ordering** — the order these must land in, because a later one
depends on an earlier one holding:

1. **I4** — the permissions. A refusal drawn too broadly passes every
   prohibition test; this is what catches it.
2. **I1–I3** — the guard itself and that a refusal keeps both edges.
3. **I6 / I6a** — contention rendering and, decisively, that a refusal does not
   evict the prior. **Without I6a the rest is a store-level fix for a
   recall-level defect.**
4. **I5** — refusal telemetry, which is what makes `0011`'s reconciliation
   possible later.
5. **I8** — the bench regression gate.

**I1 is generated from `specs/ladder.py`**, so the test and the table in §3
cannot disagree. v1 wrote that table by hand and inverted two of four
`ASSISTANT` cases.

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
- **New attack surface?** None added — this removes a capability. **It does not
  make retained history visible**; superseded edges still do not reach the model
  (`0011` E6). §4d's ranking clause orders two *active* edges — it adds no
  authorisation surface, but it **does change which active facts enter the
  prompt**, which is a top-k exposure change and is stated as one.

---

## 8. Claims and limits

**Claim, and it is deliberately narrow:** *no edge whose **recorded** effective
authority is lower may retire a higher-recorded-authority edge through the
functional-supersession loop, and refusing does not reduce the prior's recall
visibility.*

**"Narrow" describes the claim, not the surface.** The change spans write, read
and storage (§7a) — v5's WITHDRAWN framing called it *"one guard in one loop"*, and that hid
two dependencies the guard cannot work without.

**"Recorded" is load-bearing.** The guard compares the labels in the store. A
mislabelled `SYSTEM` edge, or one whose `derived_from` cap was omitted, still
receives the authority its labels claim. **Establishing that labels are honest is
`0011` E4**, and until it lands this is a guard over recorded provenance, not
over evidence origin.

**What this does NOT establish** — each was true before this change and remains
true after it, and each is owned by a named spec:

- **Not that provenance labels are honest.** `derived_from=None` is read as
  *"direct from this author"*, and nothing establishes that. A `SYSTEM` edge with
  an omitted cap gets rung 2. **`0011` E4.**
- **Not subject-scoped entitlement.** A user assertion can still retire sourced
  third-party evidence about another person. **`0011` E1/E2.**
- **Not `correct()`, and not absorption.** Both still retire edges outside this
  guard. **`0011` E5.**
- **Not history visibility.** Superseded edges still do not reach the model.
  **`0011` E6.** *(This change creates fewer of them, not more.)*
- **Not a contested-relation model.** §4c leaves two active values on a
  functional relation with a stated rendering and no unique current value.
  **`0011` E3.**

**The risk this change carries**, stated because it is the one that would show
up in a deployment rather than a test: **a legitimate cross-authority update is
now refused.** A host whose own `SYSTEM` process legitimately updates a `USER`
fact will see the update kept and the old value retained. **§4b's counter exists
to measure that**, and the fallback if it proves common is `0011`'s entitlement
model, not a weakening of this rule.

**⚠️ Advisory rationale, corrected.** v2 said exploitation *"is not automatic"*.
**That is false for this defect** — once third-party content reaches extraction,
`apply_supersession` retires the prior with no further privileged call. The
automatic/invoked distinction applies to `correct()` and not to ingest, and the
two must be dispositioned separately. **The no-advisory decision therefore rests
on deployment and exposure, which is Quentin's call and not a technical
argument this spec can make.**

---

## 9. Brief for the external reviewer

**v1 and v2's uncertainties have all been answered — two of them by you — so
they are recorded as resolved rather than asked again.**

| earlier uncertainty | outcome |
|---|---|
| *Is authority the right axis?* | **For user-self facts, yes; globally, no.** That is why entitlement moved to `0011` and this spec narrowed. |
| *Is `SYSTEM` at rung 2 defensible?* | **Only where a trusted call path establishes system origin.** I7 removed the model-facing route; the rest is `0011` E4. |
| *Is visible superseded history a read-cost regression?* | **Moot here** — this change creates fewer superseded edges, not more. The history design is `0011` E6. |

**What we are least sure of now, and it is one thing.**

**Whether refusing a legitimate cross-authority update will hurt real hosts.** We
have no measurement. A host whose own `SYSTEM` process updates a `USER` fact —
a plausible integration — now keeps both values. §4b instruments it; §8 names it
as the risk. **We would rather ship the refusal and measure than assume.**

**Where we suspect we have overstated.** §4c says two grounded values with the
contradiction visible is better than one wrong value. **That is our house rule
(*surface the tension*), and it is an assertion about model behaviour we have not
measured.** A model given two contradictory grounded facts may do worse than one
wrong one.

**What would change our minds.** A functional-relation update pattern where the
lower-authority party is routinely the correct one.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~I5 (as a history prerequisite)~~ | **Superseded.** In the narrowed design **I5 is refusal telemetry**; history visibility is `0011` E6. | moved | — | — |
| ~~**Q2**~~ | **ANSWERED 2026-08-01 20:56 — `SYSTEM` keeps rung 2, but the ladder uses CAPPED authority** (§3). Do not split the enum; `min(author, derived_from)` already distinguishes host state from a summary of someone else's content. **Sufficient post-I7**, since `system` is no longer reachable through the MCP tool. | resolved | research | — |
| **Q2a** | **Recorded trigger, not an open question:** if the CLI is ever agent-driven, `cli.py:180` becomes the same surface I7 just closed and rung 2 needs re-adjudicating. | `watch` | dev | on any CLI automation |
| ~~**Q3**~~ | **ADOPTED, narrowly.** *Never supersede, keep both, surface contention* is exactly what a refusal now does — for the refused cases only, not as a wholesale replacement of functional semantics. §4c. | resolved | — | — |
| ~~**Q5**~~ | **RESOLVED: a correction is an edit.** The replacement inherits the **complete** trust basis — v1 said "class", meaning two fields, and **`derived_from` was not among them**, so a corrected edge could move from effective authority 0 → 3. **Invariants: `0011` E5.** | resolved | research | — |
| ~~**Q6** `actor`~~ | **RESOLVED: `actor` is removed from `correct()`.** It reached only an episode f-string, so it looked like it set authority and set nothing. **The third option — "give it an authorisation role" — is refused**: authority must come from the call path (**`0011` E4**), and a parameter that granted it would rebuild the defect I7 closed in 0.4.5. Correction authorship is the corrected edge's, inherited. | resolved | dev | — |
| ~~**Q4**~~ | **MOVED to `0011` E6.** History budgeting belongs to the history-visibility design; this change creates fewer superseded edges, not more. | moved | — | — |

---

## 12. Review history

| version | verdict | findings | full disposition |
|---|---|---|---|
| v1 | deferred — direction approved | 8 | `proposals/0003-review-1.md` |
| v2 | deferred — direction approved, blockers architectural | 12 | `proposals/0003-review-2.md` |
| v3 | narrowed to the reported defect; breadth → `specs/0011` | — | `proposals/0003-review-3.md` |
| v4 | narrow design approved; deferred for retrieval fix + deletion pass | 5 | `proposals/0003-review-4.md` |
| v5 | narrow design affirmed; deferred — duplicated sections, `ladder.py` not runtime-grounded | 7 | dispositioned in this document |
| **v6** | all seven fifth-round findings closed — sections de-duplicated + a structural check, `ladder.py` runtime-grounded (144/44/8) | — | this document |
| **v7** | review-history bookkeeping corrected (this table + the header round count); **no design change** — the round-6 submission | — | this document |

**Why v3 is narrower rather than more complete.** v2 answered all eight of v1's
findings and drew twelve more, because each answer specified more design. Two
rounds in, **the defect was still unfixed at `graph.py:139`** while the spec had
grown a subject classifier, an ingress capability system and a history
partition. **v3 keeps the guard and moves the model.**

**Full dispositions live in `proposals/`, not here.** v2 recreated `0002`'s
append-only review appendix in one cycle — seven rounds of `0002` taught me that
and I repeated it the same day.

---

## Reviewer checklist

- [ ] §3 has no unanswered cells, and is **directional**
- [ ] §3's classes were read from the enums, not copied
- [ ] Prohibitions AND permissions both tested (**I1 and I4**)
- [ ] Every default fails **closed** (**I7** — the `get(..., USER)` trap)
- [ ] §2c has no empty invariant cell
- [ ] §2c-ii claims carry commands, not assurances
- [ ] §5's regime is reachable by a test — **I6/I6a** for contention, **I1** for the guard
- [ ] §8 states what this does *not* establish
- [ ] I have said where the **author's conclusion** is wrong
- [ ] §9 brief written and external review sent
