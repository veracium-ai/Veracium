# Feature spec: supersession authority

Spec-Status: deferred

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **deferred (v1)** — first external review 2026-08-02 04:26 UTC. **Ladder direction approved;
> implementation deferred for major amendment.** Eight findings, all verified.
> **Finding 1 is a normative contradiction I introduced by mis-transcribing a
> source that had it right** — see §12.

*Fill this in **before** implementing. See `PROCESS.md`.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | v1 — *re-read before editing; quote the version you approve* |
| **Status** | *see `Spec-Status:` at the top — canonical.* Ladder adopted by research; **Q1/Q2 answered 2026-08-01**; I7 shipped (`362f474`); external review not sent. |
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

**Q5 asked whether a correction is an assertion (refuse on non-assertable
edges, mirroring `confirm()`) or an edit (inherit the corrected edge's class).**
I recorded them as balanced. **They are not balanced in this spec's frame, and
the balance was an artifact of the wrong filing.**

> **(b) — the replacement edge inherits the corrected edge's
> `author_of_evidence` and `disclosure`.**

**It is what the ladder already says.** `correct()` retires E and writes E′ with
`supersedes=E`. Under §3 that is permitted only when E′'s effective authority is
≥ E's. Inheriting makes them **equal**, so every legitimate correction passes
and no correction can retire a fact its author was not entitled to retire.

**(a) tests `disclosure`** — *may this be asserted* — which is precisely the
axis error §3 exists to name: *disclosure answers may this be asserted;
supersession asks who may declare this stale.* **A rule that scores well and
answers on the wrong axis is the failure mode this spec was written about**, so
adopting it here would have contradicted the document's own §3.

**Consequence for the implementation:** the ladder check cannot live only in
`apply_supersession`. **It belongs where a supersession is recorded**, and both
paths must reach it — see I9.

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
| **I5** superseded edges render with the SUPERSEDED marker **through the gate** | `test_superseded_reaches_the_model` | CI — **PRECONDITION, see below** |
| **I6** superseded accumulation does not displace current facts | `test_superseded_do_not_crowd_out_current` — frozen: 200 superseded + 40 current, fixed queries, **every current fact retrieved at baseline must still be retrieved** | CI |
| **I7** the MCP surface refuses `system` **and fails closed on unknown** | `test_the_mcp_surface_refuses_system_authorship` · `test_an_unrecognised_author_fails_closed_not_to_user` | CI ✅ **SHIPPED `362f474`** |
| **I8** injection ladder + trust canaries unchanged | existing bench `--compare` | bench gate |
| **I9** **every** supersession path is subject to the ladder — `apply_supersession` **and** `correct()` | `test_correct_is_subject_to_the_ladder` · **`test_no_unguarded_supersession_path`** — asserts the set of `supersedes=` writers equals the set of guarded call sites, so a *future* third path fails the suite rather than shipping | CI |
| **I10** `correct()` does not widen trust: the replacement inherits the original's `author_of_evidence` and `disclosure` | `test_correcting_a_third_party_claim_stays_third_party` | CI |

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
| ~~**Q5** *(was `0002` Q5)*~~ | **RESOLVED by the move, 2026-08-01: (b) inherit the corrected edge's class.** It is what the ladder already requires; (a) answers on the disclosure axis. **Still open and independent: `actor` reaches only an episode f-string** — make it govern or remove it. | resolved / **`actor` open** | research | `actor` before implementation |
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
