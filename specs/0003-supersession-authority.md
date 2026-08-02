# Feature spec: supersession authority

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review (v3)** — submitted 2026-08-02 15:55 UTC. **A scope change, not another
> amendment.** Two reviews approved the direction and drew twenty findings, most
> about design this spec did not need in order to fix the defect that motivated
> it. **v3 is one guard in one loop**; subject entitlement, trusted-ingress
> capabilities, `correct()`, absorption, history partitioning and contested
> relations move to **`specs/0011`**. **Blocking is strictly conservative, so
> nothing in `0011` is made harder by shipping this first.**

*Fill this in **before** implementing. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v3** — *re-read before editing; quote the version you approve.* v1 deferred (8) · v2 deferred (12) · **v3 narrows rather than amends.** |
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

**The narrowing is safe because blocking is strictly conservative.** This spec
only **refuses** retirements the code currently permits. It grants nothing,
hides nothing, and adds no field, so every rule in `0011` can later be added as
a further restriction without unwinding this one.

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

> When a retirement is refused, `apply_supersession` records it: a counter for
> telemetry (`supersessions_refused`) and a `diagnostics` line naming the
> relation, the two effective authorities, and the reason. **No memory content
> is recorded** — the field contract is the same content-free shape the existing
> counters use.

**This is how a host discovers that the guard is doing something**, and it is
the only way we will learn whether legitimate updates are being blocked in real
deployments — which §8 lists as this change's main risk.

---

## 4c. What a refusal leaves behind

**Blocking means two active edges on a functional relation.** For five of the
six blocked pairs that is already handled: the incoming edge is `use_only` or
`quarantined`, so the existing gate routes it to the unverified block and the
partitioning separates them.

**Exactly one pair puts both in the grounded block: `user` prior, `system`
incoming** — both `MENTIONABLE`. There, recall renders **both values**, the
user's first.

**That is a real change in what a host sees, and it is the correct direction.**
Today the system inference **replaces** the user's fact and the model sees one
wrong value. After this it sees two, one of which is right, and the
contradiction is visible. *Surface the tension, never reconcile it* is this
project's existing rule for exactly this case.

**Stated as a limit, not solved:** a functional relation with two active values
has no unique current value, and consumers that assume one will see the newest.
**Contested-relation semantics are `0011` E3.**

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
| **I1** a retirement is refused when the incoming effective authority is lower | `test_supersession_authority_matrix` — **generated from `specs/ladder.py`**, the full 400-row `(author, derived_from)` product, so the test and the table cannot disagree | CI |
| **I2** a functional relation does not exempt the rule | `test_functional_relation_does_not_bypass_authority` | CI |
| **I3** a refused retirement leaves **both** edges active | `test_refused_supersession_keeps_both` — the measured email-retires-CFO case becomes the fixture | CI |
| **I4** the permitted directions still work | `test_a_user_can_still_correct_a_third_party_claim` · `test_same_author_update_still_supersedes` — **the permissions, not only the prohibitions.** A guard drawn too broadly passes every prohibition test | CI |
| **I5** a refusal is recorded | `test_a_refused_supersession_is_counted_and_logged` — content-free | CI |
| **I6** the one grounded-contention case renders both values | `test_user_and_system_contention_shows_both` | CI |
| **I7** the MCP surface refuses `system` and fails closed on unknown | `test_the_mcp_surface_refuses_system_authorship` · `test_an_unrecognised_author_fails_closed_not_to_user` | CI ✅ **SHIPPED `362f474`** |
| **I8** injection ladder + trust canaries unchanged | existing bench `--compare` | bench gate |

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

**Claim, and it is deliberately narrow:** *no edge may retire a
higher-authority edge through functional supersession.*

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
| ~~**Q1**~~ | **ANSWERED 2026-08-01 20:56 — yes, rung 1.** *And the conditional was the right one:* **I5 becomes a precondition of shipping, not a sibling** (§6). | resolved | research | — |
| ~~**Q2**~~ | **ANSWERED 2026-08-01 20:56 — `SYSTEM` keeps rung 2, but the ladder uses CAPPED authority** (§3). Do not split the enum; `min(author, derived_from)` already distinguishes host state from a summary of someone else's content. **Sufficient post-I7**, since `system` is no longer reachable through the MCP tool. | resolved | research | — |
| **Q2a** | **Recorded trigger, not an open question:** if the CLI is ever agent-driven, `cli.py:180` becomes the same surface I7 just closed and rung 2 needs re-adjudicating. | `watch` | dev | on any CLI automation |
| ~~**Q3**~~ | **ADOPTED, narrowly.** *Never supersede, keep both, surface contention* is exactly what a refusal now does — for the refused cases only, not as a wholesale replacement of functional semantics. §4c. | resolved | — | — |
| ~~**Q5**~~ | **RESOLVED: a correction is an edit.** The replacement inherits the **complete** trust basis — v1 said "class", meaning two fields, and **`derived_from` was not among them**, so a corrected edge could move from effective authority 0 → 3. I10/I10b. | resolved | research | — |
| ~~**Q6** `actor`~~ | **RESOLVED: `actor` is removed from `correct()`.** It reached only an episode f-string, so it looked like it set authority and set nothing. **The third option — "give it an authorisation role" — is refused**: authority comes from the call path (I11), and adding a parameter that grants it would rebuild the defect I7 closed. Correction authorship is the corrected edge's, inherited. | resolved | dev | — |
| ~~**Q4**~~ | **MOVED to `0011` E6.** History budgeting belongs to the history-visibility design; this change creates fewer superseded edges, not more. | moved | — | — |

---

## 12. Review history

| version | verdict | findings | full disposition |
|---|---|---|---|
| v1 | deferred — direction approved | 8 | `proposals/0003-review-1.md` |
| v2 | deferred — direction approved, blockers architectural | 12 | `proposals/0003-review-2.md` |
| **v3** | **narrowed to the reported defect**; breadth → `specs/0011` | — | this document |

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
- [ ] §5's regime is reachable by a test (**I6**), with a frozen threshold
- [ ] §8 states what this does *not* establish
- [ ] I have said where the **author's conclusion** is wrong
- [ ] §9 brief written and external review sent
