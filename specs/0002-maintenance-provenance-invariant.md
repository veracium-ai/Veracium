# Feature spec: the maintenance provenance invariant

Spec-Status: deferred

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **deferred (v7)** — seventh external review 2026-08-02 12:53 UTC. **Invariant approved a
> seventh time.** All eight findings verified; **all stand**. Two are the
> generated-status mechanism drifting from itself, and **finding 3 is a logic
> error in a relation I wrote: N9 forbids the first-time retirement the trust
> matrix calls clean.** **The review was document-only — the archive was not
> delivered**, so no implementation claim could be checked. See §12.

*Retrospective spec for **0.4.4** (GHSA-hcj3-8jqc-wqrp), discharging the
`Spec-Retrospective-Due: 2026-08-07` obligation recorded in `ea2e1ab`. Written
as an audit of the maintenance-time operations, because 0.4.1 and 0.4.4 are the
same shape and one fix does not close a class.*

*🔴 **v1 claimed to audit "every" maintenance-time operation. It did not, and
the word is withdrawn.** Research's review found `portability.import_memory`
absent from §2, §2c and §3 — a file **on the guarded list because I put it
there** — and it is the maximal case for this spec's own lens, not an edge of
it. See §M6. The enumeration below is being rebuilt mechanically; until it is,
this spec reports findings, not coverage.*

| | |
|---|---|
| **Author / session** | dev (`~/Dev/veracium`) |
| **Version** | **v6** — *re-read before editing; quote the version you approve.* Per-review counts are generated (§12). **Every version through v5 was deferred for status prose contradicting other status prose; v6 is the first where the prose is derived rather than checked.** |
| **Status** | *see `Spec-Status:` at the top — canonical.* **Review count and finding totals are generated — §12.** Restating them here is what drifted — the WITHDRAWN wording claimed four external reviews and 34 findings, after the fifth had landed. |
| **Internal reviewers** | research *(trust semantics; and paper 2 is on this exact subject — see §8)* |
| **External review** | required — full spec (touches `graph.py`, `lifecycle.py`, `__init__.py`) |
| **Decision + date** | — · scope narrowed 2026-08-01; M6/M7/M8 moved out. **Status is generated — see §11; nothing here restates it.** |
| **Path** | full |

---

## 1. Problem and motivation

**Two security advisories in four days, both the same shape.** GHSA-r7j7-5jq9-3f5q
(0.4.1) and GHSA-hcj3-8jqc-wqrp (0.4.4) are both *maintenance-time* operations
crossing a trust boundary that the *write path* guards correctly. We fixed two
instances. Nobody has checked whether the class is closed.

**If we do nothing:** the pattern continues. Every maintenance operation is a
place where trust state is recomputed with **no new evidence**, and our review
attention has been on the write path, where the adversary is obvious. The audit
below found **three further defects, two of them shipped**, so the answer to
"was 0.4.4 the last one" is no.

**Alternatives rejected.** *Fix each instance as found* — that is what we have
been doing, and it produced two advisories and no rule. *A prose guideline* —
§2c of the template exists because prose guidance is answered from the same
mental model that produced the defect.

**The invariant this spec proposes:**

> **A maintenance-time operation may narrow trust. It may never widen it, and it
> may never re-derive a provenance field from anything other than new evidence
> from a party entitled to supply it.**

"Narrow" is deliberate and mirrors *configuration may narrow what is assertable,
never widen it* (spec 0001) and `derived_from` capping but never raising (0.1.7).
**Three independent rules with the same shape is not a coincidence; it is the
architecture's actual invariant, stated three times in three places.** This spec
names it once.

---

## 2. Field contracts touched

| field | read / written | its **documented** contract | consumers | preserved? |
|---|---|---|---|---|
| `Edge.valid_from` | ingest; **`confirm()`**; T1 absorption | **"first-known and immutable"** — 0.4.3 CHANGELOG: *"valid_from is set at creation and never mutated"* | `render_edges` (`(since X)` → model context), `edges_since`, E1 clustering, absorption | **NO — violated in shipped code. See M2.** |
| `Edge.needs_confirmation` | `expire()` sets; `confirm()` clears; **T1 reinforcement clears** | "possibly stale — confirm before relying on it"; `confirm()` is the sanctioned exit | `render_edges` (staleness marker), `proactive` | **NO — M3.** |
| `Episode.provenance.author_of_evidence` | ingest; consolidation; **`record_outcome` upgrade-in-place** | "who authored the evidence" | gate routing, consolidation | **NO — M4, erasure without history.** |
| `Provenance.confidence` | ingest; `expire()` decay; T1 both paths | strength of belief | `expire()` floor, T2 design | **Partly — see M5.** |

**Enumerated mechanically** (not from memory — that rule is why 0.4.4 was found):

```
$ grep -rn "\.provenance\.\(confidence\|observed_at\|disclosure\|author_of_evidence\|derived_from\)\s*=\|needs_confirmation\s*=\|\.valid_from\s*=\|model_copy" \
    src/veracium/*.py src/veracium/store/*.py | grep -v ingest.py
__init__.py:493-495   confirm(): valid_from, needs_confirmation, confidence
__init__.py:554       record_outcome(): author_of_evidence  <-- overwrite in place
__init__.py:570       record_outcome(): needs_confirmation
graph.py:107-111      T1 reinforcement: observed_at, confidence, needs_confirmation
graph.py:118-121      T1 absorption: valid_from, observed_at, confidence
lifecycle.py:54       expire() CONFIRM: needs_confirmation
lifecycle.py:114      consolidate(): whole provenance   <-- fixed in 0.4.4
```

**That enumeration was the wrong shape and it is why the audit missed a class.**
Grepping for *assignments* to provenance fields cannot see a write whose
provenance arrived from somewhere else — a reconstructed object, or an edge
built fresh with hardcoded authorship. Re-run mechanically over **store writes**
instead:

```
$ grep -rn "store\.add_edge\|store\.add_episode\|store\.invalidate_edge\|\.model_validate(" \
    src/veracium/*.py src/veracium/store/*.py | grep -v ingest.py
```

**⚠️ That was still wrong — 28 sites, not 24 — and research found it the same
way I found the first correction.** The method moved from *field assignments* to
*store writes*, which was right, but I instantiated it against a **remembered
list** of store writes rather than against the interface definition. **The same
recall-versus-enumerate step the template exists to force, one level up.**

`store/base.py` declares **six** mutators; my grep covered three:

| mutator | sites | in my grep? |
|---|---|---|
| `add_edge` | 9 | ✅ |
| `add_episode` | 9 | ✅ |
| `invalidate_edge` | 6 | ✅ |
| **`delete_episode`** | 1 | ❌ |
| **`forget_user`** | 2 | ❌ |
| **`set_wiki`** | 1 | ❌ |

**Derive the enumeration from `store/base.py`, not from recall** — that closes it
permanently rather than for one more round:

```
$ grep -nE "def (add_|invalidate_|delete_|forget_|set_)" src/veracium/store/base.py
$ # then grep each name across src/, excluding ingest.py
```

`forget_user` is deliberate erasure and `delete_episode` is clean, **but both are
listed anyway** — `delete_episode` is the mechanism that made 0.4.4
*unrepairable* (consolidation deletes its member episodes, so original
authorship is unrecoverable). **The audit fixed how consolidation derives
provenance and never looked at the site that destroys it.** And `set_wiki` is
M8.

**28 sites.** The clean ones are listed in §3 alongside the findings,
because — research's phrasing, and it is right — *an audit listing only its
findings cannot be distinguished from an audit that only looked where it found
them.* The three the assignment-grep could not have found:

| site | why the first method missed it |
|---|---|
| `portability.py:87,91,94,98` | `Edge.model_validate(rec)` → `store.add_edge` — provenance arrives **from a file**, never assigned |
| `__init__.py:614-621` (`correct`) | a **new** `Provenance(...)` with hardcoded authorship, not an assignment to an existing one |
| `__init__.py:462` (`dispute`) | invalidate-only; clean, but absent from a findings-only list |

---

## 2c. Untrusted inputs

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| **host-supplied `author`** (`mcp_server.py:26`, `cli.py:299`) | rejected by enum | rejected by enum | rejected by enum | **host may claim `system`, which shares `MENTIONABLE` with `user`**; and `author` rides on `remember`, an `@server.tool()` — **the model reaches it** | ➡️ **`specs/0008` C1** — **no value of this field clears `needs_confirmation`**; only `confirm()`, which is host-API only |
| **host-supplied `actor`** (`record_outcome`) | defaults `user` | n/a | maps via `_OUTCOME_ACTORS` | **last writer's label silently wins** | **M4 fix: append, never overwrite** |
| **host-supplied `date`** (`confirm()`, `remember()`) | **absence** means now — the only thing that does | **rejected** — `_event_dt` raises | — | **future dates were accepted and unrecoverable; back-dating moved `valid_from`** | **§7f (0.4.5 + 0.4.6): `valid_from` immutable · `observed_at` monotonic · future beyond 1 day rejected at `_event_dt`** |
| **cold-episode set** (consolidation) | no-op below batch | — | — | **mixed authorship** | **M1 (0.4.4): provenance derived from the whole set** |
| **older-version store data** | — | pydantic rejects unknown enum | — | — | ⚠️ **no invariant — no `PRAGMA user_version`.** Carried from spec 0001 Q3; **this empty cell is a gate on that spec, not this one** |

---

## 3. Trust-class matrix — the audit

Every maintenance-time or trust-mutating operation, against the lens:
**does it re-derive provenance, disclosure, authorship or currency from anything
other than new evidence from a party entitled to supply it?**

<!-- GENERATED:matrix -->
| operation | verdict | detail |
|---|---|---|
| `lifecycle.expire()` — LAPSE | ✅ clean | invalidates only; ages against `observed_at` |
| `lifecycle.expire()` — DECAY | 🔴 **open** — `N4-decay` | `confidence *= decay_factor` |
| `lifecycle.expire()` — CONFIRM | ✅ clean | sets `needs_confirmation = True`; narrowing |
| `lifecycle.consolidate()` | ✅ **fixed 0.4.4** — `M1` | provenance across the whole set |
| `lifecycle.consolidate()` — provenance fields | 🟡 **fixed, unreleased** — `N9b-provenance` | `source_type` / `evidence_ref` |
| `compile.py` (wiki) | ✅ clean | filters `use_only` and `third_party_influenced` |
| `proactive.assemble()` | ✅ clean | `if not e.assertable: continue` |
| `confirm()` | ✅ **fixed 0.4.5** — `M2` | first-known vs liveness |
| T1 reinforcement | 🟠 **unimplemented** — `M3` | clears `needs_confirmation` |
| `record_outcome()` upgrade-in-place | 🟠 **unimplemented** — `M4` | overwrites `author_of_evidence` |
| T1 `confidence = max(...)` | 🟠 **unimplemented** — `M5` | a new edge arrived |
| `import_memory()` | 🔴 **open** — `N9t-transfer` | trust fields reconstructed from a file |
<!-- /GENERATED:matrix -->

**This table is generated.** The sixth review found it still calling
`expire()` DECAY *"✅ clean — narrows only"* while the generated ledger said
`N4-decay` was open and permits confidence **increases**. **A trust-class matrix
is a status table**, and generating the ledger while hand-maintaining this one
left the mechanism governing only the regions it wrote.

**Architectural note, and it is the most important line in this spec.**
`compile.py` and `gate.py` both have **correct** defences. Both were bypassed by
0.4.4 anyway, because consolidation corrupted the very field they key on
(`third_party_influenced`). **A defence in the right place is not sufficient if
an upstream maintenance operation can rewrite its input.** That is the general
form of the bug, and it is why an audit of *mutation sites* finds things an audit
of *decision sites* does not.

### M2 — `confirm()` mutates `valid_from` (shipped, 0.4.4)

`__init__.py:493` is `edge.valid_from = _event_dt(date)`. **Reproduced:**

```
stated in January.       valid_from = 2026-01-15
  renders: prefers: dark mode (since 2026-01-15) [possibly stale — confirm…]
user confirms in March.  valid_from = 2026-03-01
  renders: prefers: dark mode (since 2026-03-01)
```

**This is precisely the defect C′ shipped in 0.4.3 to eliminate**, in a sibling
path the fix did not touch. `render_edges` emits `(since X)` into answer context,
so this is **a false statement in front of the model**, not merely lost history —
C′'s own words. Worse: **0.4.3's CHANGELOG asserts *"valid_from is set at
creation and never mutated"***, which is false as shipped. We published a
BREAKING semantics change and did not honour it.

**Fix:** `valid_from` is immutable. A confirmation is new evidence about
*liveness*, so it advances `provenance.observed_at` — the same resolution C′
applied to reinforcement.

### M3 — cross-author clearing of `needs_confirmation` (shipped)

`graph.py:111` clears `needs_confirmation` on reinforcement. The 0.4.1 guard
(`graph.py:94`) compares **disclosure class**, and `USER` and `SYSTEM` **share
`MENTIONABLE`**. Reproduced: a `SYSTEM`-authored restatement clears a `USER`
fact's staleness flag.

`needs_confirmation` renders as *"[possibly stale — confirm before relying on
it]"*. It is a **question addressed to the user**. A system restatement answering
it is the same speaker/witness confusion that caused spec 0001's deferral, one
layer down. `THIRD_PARTY` is correctly blocked — the 0.4.1 guard does its job;
it just guards the wrong axis for this field.

**Not a disclosure-class crossing, so materially milder than 0.4.4** — nothing
becomes assertable that was not. It removes a caveat on someone else's
authority.

**OBSOLETE released behaviour (0.4.5):** the fix shipped was *"clears only on
evidence from the same author class, or via `confirm()`"*. **It is inadequate and
is not the rule.** It closed cross-*class* clearing and left same-*class*
clearing open — the case that matters, because **the host chooses the class**,
and `author` rides on `remember`, which the model calls.

**Current rule → `specs/0008`:** only `confirm()` clears `needs_confirmation`;
**no value of any provenance field ever does.**

### M4 — `record_outcome` overwrites authorship without history (shipped)

`__init__.py:554`: `prior.provenance.author_of_evidence = author` on
upgrade-in-place. The last writer's `actor` label silently wins and **the prior
authorship is unrecoverable** — in a system whose stated principle is
**supersession-never-erasure**. The host controls `actor` in both directions, so
this is not privilege escalation; it is provenance destruction.

**OBSOLETE released behaviour (0.4.5):** the fix shipped appends a phrase to the
episode summary and **still overwrites the structured field**. `summary` is
rebuilt on every upgrade, so the trail survives **exactly one hop** —
`system → user → system` reduces to *"prior was user"*. **The "note"
alternative is withdrawn**; a note cannot be queried, gated on, or exported.

**Current rule → `specs/0009`:** an append-only chain of outcome episodes, each
with its own provenance, ordered by a store-assigned per-chain sequence.

### M6 / M7 / M8 — MOVED OUT on 2026-08-01

**These three were findings of this audit and are no longer specified here.**
The audit found them; that does not make this their spec. **This document is a
retrospective for a shipped hotfix and must be closeable. A proposal is not**,
and keeping unshipped proposals inside a finished record meant `accepted` moved
further away with every finding, while everything citing `0002` waited behind
all of them.

| finding | now | why there |
|---|---|---|
| **M6** `import_memory` has no trust boundary | **`specs/0005-import-trust-boundary.md`** | Carries the docs-recipe trigger. Writing it up separately surfaced a **new gap in the fix**: the cap keys on the export header's `user_id`, which is inside the attacker-written file (`I-Q1`). |
| **M7** `correct()` elevates non-assertable facts | **`specs/0003-supersession-authority.md` §1b** | **Not a maintenance finding at all.** `correct()` is a *supersession* path, so it is 0003's subject — and moving it revealed that `apply_supersession` and `correct()` are **disjoint**, i.e. the ladder as specified had an uncovered maximum-authority bypass. |
| **M8** the wiki serves a revoked trust decision | **`specs/0004-derived-views-and-revocation.md`** | Clean fix, no natural home, no dependency on anything here. |

**Two of the three moves changed the content, not just the filing** — which is
the argument that the split was structural rather than administrative. M7's open
question **dissolved** once it was read against the ladder instead of against
the maintenance lens; M6 **grew** a blocking question that this document's frame
had no reason to ask.

**What stays here:** the findings owned by this spec plus the 28-site
enumeration — **see §11 for which are shipped and which are open; this sentence
deliberately names none of them.** It said *"M1–M5, all shipped or resolved"*
while `N4-decay` was open and owned here.

### M5 — merge-time `confidence = max(...)` (design, partly shipped)

T1 (`graph.py:109`, `:121`) and T2's approved design both take
`confidence = max(members)`. **`max` raises**, which the invariant forbids
without new evidence. On T1 the incoming edge *is* new evidence, so it is
defensible; **on T2 dedup it is not — dedup is maintenance-time bookkeeping over
existing statements.** T2 is unshipped, so this is a design correction, not a
defect. **It must be settled before T2 lands, not during.**

---

> **RESOLVED 2026-08-01 21:04 (research).** **T1: `max` stands.** A new edge
> arrived, so `max` retains the strongest value earned by an actual evidentiary
> event. **T2: `max` is not acceptable — the survivor keeps its own confidence,
> unchanged.** No new edge arrives at T2; it is recognition that two existing
> statements match, and raising confidence there **manufactures lifetime from
> recognition** exactly as advancing `observed_at` would manufacture freshness.
>
> **T2 must change no field encoding evidentiary strength or currency** —
> `observed_at` not advanced, `needs_confirmation` not cleared, `confidence`
> unchanged. **N1 is absolute and nothing is excepted from it** — under §7c,
> `min` is a property of *constructing a new edge*, never of mutating an
> existing one. The merge record keeps the absorbed edge's value recoverable.
>
> This is the write-time-evidence vs maintain-time-bookkeeping rule that already
> settled `needs_confirmation` in July, applied to a different field. **Two
> fields now follow it, which makes it a rule rather than a precedent.**
>
> **Recorded against my own argument:** I offered a blast-radius measurement —
> `confidence` has one live consumer and no ranking effect — as the case for
> letting `max` stand. Research's ruling names that as answering *"how bad is
> it"* when the question was *"is it justified."* Severity bounds the cost of
> being wrong; it says nothing about legitimacy, and I substituted the first for
> the second. **T2 is unwritten, so this costs nothing today and becomes a
> constraint on its design.**

## 3b. Authorization and scope

n/a — no operation here crosses a user, tenant or scope boundary; all are
single-`user_id` in-store transformations. Recorded rather than omitted because a
blank heading is indistinguishable from an unasked question.

---

## 4. Behaviour

| | before | after |
|---|---|---|
| confirm a fact stated in January, in March | context reads `(since March)` | `(since January)`; `observed_at` advances to March |
| system-authored restatement of a stale user fact | staleness marker removed | marker retained — **only `confirm()` clears it**; no field value ever does (`specs/0008`) |
| second outcome recorded by a different actor | prior authorship overwritten | prior authorship retained |

**Interfaces:** no signature changes. **Migration:** none — no backfill. Edges
whose `valid_from` was already moved by `confirm()` **cannot be repaired**: the
original date is not recorded anywhere. That is unrecoverable and must be said in
the changelog.

---

## 5. Regime analysis

- **Duration is the regime**, and it is why these survived. Every defect here
  needs *elapsed time* to become visible: `confirm()` needs a fact old enough to
  go stale, consolidation needs 30 days and 8 episodes, expiry needs a lifetime
  to pass. **Fixtures are instantaneous.** Our test suite runs in 17 seconds and
  cannot, in principle, reach the regime where maintenance defects live.
- **Thresholds:** `consolidate_after_days` (30), `consolidate_min_batch` (8),
  `volatility_lifetime_days`, `confidence_floor`.
- **Do the tests reach it?** Only by injecting `now=`. **Release class: stable,
  so an unreachable regime blocks** — §6 checks all use explicit clock injection
  over simulated months rather than wall-clock.
- **Cold vs warm:** maintenance is where the difference *is*; a store that never
  runs `maintain()` exhibits none of this.

---

## 6. Invariants and executable checks

| invariant | executable check | where |
|---|---|---|
| **N1** `valid_from` is **never mutated on a persisted edge**, by any operation, without exception | `test_valid_from_immutable_across_every_mutation_site` — parametrised over confirm / reinforce / absorb / expire / consolidate | CI |
| **N2** `confirm()` advances `observed_at`, not `valid_from` | `test_confirm_advances_liveness_not_first_known` | CI |
| **N3** ➡️ **`specs/0008`** — only `confirm()` clears `needs_confirmation`; no field value ever does | `0008` C1–C6 | `0008` |
| **N4** no maintenance operation raises `disclosure` toward assertable **or raises `confidence`** | `test_no_maintenance_op_widens_disclosure` · **`test_no_maintenance_op_raises_confidence`** — property-based over a random op sequence, **run under a hostile `MemoryConfig`** | CI |
| **N4b** `MemoryConfig` rejects **`decay_factor` and `confidence_floor`** outside `[0, 1]`, and `NaN`/`±inf` | `test_config_bounds_are_validated` — **both fields** × 0 · 1 · interior · >1 · negative · NaN · +inf · −inf | CI |
| **N4b′** the exact boundaries **remain accepted** | `test_boundary_configs_are_still_valid` — `0.0` and `1.0` on both fields; **a regression test, because the cheapest wrong fix is an exclusive bound** | CI |
| **N4c** a declared bound on **every** bounded mutable trust field is enforced **on assignment**, not only on construction | `test_declared_bounds_hold_under_in_place_mutation` — **enumerated from the models, not hand-listed**: every `Field` on `Provenance`/`Edge` carrying `ge`/`le`/`gt`/`lt` is mutated past its bound and must raise. Verified today that `validate_assignment` is `False` and `confidence *= 2.0` yields `1.8` | CI |
| **N4d** the mutation happens through the **real path**, not a synthetic assignment | `test_decay_through_expire_cannot_exceed_the_bound` — drives `expire()` with a hostile config rather than poking the model | CI |
| **N8** every store-mutator call site carries a verdict and a test | `test_every_store_mutation_site_carries_a_verdict` → `specs/audit_manifest.py --check` | CI |

**N4 was extended to `confidence` on 2026-08-01** (research's 03:45 amendment 3,
which never landed and became load-bearing when M5 was ruled). **The M5 ruling
created a rule with no executable check** — *T2 keeps the survivor's own
confidence* — and by this spec's own template rule an invariant without a check
does not count. Extending N4 makes it enforcement rather than a sentence.

The two clauses are the same statement about different fields, which is why they
belong in one invariant: **maintenance-time bookkeeping may not manufacture
what only evidence can earn** — assertability in the first case, strength in the
second.
| **N5** ➡️ **`specs/0009`** — outcome authorship is an append-only chain; `0009` H7 asserts on **structure**, not on a retained value | `0009` H1–H7 | `0009` |
| **N6** consolidation provenance derives from the whole set (0.4.4) | existing `test_consolidation_provenance.py` | CI |
| **N7** a full `maintain()` cycle over simulated months never moves an edge from UNVERIFIED to GROUNDED | `test_maintenance_never_promotes_across_the_gate` — **an end-to-end gate over the observable boundary.** Not the general form; see N9 | CI + bench |
| **N9** *(replaces N7's general claim)* for an operation whose evidence class is **`none`** (§6a), the post-state is no stronger than the pre-state under the partial order **defined below** | `test_evidence_free_maintenance_is_monotone` — property-based over random op sequences | CI |
| **N9t** a **`transfer`** may not raise any trust field above the importing principal's cap, nor claim new observation currency | `test_transfer_cannot_raise_trust_or_currency` | CI |
| **N10** history preservation is checked **separately** from trust rank | `test_maintenance_preserves_authorship_history` | CI |

**N7 is the strongest *end-to-end* check and it is not the general form.**
It is stated over the *observable boundary* — what the model may assert — which
is why it survives refactors that instance checks do not. **But it tests one
transition**, and three of this spec's own findings never cross it: **M2** changes
a date inside a tier, **M3** removes a caveat without necessarily changing tier,
and **M4** destroys authorship without touching disclosure at all. **A check that
misses three of your six findings is not their general form**, and calling it one
is what the second external review objected to. **N9 carries that role.**

---

## 6a. The partial order N9 quantifies over

**Second external review item 4: v2 named a partial order and never defined
one.** A field list is not a relation, and a property test cannot implement one.
Defined here so N9 is executable rather than aspirational.

**For an operation of evidence class `none`, on a single persisted edge**, every
clause must hold:

```
post.active              <=  pre.active              # a retired edge stays retired
post.invalidation_reason ==  pre.invalidation_reason # why it retired may not be rewritten
post.assertable          <=  pre.assertable          # False is weaker than True
post.needs_confirmation  >=  pre.needs_confirmation  # True  is weaker than False
post.disclosure          <=T pre.disclosure          # MENTIONABLE > USE_ONLY > QUARANTINED
post.confidence          <=  pre.confidence
post.observed_at         <=  pre.observed_at         # currency may not advance
post.author_of_evidence  ==  pre.author_of_evidence  # categorical: equality
post.derived_from        ==  pre.derived_from        # categorical: equality
post.valid_from          ==  pre.valid_from          # immutable identity, §7c
```

**`<=T` is the disclosure trust order**, taken from the enum's own documented
meanings (`schema.py:45`): `MENTIONABLE` (may be volunteered) **>** `USE_ONLY`
(may shape behaviour, never volunteered) **>** `QUARANTINED` (never asserted).

**`invalidation_reason` is in the relation, not only in prose.** v5 said it was
*"preserved alongside `active`"* and left it out of the product rule, so N9
could pass while a retirement's recorded cause changed — `superseded` rewritten
to `lapsed` loses the fact that something replaced it, which is exactly what
`render_edges`' SUPERSEDED marker depends on. **A field described as preserved
and absent from the relation is not preserved by anything.**

**`active` is a separate clause too, and it is the one v4 missed.** An
evidence-free operation could **reactivate a retired edge** while every other
clause held — `assertable` stays `False` (the edge is quarantined), disclosure
unchanged, dates unchanged. **Persistent trust state widens and N9 passes.**
`invalidation_reason` is preserved alongside it: a re-activated edge that kept
its reason would render as history while being live.

**`disclosure` is a separate clause from `assertable`, and third external review
item 6 is why.** `assertable` is derived and collapses two of the three levels:
a move from `QUARANTINED` to `USE_ONLY` leaves `assertable` `False` throughout,
so **a maintenance operation could widen disclosure without N9 noticing.** N4
would catch it, but then **N4 — not N9 — would be doing the work**, and N9 would
not be the general form it claims to be.

**The boolean clauses express trust strength, not ordinary ordering** —
`needs_confirmation` is written `>=` because *keeping* the caveat is the weaker,
permitted direction. **Authorship and `derived_from` are categorical**: there is
no "less trusted author" to move toward, so the only safe relation is equality,
and any change is a violation regardless of direction. **That is what makes N9
catch M4**, which N7 misses entirely.

**`observed_at` is the clause most likely to be argued with**, so: a
maintenance operation may not advance currency, because currency is a claim
about evidence and maintenance has none. Advancing it is the same manufacture
`0002` M5 forbids for `confidence` at T2 — *manufacturing freshness from
recognition*.

### Which operations N9 applies to

**Fourth external review item 5: this table and the manifest gave opposite
answers for `import_memory`, and neither was wrong on its own terms.** The
manifest asked *"evidence-bearing?"* and answered **no**; this table asked
*"evidence-free?"* and answered **no**. **Two negations of one question is how a
contradiction hides** — reading either alone looks consistent.

**Both columns are replaced by one positive vocabulary**, declared per call site
in `audit_dispositions.py` and CI-checked:

| class | meaning | N9 applies? |
|---|---|---|
| **`act`** | an authorised call through a dedicated entry point that is **not model-reachable** — `0008`'s principle: *the act is the evidence* | no |
| **`observation`** | new content arriving from outside and being extracted | no |
| **`none`** | maintenance — no new information, only **recognition of existing records** | **yes** |
| **`transfer`** | records moved between stores | **yes — via N9t** |

> **N9t — the `transfer` regime.** A transfer may not raise any trust field
> above the **importing principal's cap**, and **may not claim new observation
> currency**: `observed_at` is carried from the record, never set to now, and
> `valid_from` is never advanced. The `0005` cap applies on top; N9t is the
> floor that holds whether or not `0005` has landed.

**Fifth review, finding 5: `transfer` was in neither regime** — no evidence
authority to widen trust, and outside N9's formal relation, constrained only by
prose delegation to `0005`. **A class whose constraints exist only as a pointer
to another spec is unconstrained until that spec lands.** N9t closes it now, and
`transfer` becomes `observation` only when an authenticated source exists.

**`import_memory` is `transfer`, and that is the reconciliation.** The
operator's *act* is authorised; **the records it carries are vouched for by
nobody.** So it is not `act` (the act authorises the move, not the content) and
not `observation` (nothing was observed). It gets **no evidence exception**: it
takes `0005`'s cap, and it becomes `observation` only if `0005` ever
authenticates the source — which `I-Q1` shows is harder than it looked, since
the cap keyed on a field inside the imported file.

**Current tally: 12 `act` · 7 `observation` · 7 `none` · 2 `transfer`.**

**This is a reviewed classification, not a derived fact.** The *call sites* are
mechanically enumerated from the AST; the `evidence` column is hand-authored,
and `--check` proves somebody chose a valid class, **not that the choice follows
from anything.** The sharpest illustration: every `apply_supersession` write is
`observation` **while M3 — the open defect — is precisely that a repetition can
be mistaken for authoritative new evidence.**

**Making it mechanical needs an evidence capability checkable at the entry
point** — `0008`'s principle generalised — and that does not exist. **`act` is
the one class with a mechanical proxy today**: those entry points are absent
from `mcp_server.py`'s tool list, which is checkable and is what `0008` C1
rests on.

### Consolidation needs a second rule

**N9 as written compares one edge before and after. Consolidation maps a *set* of
episodes to a *new* object**, so there is no pre-state to compare against:

> **N9b — set→output**, over **every** trust-bearing field, because a rule that
> constrains three of them permits manufacture in the rest:
>
> | field | rule |
> |---|---|
> | `disclosure` | **no stronger than the least-trusted input** (`min` under `<=T`) |
> | `author_of_evidence` | **`SYSTEM`** — what the output *is*, never an inherited author |
> | `derived_from` | retains **any** third-party influence present in the set |
> | `confidence` | **`<= min(inputs)`** — a summary is not better evidence than its worst member |
> | `observed_at` | **`<= max(inputs)`**, and never *now* — recognition is not observation |
> | `valid_from` | **`min(inputs)`** — first-known of the set, by construction (§7c) |
> | `needs_confirmation` | **`True` if any input has it** — the caveat propagates |
> | lineage | every input is recorded; **a member may not be dropped silently** |
> | mixed currency | the spread is **retained, not averaged** — see below |

**Third external review item 6:** the previous N9b specified only the first three
rows, so **a consolidation could satisfy it while manufacturing confidence or
freshness** — the precise defect M5 forbids at T2, one operation over.

**Mixed currency is the row most likely to be got wrong.** Consolidating
episodes from January and June produces one record. Taking `max` makes the
January content look current; taking `min` makes the June content look stale.
**Neither is true, so the summary must not claim a single currency it does not
have** — `observed_at` bounds it and the lineage carries the spread. *(Consistent
with the standing rule: surface the tension, never reconcile it.)*

**That is M1's shipped rule** (0.4.4, GHSA-hcj3-8jqc-wqrp), stated as an
invariant rather than as a fix, which is what lets it be checked on operations
M1 never touched.

**History preservation stays out of both** — it is N10. **Erasing history is not
modelled as a trust rank**, and folding it in would let a "narrower" post-state
launder a destroyed record.

---

## 7. Failure modes and reversibility

- **Silent failure:** all four defects are silent by construction — they change
  provenance, and provenance is only visible through `introspect()` or a
  rendered marker most users never diff. M2's symptom is a wrong date in an
  answer; M3's is a *missing* caveat, which is invisible.
- **Reversibility:** the fixes are reversible. **The damage is not** — M2 has
  already destroyed original `valid_from` values in any store where a stale fact
  was confirmed, and consolidation has already destroyed member episodes.
- **Partial failure:** **`expire()` is crash-safe; `consolidate()` is not.**
  `expire()` is per-edge and idempotent. **`consolidate()` is neither**: it
  deletes every member episode
  *before* writing any replacement (`lifecycle.py:123`), so a crash between the
  loops is **total loss of that batch**, and a retry re-consolidates whatever
  survived. **Narrowing trust is not crash consistency** — a narrower state can
  still be destroyed, and consolidation is the one maintenance operation that
  destroys rather than retires. Contract frozen in **§7e**; until it lands, the
  honest statement is *"`expire()` is crash-safe; `consolidate()` is not."*
- **New attack surface:** none. This spec only removes capability.

---

## 7a / 7b. M4 and M3 — MOVED OUT on 2026-08-01

**Both were frozen designs living inside a retrospective, which is the same
structural error that forced the first split** — and I made it again, in the
commit that applied v2's amendments. A retrospective must be closeable; a frozen
design awaiting implementation is not.

| finding | now | why it moved |
|---|---|---|
| **M3** staleness clearing | **`specs/0008-staleness-clearing.md`** | The rule is settled by **R2 + R3**; what remains is acceptance and a one-conditional deletion. It was blocked only by this document. |
| **M4** outcome authorship | **`specs/0009-outcome-authorship-history.md`** | The second review required **head and concurrency semantics** before acceptance; that is design work with its own open questions, not a line in a ledger. |

**Both are inadequate fixes in a released version, not open questions** — 0.4.5
claimed both and neither holds. That is the argument for giving them specs that
can be *accepted*, rather than leaving them behind one that keeps being
deferred.

---

## 7c. R1 — frozen: `valid_from` is immutable edge identity

**External review item 1.** The spec asserted both *"never mutated after
creation by any operation"* (N1) and *"`valid_from = min` stays the sole
exception"* (M5). **Research owns the contradiction** — the exception was in
their M5 ruling.

**Narrow correction to the reviewer's premise, which does not save it.** The
shipped code is *technically* consistent: absorption mutates `graph.py:128`, but
`store.add_edge(edge)` is `graph.py:143`, so **the edge is not yet persisted**.
Under *creation = persistence* N1 holds, which is why its test passes. **A
contract that survives only under an unstated reading of one word is not a
contract**, and T2 applies `min` to an existing **survivor**, which breaks it
outright.

**Frozen — option (1), immutable edge identity:**

> `valid_from` never changes on a persisted edge. A merge whose first-known date
> is earlier than the survivor's **constructs a new edge**:
>
> 1. **new `id`**, `valid_from = min(inputs)`;
> 2. the inputs are **superseded, never mutated** — `active = False`,
>    `invalidation_reason = "absorbed_duplicate"`, `supersedes` links the new
>    edge to them;
> 3. the **structured merge record** retains both pre-merge states (T2 v2.1
>    delta (d)) — it is evidence, not a comment;
> 4. **the new edge is the only active one** for that `(subject, relation)`, so
>    nothing renders twice.

**The "(or merge record)" alternative is withdrawn.** Second external review item
7: they are not equivalent, and a merge record alone leaves *which edge is
current* and *how the earlier first-known date renders* undefined. **Clause 4 is
the one that alternative could not answer.**

**The cost is already paid, which is the decisive argument and not the one I
gave.** T2 v2.1 delta (d) already requires a structured merge-event record with
full pre-merge states. **Option (1) does not add a merge record; it makes the one
we already agreed to load-bearing instead of decorative.** Marginal cost: an
edge id and a supersession link.

**And it removes the exception rather than relocating it** — N1 becomes
absolute, and `min` becomes a property of *constructing* a new edge rather than
of mutating an existing one.

**Why not option (2), monotonic correction.** *"No operation may move
`valid_from` later"* forbids the direction of the C′ defect we have already had
and **permits the one that still carries risk**: a merged edge rendering
`(since <earlier>)` for an unverified claim that now looks longer-established.
**A rule shaped to forbid only the failure we have already had is how we get the
next one.**

---

## 7d. Decay bounds — configuration may not invert an invariant

**External review item 8, and it is worse than reported.** `MemoryConfig` is a
plain `@dataclass` with no validation:

```
MemoryConfig(decay_factor=2.0)   -> accepted
MemoryConfig(decay_factor=nan)   -> accepted
MemoryConfig(decay_factor=-1.0)  -> accepted
```

`expire()` does `confidence *= decay_factor`, so **a host config can make a
maintenance operation RAISE confidence — which makes N4 false as written**,
three hours after it was extended to cover `confidence`.

**And the field's own declared bound does not stop it.** `Provenance.confidence`
is declared `Field(default=0.9, ge=0.0, le=1.0)`, which reads as enforcement and
is not:

```
>>> p.model_config.get("validate_assignment", False)
False
>>> p.confidence *= 2.0
1.8                      # declared le=1.0
>>> p.confidence = float("nan")
nan
```

**Pydantic validates on construction, not on assignment, and every maintenance
site mutates in place.** So the bound holds exactly where trust data is *built*
and nowhere it is *changed* — which is the entire subject of this spec. This
generalises past `confidence`: **no `Field(...)` constraint on `Provenance` or
`Edge` is enforced on the mutation path.**

**Frozen, both halves:** `MemoryConfig` validates on construction — `0 ≤
decay_factor ≤ 1`, finite; `0 ≤ confidence_floor ≤ 1`, finite — **and** the
models that carry trust fields set `validate_assignment=True`, so a declared
bound means what it appears to mean. **Invalid configuration fails at
construction, not by N4 discovering corruption after maintenance has run.**

**The general statement, which is why this is not a footnote:** *configuration
may narrow, never widen* has been one of our recurring invariants since 0001,
and it was **never enforced on the numeric knobs**. N4b is the enforcement.

---

## 7e. Consolidation must be crash-safe

**External review item 9 — not a hypothesis, the shipped order:**

```python
for e in cold:  store.delete_episode(e.id)     # lifecycle.py:123
for r in new:   store.add_episode(...)         # lifecycle.py:125
```

**Delete-all, then write.** A crash between the loops loses the cold episodes
**with no replacement at all** — total loss, not the partial states the review
enumerates. *"A partial `maintain` is safe because every operation narrows"* is
false in the worst available direction: **narrower is not the same as
recoverable**, and consolidation is the one maintenance operation that destroys
rather than retires.

**Owned by `specs/0010`**, which picks one of the two strategies this contract
left open — third external review: acceptance authorises implementation, so
*"atomic or a state machine"* would authorise two materially different designs
without specifying either.

**Frozen persistence contract:**

> - consolidation commits **atomically**, or runs as a recoverable state machine;
> - **originals are not deleted until the replacement and its provenance lineage
>   are durable**;
> - retry is **idempotent**;
> - partial state is detected and repaired before ordinary reads depend on it.

**§7 must stop claiming crash-safety follows from narrowing.** It does not
follow, and this is the operation that proves it.

---

## 7f. M2 — frozen: the confirmation-time contract

**Second external review item 2:** 0.4.6's behaviour was asserted in the header
and the changelog and **specified nowhere**, while N2 still said only that
`confirm()` *"advances `observed_at`"* — which constrains neither the response
nor a hostile date. **A released fix that is not pinned is not closed.**

> **Event dates.** Any host-supplied `date` more than `MAX_FUTURE_SKEW`
> (**1 day**) beyond now is **rejected** — `ValueError`, not clamped. Applied in
> `_event_dt`, the single point every event date passes through, so
> `remember` · `confirm` · `correct` · `record_outcome` are covered by one rule.
> **Malformed dates are rejected**, and an offset-bearing timestamp is
> **converted** to UTC, never relabelled — `.replace(tzinfo=utc)` discarded the
> offset, so a `-12:00` value bypassed the skew limit by 12 hours.
>
> **`observed_at`.** `max(existing, accepted event_time)` — monotonic, so a
> back-dated confirmation cannot move currency backwards.
>
> **`valid_from`.** Never touched by confirmation. Immutable per §7c.
>
> **`confirm()` returns** `{"confirmed": <edge_id>, "valid_from": <the persisted
> edge's immutable value>, "confirmed_at": <the accepted event date>}`.
> **`valid_from` in the response is the stored value and never the caller's
> argument.**

**Why rejection rather than clamping.** A future event date has no legitimate
meaning — the event date records *when a statement was made*, not what it is
about, so *"the contract expires in 2027"* is a value and never a date. Clamping
would silently rewrite a caller bug.

**Why this needed both halves.** The monotonic `max` that correctly defeats
back-dating is **exactly what made forward-dating permanent**: one future date
removed an edge from lapse, decay and staleness flagging for 73 years, with no
API to undo it. **Fixing back-dating alone created the unrecoverable case.**

**N2 replaced.** *"`confirm()` advances `observed_at`, not `valid_from`"* is
retained as one clause of a wider invariant:

| invariant | executable check | where |
|---|---|---|
| **N2a** confirmation advances `observed_at`, never `valid_from` | `test_confirm_advances_liveness_not_first_known` | CI |
| **N2b** a back-dated confirmation does not move currency backwards | `test_backdated_confirmation_is_monotonic` | CI |
| **N2c** a future date is rejected at every entry point | `test_a_future_event_date_is_rejected` · `test_a_future_date_cannot_enter_through_ingest_either` | CI |
| **N2d** the skew boundary is tested on both sides | `test_clock_skew_is_tolerated_but_a_typo_is_not` | CI |
| **N2e** repeated confirmation is idempotent in `valid_from` | `test_past_and_today_still_work` | CI |
| **N2f** the response reports the **persisted** `valid_from` | `test_confirm_returns_the_real_valid_from_not_the_confirmation_date` | CI |

**All pass today.** N2b is the one whose behaviour predates the fix and was
never pinned. **Which release carries which clause is in §11 and is generated** —
this section deliberately names no version, because it named 0.4.5/0.4.6 and was
still saying so after 0.4.7 shipped.

---

## 8. Claims and limits

- **What we will say:** *"0.4.5 **attempted** fixes for three provenance defects
  identified during a reviewed audit of the store-mutation sites scoped to spec
  0002. **The M2 fix holds; the M3 and M4 fixes were subsequently found
  inadequate** and are governed by specs 0008 and 0009. Import, supersession and
  derived-view findings are governed by specs 0005, 0003 and 0004."*

  ⚠️ **WITHDRAWN wording, quoted here as history:** v1 said *"an audit of every
  maintenance-time operation"* after §1 had withdrawn that claim; v2/v3 said
  *"fixes three provenance defects"* after §11 recorded that two of the three do
  not hold. **Both phrases are in `specs/withdrawn_phrases.py` and the lint
  fails if either reappears outside a block marked WITHDRAWN or OBSOLETE.**
  **The release claim has now been wrong in the same direction in three
  consecutive drafts**, and each time the correcting fact was already in the
  document.

  **"Mechanically derived" is also withdrawn** — the call-site *enumeration* is
  mechanical; the per-site **classification** is hand-authored (§12 item 5).

  **⚠️ WITHDRAWN wording:** the previous release language claimed *"an audit of
  every maintenance-time operation"*, and §1 had already withdrawn exactly that
  claim. It survived into the release language and out the door. External review
  item 6 caught it.
  **This is the fourth claim-versus-artifact gap** — after the `_cover`
  docstring, the `valid_from` changelog and the r2 headline — **and the first an
  outside reader found before we did.** A retraction that is not applied by
  `grep` is not applied.

  **Also corrected:** the limits below said *"nine mutation sites"* while the
  enumeration had grown to **28**. Both numbers were in the same document.
- **What this does NOT establish.**
  - **Not that the class is now closed.** It establishes that **28 store-mutator
    call sites** were enumerated *from the mutator interface* and each given a
    verdict — see **`specs/generated/0002-audit-manifest.md`**, generated and CI-verified,
    not asserted. **15 clean · 2 fixed · 4 open · 7 moved** — 17 of 28
    unaffected. **States are declared, not inferred from the rendered table**;
    deriving them by searching rows for emoji shipped two different totals in
    one review package.
  - **N7 is not the general invariant**, and the previous draft called it one.
    It tests a single UNVERIFIED→GROUNDED transition across a full `maintain()`;
    **M2 changes a date without changing tier, M3 removes a caveat without
    necessarily crossing tiers, and M4 destroys authorship without touching
    disclosure at all.** N7 stays as an end-to-end gate. **N9** is the general
    form.
  - Not that `expire`, `compile` and `proactive` are *correct* — only that they
    do not violate **this** invariant. `compile` and `gate` were both individually
    correct and were bypassed anyway.
  - No measurement of real-world exposure. We do not know how many deployments
    run `maintain()`.
- **⚠️ Conflict of interest, stated because nobody else will.** Research's
  **paper 2 is titled *"Maintenance Is an Attack Surface"***, is preregistered,
  and has not run. This audit produces exactly the evidence that paper wants,
  from our own codebase, found by us. **That is a reason for more caution in
  reporting it, not less.** Recommend: the paper cites the two advisories as
  public artifacts with dates, and does **not** cite this internal audit as a
  finding; and no marketing framing presents an internally-found bug count as
  evidence of the thesis. Research's call, flagged before the findings are
  written up rather than after.

---

## 9. Brief for the external reviewer

**All three of v1's "least sure of" items have since been answered — two of them
by you.** Repeating them would have wasted a round, so they are recorded as
resolved and replaced with what is actually uncertain now.

| v1 uncertainty | outcome |
|---|---|
| *Is N7 the general form?* | **No.** You showed it misses M2, M3 and M4. N7 is an end-to-end gate; **N9 + §6a** is the general form, now defined rather than named. |
| *Is "same author class" the right axis for M3?* | **No** — and the replacement was wrong too. §7b's *"user-authored observation"* relied on `author`, which **§2c of this document lists as adversarial**. Ruled strict (R3), moved to **`0008`**. |
| *Is `expire()`'s decay genuinely narrowing?* | **No.** `MemoryConfig` was unvalidated, so `decay_factor=2.0` raised confidence — **and `validate_assignment` is `False`, so the declared `le=1.0` on the field never applied on the mutation path either.** N4b–N4d. |

**What we are least sure of now.**

1. **Whether §6a's `observed_at` clause is too strong.** It forbids maintenance
   advancing currency at all. That is right for T2 and for decay; we are less
   certain there is no legitimate maintenance-time liveness signal we have not
   thought of.
2. **Whether N9's categorical equality on `author_of_evidence` / `derived_from`
   is the right shape**, or whether a *lattice* (a merge may only move toward
   less-trusted) is needed once `0009`'s chains and `0003`'s ladder both land.
   Equality is the conservative choice and may be too blunt.
3. **Whether splitting M3/M4/M6/M7/M8 out was right.** It made each closeable and
   left this document a record — but **five specs now cross-reference each other**,
   and a reviewer of any one of them sees less of the whole than a reviewer of v1 did.

**Where we suspect we have overstated.** §1's claim that three same-shaped rules
reveal "the architecture's actual invariant" is a satisfying sentence built on
three data points. **It has since grown to five instances, which is either
confirmation or a stronger selection effect** — we keep finding it because we
keep looking for it.

**What would change our minds.** A maintenance operation that legitimately needs
to widen trust. We still cannot construct one.

**What is different in this submission.** The **28-site manifest is included** —
`specs/generated/0002-audit-manifest.md` plus `audit_manifest.py` and
`audit_dispositions.py`. **Its absence was item 9 last time**, and it was the one
artifact built specifically to make the coverage claim checkable. It is generated
from the mutator interface and CI-verified; `--check` fails when the code and the
verdicts disagree.

---

## 10. Open questions

| # | question | class | who | by when |
|---|---|---|---|---|
| ~~Q1~~ | **ANSWERED 2026-08-01 21:04 — no.** *(Corrected by research the same hour: their 20:06 ruling answered T1, and Q1 asks only about T2.)* **T1 `max` stands** — a new edge arrived, so `max` retains strength earned by an actual evidentiary event. **T2 `max` does not** — the survivor keeps its own confidence, unchanged. | resolved | research | — |
| ~~Q2~~ | **MOOT — 0.4.5 was tagged, released and published to PyPI on 2026-07-31, without an advisory.** The question was still marked *blocking / before release* a day later, which a canonical machine-readable status must never coexist with. **Acceptance of this spec is retrospective documentation, not authorisation for already-landed code.** External review item 10. | resolved | — | — |
| Q3 | Does the paper-2 conflict in §8 need a stated policy, or is per-case judgement enough? | `pre-release` | research | before paper 2 runs |
| Q4 | Should `needs_confirmation` be per-author rather than a single boolean? Would dissolve M3 structurally. | `deferred` | dev | own design round |
| ~~Q5~~ | **MOVED to `specs/0003` with M7, and resolved there: (b) inherit.** The question only looked balanced under this spec's lens. `actor` remains open, tracked in 0003. | moved | research | — |

---

## 11. Finding ledger

**Generated from `specs/findings.py`.** Do not edit this section — edit the
records and run `render_status.py --write`. `--check` runs in CI.

**Five reviews were deferred for status prose contradicting other status prose
in the same document.** Most recently a WITHDRAWN header claim — *"M1–M5, all
closed"* — sat beside this table showing five unimplemented. Each was corrected by hand and the
next appeared. The v5 phrase lint passed through that one, because a lint is a
better hand-check rather than a different mechanism. **So the summaries are now
derived and nothing below is restated by hand.**

<!-- GENERATED:summary -->
**18 findings · 6 shipped (0.4.4, 0.4.5, 0.4.6, 0.4.7) · 9 unimplemented · 7 still open · **2 fixed but unreleased**.**

**Unimplemented:** `M3`, `M4`, `N9b-lineage`, `N4-decay`, `N9t-transfer`, `M7-correct`, `M8-wiki`, `M6-import`, `X-crash`. **Open:** `N9b-lineage`, `N4-decay`, `N9t-transfer`, `M7-correct`, `M8-wiki`, `M6-import`, `X-crash`.

*Two of the unimplemented — `M3` and `M4` — shipped in 0.4.5 as fixes that do not hold.*
<!-- /GENERATED:summary -->

<!-- GENERATED:ledger -->
| finding | released behaviour | current defect | owner | implemented? | test |
|---|---|---|---|---|---|
| **M1** consolidation derived provenance from `cold[0]` | provenance inherited from the first cold episode | — | this spec | **yes** — 0.4.4 + GHSA-hcj3-8jqc-wqrp | `test_consolidation_preserves_and_compresses` |
| **M2** `confirm()` mutated `valid_from` | confirmation moved a fact's first-known date | — | this spec | **yes** — 0.4.5 | `test_confirm_advances_liveness_not_first_known` |
| **M2′** `confirm()` returned a `valid_from` it never set; future dates accepted | the return contract carried the caller's date; a future date was unrecoverable | — | this spec | **yes** — 0.4.6 | `test_confirm_returns_the_real_valid_from_not_the_confirmation_date` |
| **M2″** offset-bearing dates relabelled UTC instead of converted | `.replace(tzinfo=utc)` discarded the offset — 12h of skew bypass measured | — | this spec | **yes** — 0.4.7 | `test_an_offset_bearing_timestamp_is_converted_not_relabelled` |
| **M2‴** malformed dates silently became *now* | an invented observation time the caller never supplied | — | this spec | **yes** — 0.4.7 | `test_a_malformed_event_date_is_rejected_not_silently_now` |
| **M3** staleness cleared on same-author-class evidence | 0.4.5 closed cross-class clearing and left same-class open | the host chooses the class, and `author` is model-reachable | **`specs/0008`** | **no** | `0008 C1–C6` |
| **M4** `record_outcome` overwrites authorship | 0.4.5 appends a note to a summary rebuilt on every upgrade | the trail survives exactly one hop; the field is still overwritten | **`specs/0009`** | **no** | `0009 H1–H7` |
| **M5** merge-time `confidence = max(...)` | T1 retains `max`, which is earned | — | this spec | n/a | `constrains the unwritten T2 design` |
| **N9b-floor** consolidation manufactured confidence, disclosure and currency | `confidence = 0.9` flat; disclosure inherited from `cold[0]` | — | this spec | **yes** — 0.4.7 | `test_consolidation_output_is_no_stronger_than_its_weakest_input` |
| **N9b-lineage** consolidation retains no record of the absorbed set | inputs deleted, no lineage | 🔴 mixed-currency spread unretained, so N9b's premise and N10 are unmet | **`specs/0010`** | **no** | `0010 X6, X8` |
| **N4-decay** `MemoryConfig` bounds are unvalidated, and declared field bounds are not enforced on assignment | `decay_factor=2.0`, `NaN`, `-1.0` all accepted; `validate_assignment` is False | 🔴 `expire()` can RAISE confidence, which makes N4 false as written | this spec | **no** | `0002 N4b–N4d` |
| **N9t-transfer** `transfer` may raise trust and claim new currency | `import_memory` persists every claimed trust field verbatim | 🔴 no importing-principal cap and no currency restriction; N9t is frozen design only | **`specs/0005`** | **no** | `test_transfer_cannot_raise_trust_or_currency` |
| **N9b-provenance** consolidation inherits `source_type` and `evidence_ref` from `cold[0]` | a SYSTEM summary reports `source_type=stated` and the first input's `evidence_ref` | internally false provenance — M1's `cold[0]` inheritance surviving on two unexamined fields | this spec | **code yes, unreleased (c83b31b)** — users do not have it | `test_consolidated_provenance_is_internally_consistent` |
| **M2⁗** offset timestamps fail through `remember()` | `prompts.date_context` parses the raw string and rejects offsets | one input, two parsers — `_event_dt` is not the single contract §7f claims | this spec | **code yes, unreleased (c83b31b)** — users do not have it | `test_an_offset_timestamp_survives_every_public_entry_point` |
| **M7-correct** `correct()` bypasses the supersession ladder | `correct()` writes a replacement with hardcoded `author=USER` | 🔴 it is the only `supersedes=` writer and never calls `apply_supersession` | **`specs/0003`** | **no** | `0003 I9, I10` |
| **M8-wiki** the wiki serves a revoked trust decision | a cached wiki outlives the revocation of its inputs | 🔴 no wiki drop on a trust-reducing invalidation | **`specs/0004`** | **no** | `0004 W1–W4` |
| **M6-import** `import_memory` has no trust boundary | `--user` remap re-homes another principal's records verbatim | 🔴 no cap; and the cap as designed keys on an attacker-controlled header | **`specs/0005`** | **no** | `0005 P1–P6` |
| **X-crash** consolidation deletes every input before writing any output | delete-all-then-write; a crash loses the batch | 🔴 no fenced operation, no atomic claim, no read-visibility rule | **`specs/0010`** | **no** | `0010 X1–X9` |
<!-- /GENERATED:ledger -->

**`disposition` and `implementation` are separate columns on purpose.** The
second review's first finding was that *"closed"* silently meant *a disposition
exists* in one place and *the code is fixed* in another.

---

---

## 11a. Dependency index

**Generated.** The fifth review confirmed the split into separate specs was
structurally right, and identified the real cost: **a reviewer of any one spec
now sees less of the whole than a reviewer of v1 did.** The remedy is not to
recombine the normative designs but to publish the map — from the same records
as §11, so it cannot become another independently-maintained summary.

<!-- GENERATED:index -->
| finding | owner spec | disposition | implementation | test |
|---|---|---|---|---|
| `M1` | `0002` | resolved | shipped 0.4.4 | `test_consolidation_preserves_and_compresses` |
| `M2` | `0002` | resolved | shipped 0.4.5 | `test_confirm_advances_liveness_not_first_known` |
| `M2′` | `0002` | resolved | shipped 0.4.6 | `test_confirm_returns_the_real_valid_from_not_the_confirmation_date` |
| `M2″` | `0002` | resolved | shipped 0.4.7 | `test_an_offset_bearing_timestamp_is_converted_not_relabelled` |
| `M2‴` | `0002` | resolved | shipped 0.4.7 | `test_a_malformed_event_date_is_rejected_not_silently_now` |
| `M3` | `0008` | resolved | **not implemented** | `0008 C1–C6` |
| `M4` | `0009` | resolved | **not implemented** | `0009 H1–H7` |
| `M5` | `0002` | resolved | n/a | `constrains the unwritten T2 design` |
| `N9b-floor` | `0002` | resolved | shipped 0.4.7 | `test_consolidation_output_is_no_stronger_than_its_weakest_input` |
| `N9b-lineage` | `0010` | open | **not implemented** | `0010 X6, X8` |
| `N4-decay` | `0002` | open | **not implemented** | `0002 N4b–N4d` |
| `N9t-transfer` | `0005` | open | **not implemented** | `test_transfer_cannot_raise_trust_or_currency` |
| `N9b-provenance` | `0002` | resolved | **committed, unreleased** | `test_consolidated_provenance_is_internally_consistent` |
| `M2⁗` | `0002` | resolved | **committed, unreleased** | `test_an_offset_timestamp_survives_every_public_entry_point` |
| `M7-correct` | `0003` | open | **not implemented** | `0003 I9, I10` |
| `M8-wiki` | `0004` | open | **not implemented** | `0004 W1–W4` |
| `M6-import` | `0005` | open | **not implemented** | `0005 P1–P6` |
| `X-crash` | `0010` | open | **not implemented** | `0010 X1–X9` |
<!-- /GENERATED:index -->

---

## 12. Review history

<!-- GENERATED:reviews -->
**5 external reviews, 45 findings: v1 (9) · v2 (10) · v3 (7) · v4 (8) · v5 (11).** The invariant was approved in every one; the retrospective was deferred in every one.
<!-- /GENERATED:reviews -->

Full dispositions live in `~/Documents/veracium/proposals/` — **not here**,
because two full appendices inside the spec were themselves finding #1 of the
third review.

| round | verdict | findings | what recurred |
|---|---|---|---|
| **v1** | deferred | 9 | — |
| **v2** | deferred | 10 | **appended corrections instead of replacing the text they correct** |
| **v3** | deferred | 7 + package issues | **the same thing again — and this time the header asserted it had been fixed** |

**The recurring failure, stated once, plainly.** Twice I corrected a rule by
writing the correction *next to* the old rule rather than deleting it — with a
⚠️ marker, on the reasoning that visible corrections beat silent revision. **That
reasoning is right for a changelog and wrong for a normative section.** A
contributor greps `needs_confirmation` and finds two rules; the marker does not
help, because both hits look authoritative. **History belongs in one place. The
rule belongs where the rule is.**

**Third review, verified against the code — every item stands, and three are
defects in the manifest machinery I built to prevent exactly this:**

| # | finding | verified |
|---|---|---|
| 1 | stale rules, old ledger and both appendices still present | **yes** — old ledger `:802`, behaviour row `:313`, §§12–13 |
| 2 | header/§8 contradict the authoritative ledger | **yes** |
| 3 | `--check` validates the verdict and **never the test**, while its error text claims both | **yes — demonstrated.** Blanked a test, regenerated, `--check` passed |
| 4 | ordinal identity silently reattaches verdicts on reorder | **yes — demonstrated.** Reordered two `add_edge` calls: identical key set, different operations. **The only thing that flagged it was line numbers, which I documented as *not* part of identity** |
| 4b | the no-argument display path crashes | **yes** — unpacks a 5-tuple into 4 names; I only ever ran `--write` and `--check` |
| 5 | "evidence-free is derived from the manifest" is overstated | **yes** — the column is hand-authored. **A claim-versus-artifact gap inside the artifact built to close claim-versus-artifact gaps** |
| 6 | N9 omits `disclosure`; N9b omits most trust fields | **yes** |
| 7 | malformed dates still silently become *now* | **yes — and this is live in released 0.4.6.** §7f says it is "not this fix's business"; the reviewer is right that it is the same principle — **a malformed statement about when an event happened is not evidence that it happened now** |

### Tooling rebuilt — and it found the coverage claim was substantially unbacked

**Items 3, 4 and 4b are fixed** (`audit_manifest.py`, rebuilt on the AST).

| was | now |
|---|---|
| line-oriented regex; no `async def`, no class scope, first match per line | **`ast.parse`**, full scope qualification, every call node |
| identity = **ordinal** — reordering silently reattached verdicts | identity = **fingerprint** of the call's normalised expression + enclosing branch **and its condition**. Verified: **moving** a call keeps its verdict; **changing what it does** produces an explicit *no disposition* / *no longer exists* pair |
| `--check` validated the verdict, never the test | validates **5 fields, operation class, evidence value, trust fields, verdict, and test-or-owning-spec** — clean rows must name a **concrete test**, moved/open rows an **owning spec** |
| no-argument path crashed | fixed; the store-implementation exclusion is now **reported**, not silent |

**Then it found something worse than any of them.** With test-existence checked
for the first time, **11 of the 17 sites certified *clean* named tests that do
not exist.** I had written plausible test names rather than looking up real
ones. **The "17 clean" figure in the v3 package was therefore not backed by 11 of
its 17 rows** — the reviewer suspected the guarantee was not established and
could not see how far.

All 11 now point at tests verified present in the tree, and **a clean row citing
a non-existent test is a hard failure**.

**What this still does not establish**, stated because the last three drafts
overstated it: direct calls only — **aliased or indirect invocation is
invisible** — and the `evidence-bearing?` column remains a **reviewed
classification**, not a derived fact (§6a).

### Fourth review — disposition

**All eight stand. Three are live code defects; one means the v4 package
contradicted itself.**

| # | finding | verified |
|---|---|---|
| 1 | stale rules survive a pass that claimed to delete them | **yes** — §3's **M3 and M4 sections still state the rejected rules under bare `**Fix:**` headings** (`:231`, `:242`), the malformed fallback is still normative in §2c and §7f, the status row still says v3, and §8 still says *17 clean · 4 open · 7 moved* |
| 2 | manifest counts are arithmetically wrong | **yes — and the package shipped both numbers.** `render()` derives state by searching **rendered rows** for emoji, so a row is counted twice when its verdict says `🔴` and its test column says `➡️`. **28 − 4 − 10 = 14** double-subtracts 3 rows; the true unaffected count is **17**. The manifest headline said 14, the cover note said 17, **and I did not notice** |
| 3 | the fingerprint is not a unique identity | **yes** — two syntactically identical calls in one branch produce **one key**, and `_validate` converts to a `set`, so **one disposition satisfies both**. No collision check exists |
| 4 | independent verification still impossible | **yes** — the package carried 3 of the 7 modules the manifest cites, and neither `store/base.py` (the mutator source) nor the tests. **And the test-existence check is a substring match**: `def test_foo` is satisfied by `def test_foobar` |
| 5 | N9 omits `active`; import classification contradicts itself | **yes** — an evidence-free op could reactivate a retired edge with every other clause holding. And `import_memory` is **`evidence-bearing = no`** in the manifest while §6a says **`evidence-free = no`** — opposite answers to one question, readable only by noticing both columns are negatively phrased |
| 6 | N9b is unimplemented and unrepresented | **yes** — `consolidate()` copies `cold[0]`'s provenance and sets **`confidence = 0.9`**, computing neither minimum. A batch containing `0.2` yields a summary at `0.9`, **directly violating the invariant added in v4**. The ledger has no row saying so |
| 7 | `_event_dt` mishandles offsets | **yes — live in released 0.4.6.** `.replace(tzinfo=utc)` **discards** an existing offset instead of converting. Measured: a `-12:00` timestamp **bypasses the future-skew limit by 12 hours** |
| 8 | `0010`'s protocol is not implementation-ready | **yes** — no input→summary mapping for multiple outputs, no atomic claim, and recovery cannot distinguish a crash from a live writer mid-LLM-call |

**The root cause of #1, stated precisely because "I swept for it" was v4's claim:**
I swept for **`previously read`-style annotations and the obsolete ledger** —
the shape of my *own correction pattern* — and never for **every place a rule is
stated.** §3's `**Fix:**` lines were never annotated, so the sweep could not see
them. **A search for one's own edits is not a search for the rule.**

### Seventh review — disposition

**All eight stand. Two are the mechanism failing on its own terms.**

**Finding 3 is a real logic error, not a documentation gap.** N9 governs
evidence class `none`, which includes `expire()`, and its relation requires
`post.invalidation_reason == pre.invalidation_reason`. **A first-time retirement
moves that field from `None` to `"lapsed"`** — so the relation forbids the
operation §3 lists as clean. Equality is right for an **already-retired** edge
and wrong for **the transition that retires it**; the rule needs to be
transition-aware.

| # | finding | verified |
|---|---|---|
| 1 | the generated status system has already drifted | **yes** — the header says **v7** (`:7`) and the version row says **v6** (`:30`); the generated summary says *"5 external reviews, 45 findings"* while this document contains **six** dispositions. **`REVIEWS` in `findings.py` still ends at v5**: I wrote the sixth review's prose and never added its record. **The generator covers what I remember to record**, which is the same failure one level up |
| 2 | the process gate contradicts the ledger | **yes** — only `accepted` authorises implementation, the status is not `accepted`, and two corrective fixes are **committed**. They are new implementations produced during review, not retrospective description |
| 3 | N9 forbids legitimate expiry | **yes** — above |
| 4 | N9b still omits `source_type` / `evidence_ref` | **yes** — fixed in code and recorded in the ledger, **absent from the field contract**. A later implementation could reintroduce the defect while satisfying the table |
| 5 | N9t is declared closed and open | **yes** — `:495` says *"N9t closes it now"*; the ledger says open and unimplemented |
| 6 | §8 still carries manual counts | **yes** — *"15 clean · 2 fixed · 4 open · 7 moved"* (`:825`), which **omits `open_moved`** — the state added to distinguish open defects owned elsewhere — and is wrong |
| 7 | §12 recreated the append pattern | **yes** — it says dispositions live elsewhere and then contains four of them |
| 8 | the invariant table is malformed | **yes** — rows at `:370–378`, prose, then `:390–395` **with no new header**; N9 and N9t are in the orphaned part |

**Not verifiable this round: the archive was not delivered.** The reviewer
received the Markdown alone, so pytest behaviour, the manifest generator, the
canonical identity output, the 28-site count and the unreleased fixes are
**unverified rather than rejected**. **The tarball exists and was tested**
(`proposals/0002-v7-review-package.tar.gz`); what reached the reviewer was one
file.

---

### Sixth review — disposition

**All findings stand. The reviewer ran the code this time** — 210 tests
collected, 36 targeted tests passed — which is why three of these are defects
rather than documentation gaps.

**Finding 1 is the one that matters, and it is the same class again.**
Generating the ledger fixed *the ledger*. **§3's trust-class matrix is also a
status table, and I never converted it:** it still says `expire()` DECAY is
*"✅ clean — narrows only"* (`:172`) while the generated ledger says `N4-decay`
is **open and permits confidence increases**, and §3 still says *"M1–M5, all
shipped or resolved"* (`:277`) while `N4-decay` is open and owned here.
**The generated regions are internally consistent and the document around them
is not.** A mechanism that covers the summaries I remembered to generate is a
better hand-check wearing a generator's clothes.

| # | finding | verified |
|---|---|---|
| 1 | status verdicts survive outside the generated regions | **yes** — §3 `:172`, `:277` |
| 2 | the pytest collection check **fails open** | **yes** — any nonzero return is read as *"pytest unavailable"*, so a real collection error silently degrades to an AST scan. **The reviewer's run took that path and my success message came from the fallback.** Their environment failed only because the recipe never set `PYTHONPATH` |
| 3 | N9t is "closed" but unimplemented and untracked | **yes** — `test_transfer_cannot_raise_trust_or_currency` does not exist, `import_memory` still persists claimed trust fields verbatim, and **N9t has no record in `findings.py`, so the generated ledger cannot show it is open** |
| 4 | N9b omits `source_type` and `evidence_ref` | **yes — measured.** A consolidated summary reports `author_of_evidence=system` **with `source_type=stated` and `evidence_ref=event-0`**. Internally false provenance, and **the original M1 `cold[0]` inheritance surviving on two fields the 0.4.7 test does not inspect** |
| 5 | the offset fix does not cover `remember()` | **yes — reproduced.** `remember(date="2026-01-01T12:00:00+05:30")` raises `Invalid isoformat string` from `prompts.date_context`, not from `_event_dt`. **One input still has two parsers** |
| 6 | the manifest does not publish the identity it claims | **yes** — the canonical section publishes the *context only*, not the call expression, so no digest can be recomputed. And `canon[fp] = ctx` collapses rows: `confirm()` and `record_outcome()` both hash to `5b46e2531803`. **The `# audit:` label the tool demands is invisible to an AST walker — a remediation that cannot work** |
| 7–10 | `0010` fencing primitives, state machine, read contract, mixed time | **accepted in full** |

**Three unimplemented invariants are presented as frozen and closed** — N9t,
N9b's provenance fields, and `0010`'s protocol. **The structured records only
know about findings I remembered to record**, which is the fifth review's
finding relocated one level up: the mechanism narrows the class and does not
close it.

**And finding 2 deserves naming plainly:** I wrote a fallback that announces
itself, and treated announcing as sufficient. **A check that degrades on error
and prints a note is fail-open.** The correct behaviour is to fall back only
when *importing pytest* fails, and to treat a collection error as fatal.

---

### Fifth review — disposition

**All findings stand. The two that matter most are about the fixes themselves.**

**The lint I added in v5 to end this cycle failed on its first live test.** It
passed while **`| Decision + date | … M1–M5, all closed |`** sat in the header
against a ledger saying M3 and M4 are unimplemented. The phrase list knows
*"all five findings … are closed"* and not the equivalent **"M1–M5, all
closed"**. Two further live contradictions in the same document: *"three rows
are red"* where the table has **four**, and *"three external reviews"* where
there had been four.

**That settles the design question rather than the instance.** A phrase list
catches recurrences of retractions **we remembered to record** — I said so in
the cover note and still treated it as the fix. **Status stated in prose cannot
be made correct by checking it harder.** §11 must be the generated view of
structured records (`finding_id · owner_spec · disposition · implementation ·
verification · release`), with the header, the manifest counts, the ledger
summary and the review count **all derived from it**. Adopted for v6.

| # | finding | verified |
|---|---|---|
| 1 | the lint already misses a live contradiction | **yes — reproduced.** Plus the open **decay** defect (`expire()` `add_edge`, N4 false, no passing test) is **absent from the ledger entirely** |
| 2 | states assigned contrary to their own definitions | **yes** — M3, M4 and consolidation are `open` while owned by `0008`/`0009`/`0010`; all three are **`open_moved`**. Correct tally: **15 clean · 2 fixed · 1 open · 7 moved · 3 open_moved**. Only decay is genuinely `open` and owned here |
| 3 | the fingerprint still reattaches on reorder | **yes — their collision reproduced.** `x == 119` and `x == 125` both hash to **`4bd2`** at four hex chars, so two different branches share a context and the `#n` suffix then follows **source order**. `except` type, `match` case and `async with` are unencoded |
| 4 | mutator discovery is a remembered verb list | **yes** — `0010`'s `claim_episode_batch` would be invisible. **The original failure, one level up:** the interface is scanned, mutation is still inferred from remembered prefixes |
| 5 | `transfer` is in neither regime | **yes** — no evidence authority *and* outside N9, constrained only by prose delegation to `0005`. `invalidation_reason` is also prose-only, absent from the formal relation |
| 6 | the release record contradicts itself | **yes** — §7f's heading says *"released 0.4.5 + 0.4.6"*, §7f says the tests pass *"(0.4.6)"*, and §11 calls 0.4.6 **"unreleased — committed only"**. **0.4.6 and 0.4.7 are both published.** No `M2″` row for the offset fix |
| 7 | test-name validation ≠ collection | **yes** — a nested function, one under `if False`, or a method on an uncollected class all satisfy it. The claim narrows to *a function of that name occurs syntactically in the tests tree* |
| 8–11 | `0010` fencing, atomicity, visibility, lineage | **accepted in full** — see below |

### `0010`: the lineage finding is the serious one

**A fence orders; it does not prove liveness** (8), *"one conditional update"*
does not give an all-or-nothing set claim without an explicit store primitive
(9), and hiding inputs at claim time creates a window where a read sees
**neither** inputs nor outputs (10) — so recovery timing is a real availability
question, not the non-issue v5 claimed.

**But (11) is the one that would have shipped a defect.** Per-summary lineage was
to be computed by the caller from output date ranges. **The model sees the whole
batch**, so any output may carry content derived from any input, and a date
partition understates provenance: **a third-party-influenced input can inform an
output whose lineage names only user inputs.** That **recreates the laundering
defect N9b exists to prevent**, inside the spec written to satisfy N9b. Fix:
pre-partition before generation, or every output inherits the whole claimed set
and its minimum trust.

### The package failure is mine

The cover asserted the complete `src/` and `tests/` trees were included. **They
were written to the package directory and never transmitted** — the reviewer
received the eight top-level files only, and could execute nothing that touches
source. **v4 was deferred partly for asserting reproducibility the package could
not support; v5 asserted it, built it correctly, and failed at delivery.**

### Answers received to §9's questions

- **`observed_at` monotonicity: keep it.** A legitimate maintenance-time liveness
  signal *would itself be a new observation*, so it belongs in `observation`,
  **not as an exception inside `none`.**
- **Categorical equality: keep it** for single-object evidence-free mutation. A
  lattice belongs in N9b, supersession and import capping — letting a persisted
  object's authorship move *down* during maintenance still rewrites provenance.
- **The split was correct.** The remedy for lost overview is **not** recombining
  the normative designs but a one-page dependency index — which is the same
  structured record §11 should be generated from.
