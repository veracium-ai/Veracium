# Feature spec: the maintenance provenance invariant

Spec-Status: deferred

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **deferred (v2)** — second external review 2026-08-01: **invariant approved; retrospective deferred again.** All ten items verified present and **all stand**. The diagnosis is right and is the thing to fix: **v2 appended corrections instead of replacing the text they correct**, so the document now describes two systems. **v3 is a rewrite, not another amendment** — see §13.

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
| **Version** | **v2** — *re-read before editing; quote the version you approve.* v1 was deferred at external review 2026-08-01; all nine amendments applied. |
| **Status** | *see `Spec-Status:` at the top — canonical.* **v2 — deferred at external review, amended, re-submission requested.** The nine required amendments are applied (§7a–§7e, N1/N4b/N8/N9/N10, §8, Q2) and the 28-site manifest now exists as a generated, CI-verified artifact. |
| **Internal reviewers** | research *(trust semantics; and paper 2 is on this exact subject — see §8)* |
| **External review** | required — full spec (touches `graph.py`, `lifecycle.py`, `__init__.py`) |
| **Decision + date** | — · **scope narrowed 2026-08-01** to M1–M5, all closed. M6/M7/M8 moved out; see §11. |
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
| **host-supplied `author`** (`mcp_server.py:26`, `cli.py:299`) | rejected by enum | rejected by enum | rejected by enum | **host may claim `system`, which shares `MENTIONABLE` with `user`** — this is M3's reachability | ➡️ **`specs/0008`.** ⚠️ This cell previously read *"clears only on same-author evidence or `confirm()`"* — **the rule R3 overturned**, still stated normatively here after v2 amended it elsewhere. **Now: no value of this field clears anything** |
| **host-supplied `actor`** (`record_outcome`) | defaults `user` | n/a | maps via `_OUTCOME_ACTORS` | **last writer's label silently wins** | **M4 fix: append, never overwrite** |
| **host-supplied `date`** (`confirm()`, `remember()`) | defaults today | `_event_dt` falls back to now | — | **future dates were accepted and unrecoverable; back-dating moved `valid_from`** | **§7f (0.4.5 + 0.4.6): `valid_from` immutable · `observed_at` monotonic · future beyond 1 day rejected at `_event_dt`** |
| **cold-episode set** (consolidation) | no-op below batch | — | — | **mixed authorship** | **M1 (0.4.4): provenance derived from the whole set** |
| **older-version store data** | — | pydantic rejects unknown enum | — | — | ⚠️ **no invariant — no `PRAGMA user_version`.** Carried from spec 0001 Q3; **this empty cell is a gate on that spec, not this one** |

---

## 3. Trust-class matrix — the audit

Every maintenance-time or trust-mutating operation, against the lens:
**does it re-derive provenance, disclosure, authorship or currency from anything
other than new evidence from a party entitled to supply it?**

| operation | verdict | detail |
|---|---|---|
| `lifecycle.expire()` — LAPSE | ✅ clean | invalidates only; ages against `observed_at`, which is the C′ liveness axis |
| `lifecycle.expire()` — DECAY | ✅ clean | `confidence *= decay_factor` **narrows only**; re-add via `add_edge` is a pure upsert with no timestamp mutation (verified) |
| `lifecycle.expire()` — CONFIRM | ✅ clean | sets `needs_confirmation = True`; narrowing |
| `lifecycle.consolidate()` | ✅ **fixed 0.4.4** | **M1** — derived provenance from `cold[0]`; now whole-set, min-trust |
| `compile.py` (wiki) | ✅ clean | filters `not e.use_only` **and** `not third_party_influenced`, explicitly mirroring `gate.partition`. **But see the architectural note below** |
| `proactive.assemble()` | ✅ clean | `if not e.assertable: continue` |
| **`confirm()`** | 🔴 **M2 — shipped defect** | mutates `valid_from` |
| **T1 reinforcement** | 🟠 **M3 — shipped defect** | clears `needs_confirmation` on cross-author evidence |
| **`record_outcome()` upgrade-in-place** | 🟠 **M4 — shipped defect** | overwrites `author_of_evidence`, no history |
| **T1 `confidence = max(...)`** | 🟢 **M5 — permitted** | a new edge arrived; `max` retains earned strength |
| **T2 `confidence = max(...)`** | 🔴 **M5 — forbidden by design constraint** | manufactures lifetime from recognition; survivor keeps its own |

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

**Fix:** `needs_confirmation` clears only on evidence from the **same author
class** as the flagged edge, or via `confirm()`.

### M4 — `record_outcome` overwrites authorship without history (shipped)

`__init__.py:554`: `prior.provenance.author_of_evidence = author` on
upgrade-in-place. The last writer's `actor` label silently wins and **the prior
authorship is unrecoverable** — in a system whose stated principle is
**supersession-never-erasure**. The host controls `actor` in both directions, so
this is not privilege escalation; it is provenance destruction.

**Fix:** append a new outcome episode rather than overwriting, or retain prior
authorship in a note. Erasure is the part that is wrong, not the update.

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

**What stays here:** M1–M5, all shipped or resolved, plus the 28-site
enumeration. That is a record of what happened, and it can be reviewed and
accepted as one.

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
> unchanged. **`valid_from = min` stays the sole exception**, because it
> *corrects* first-known rather than manufacturing anything, and the merge-event
> record keeps the absorbed edge's value recoverable.
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
| system-authored restatement of a stale user fact | staleness marker removed | marker retained; only user evidence or `confirm()` clears it |
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
| **N3** `needs_confirmation` clears only on same-author evidence or `confirm()` | `test_cross_author_cannot_clear_staleness` | CI |
| **N4** no maintenance operation raises `disclosure` toward assertable **or raises `confidence`** | `test_no_maintenance_op_widens_disclosure` · **`test_no_maintenance_op_raises_confidence`** — property-based over a random op sequence, **run under a hostile `MemoryConfig`** | CI |
| **N4b** `MemoryConfig` rejects a `decay_factor` outside `[0, 1]`, and `NaN`/`±inf` | `test_decay_factor_bounds_are_validated` — 0 · 1 · interior · >1 · negative · NaN · ±inf | CI |
| **N4c** a declared field bound is enforced **on assignment**, not only on construction | `test_confidence_bound_holds_under_in_place_mutation` — verified today that `validate_assignment` is `False` and `confidence *= 2.0` yields `1.8` | CI |
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
| **N5** `author_of_evidence` is never overwritten without retaining the prior value | `test_outcome_upgrade_retains_prior_authorship` | CI |
| **N6** consolidation provenance derives from the whole set (0.4.4) | existing `test_consolidation_provenance.py` | CI |
| **N7** a full `maintain()` cycle over simulated months never moves an edge from UNVERIFIED to GROUNDED | `test_maintenance_never_promotes_across_the_gate` — **the general form of both advisories** | CI + bench |
| **N9** *(replaces N7's general claim)* for an **evidence-free** operation the post-state is no stronger than the pre-state under a defined partial order over `assertable` · `needs_confirmation` · `confidence` · `observed_at` · `author_of_evidence` · `derived_from` · `valid_from` | `test_evidence_free_maintenance_is_monotone` — property-based over random op sequences | CI |
| **N10** history preservation is checked **separately** from trust rank | `test_maintenance_preserves_authorship_history` | CI |

**N7 is the one that matters.** It is stated over the *observable boundary*
rather than over any field, so it catches the next instance of this class even if
the mechanism is one nobody has thought of. Both advisories would have failed it.

---

## 7. Failure modes and reversibility

- **Silent failure:** all four defects are silent by construction — they change
  provenance, and provenance is only visible through `introspect()` or a
  rendered marker most users never diff. M2's symptom is a wrong date in an
  answer; M3's is a *missing* caveat, which is invisible.
- **Reversibility:** the fixes are reversible. **The damage is not** — M2 has
  already destroyed original `valid_from` values in any store where a stale fact
  was confirmed, and consolidation has already destroyed member episodes.
- **Partial failure:** ⚠️ **this previously read *"a crash leaves a partially-
  maintained store, which is safe because every operation narrows."* That is
  false and is withdrawn.** `expire()` is per-edge and idempotent, so it does
  hold there. **`consolidate()` is neither**: it deletes every member episode
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
> is earlier than the survivor's produces a **new merged edge** (or merge record)
> whose `valid_from` is the `min` of its inputs, with the originals retained and
> recoverable.

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

**Frozen persistence contract:**

> - consolidation commits **atomically**, or runs as a recoverable state machine;
> - **originals are not deleted until the replacement and its provenance lineage
>   are durable**;
> - retry is **idempotent**;
> - partial state is detected and repaired before ordinary reads depend on it.

**§7 must stop claiming crash-safety follows from narrowing.** It does not
follow, and this is the operation that proves it.

---

## 7f. M2 — frozen: the confirmation-time contract (released 0.4.5 + 0.4.6)

**Second external review item 2:** 0.4.6's behaviour was asserted in the header
and the changelog and **specified nowhere**, while N2 still said only that
`confirm()` *"advances `observed_at`"* — which constrains neither the response
nor a hostile date. **A released fix that is not pinned is not closed.**

> **Event dates.** Any host-supplied `date` more than `MAX_FUTURE_SKEW`
> (**1 day**) beyond now is **rejected** — `ValueError`, not clamped. Applied in
> `_event_dt`, the single point every event date passes through, so
> `remember` · `confirm` · `correct` · `record_outcome` are covered by one rule.
> Malformed dates keep their pre-existing fallback to now.
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

**All six pass today** (0.4.6, `533092c`); N2b is the one whose behaviour
predates the fix and was never pinned.

---

## 8. Claims and limits

- **What we will say:** *"0.4.5 fixes three provenance defects identified during
  a mechanically derived audit of the store-mutation sites scoped to spec 0002.
  Import, supersession and derived-view findings are governed by specs 0005,
  0003 and 0004."*

  **⚠️ The previous wording was *"an audit of every maintenance-time
  operation"*, and §1 had already withdrawn exactly that claim.** It survived
  into the release language and out the door. External review item 6 caught it.
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
    not asserted. **17 clean · 4 open · 7 moved.**
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

- **What we are least sure of.** (1) Whether **N7 is actually the general
  form**, or merely the general form of the two instances we happen to have seen
  — the honest answer is that we cannot tell from two. (2) Whether "same author
  class" is the right axis for M3, given that the axis error is exactly what
  deferred spec 0001. (3) Whether `expire()`'s confidence decay is genuinely
  narrowing in all cases, or only in the ones we constructed.
- **Where we suspect we have overstated.** §1's claim that three rules with the
  same shape reveal "the architecture's actual invariant" is a satisfying
  sentence and may be pattern-matching on three data points.
- **What would change our minds.** A maintenance operation that legitimately
  needs to widen trust. We could not construct one, which is either evidence for
  the invariant or a failure of imagination.

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

**Rebuilt to the second external review's shape.** The previous table said
*"all five findings that remain here are closed"* while the header said three
were unimplemented. **Both were written by me and "closed" silently meant two
different things** — *a disposition exists* in one place, *the code is fixed* in
the other. The columns now force the distinction.

| finding | released behaviour | current defect | frozen behaviour | implemented? | test | release |
|---|---|---|---|---|---|---|
| **M1** consolidation derived provenance from `cold[0]` | whole-set minimum trust | — | — | **yes** | `test_consolidation_uses_whole_set_min_trust` | 0.4.4 + GHSA-hcj3-8jqc-wqrp |
| **M2** `confirm()` mutated `valid_from` | `valid_from` immutable; confirmation advances `observed_at` | — | §7f | **yes** | `test_confirm_advances_liveness_not_first_known` | 0.4.5 |
| **M2′** return value / future dates | returns real `valid_from` + `confirmed_at`; future dates rejected at `_event_dt` | — | §7f | **yes** | `test_confirm_returns_the_real_valid_from…` · `test_a_future_event_date_is_rejected` | **0.4.6 (unreleased — committed only)** |
| **M3** staleness clearing | same-**class** clearing still permitted | 🔴 **the shipped fix is inadequate** — the host chooses the class | ➡️ **`0008`** | **no** | `0008` C1–C6 | — |
| **M4** outcome authorship | note in `summary`, structured field still overwritten | 🔴 **the shipped fix is inadequate** — the note survives one hop | ➡️ **`0009`** | **no** | `0009` H1–H7 | — |
| **M5** merge-time `confidence` | T1 `max` retained | — | T2 keeps the survivor's own | **n/a — T2 is unwritten** | constrains `0009`-era T2 design | — |
| **crash-safe consolidation** | delete-all-then-write | 🔴 open | §7e (contract only; **strategy deliberately open**) | **no** | `test_consolidation_is_crash_safe` | — |

**Three rows are red and two of them shipped as fixes.** That is the honest
state, and it is why `0008` and `0009` exist separately: **they are corrections
to released behaviour, not documentation debt.**

---|---|---|
| **M1** | consolidation derived provenance from `cold[0]` | ✅ **shipped 0.4.4** + advisory GHSA-hcj3-8jqc-wqrp |
| **M2** | `confirm()` mutated `valid_from` | ✅ **shipped 0.4.5** |
| **M3** | cross-author clearing of `needs_confirmation` | ✅ **shipped 0.4.5** |
| **M4** | `record_outcome` overwrote authorship | ✅ **shipped 0.4.5** |
| **M5** | merge-time `confidence = max(...)` | 🟢 **RESOLVED 2026-08-01 — no code change needed today.** T1 keeps `max`; T2 keeps the survivor's own confidence. T2 is unwritten, so this is now a **constraint on the T2 design** rather than a fix. Note what the resolution corrects in *my* framing: I offered a blast-radius measurement (one consumer, no ranking effect) as the argument, and research's ruling names that as answering **"how bad is it"** when the question was **"is it justified."** Severity bounds the cost of being wrong; it says nothing about legitimacy. |
| **M6** | `import_memory` has no trust boundary | ➡️ **MOVED — `specs/0005-import-trust-boundary.md`.** Fix designed there; **a new blocking question surfaced in the move** (`I-Q1`: the cap keys on an attacker-controlled header field). The docs recipe stays held against *that* spec now. |
| **M7** | `correct()` elevates non-assertable facts | ➡️ **MOVED — `specs/0003-supersession-authority.md` §1b**, where it belongs: `correct()` is a supersession path. **The move resolved it** — `0002` Q5 dissolves into the ladder, (b) inherit. It also exposed that `apply_supersession` and `correct()` are disjoint, so 0003 gained I9. |
| **M8** | wiki serves a revoked trust decision | ➡️ **MOVED — `specs/0004-derived-views-and-revocation.md`.** Fix designed there, plus the strike of an unreachable *"any quarantine"* clause. `compile.py` stays **guarded** (`8ad5167`). |

**All five findings that remain here are closed.** M1–M4 shipped; M5 is ruled
and constrains a design that does not exist yet. **This document is now what it
always was — the 0.4.4 retrospective plus the 28-site audit — and it is
reviewable as one thing.**

**External review: REQUESTABLE as of 2026-08-01.** The old note said it should
wait until M5–M8 carried proposed resolutions, and that was right while they
lived here. **The split, not the resolutions, is what unblocked it.** Accepting
this spec also retroactively documents 0.4.5's basis, which is the honest fix
for M2/M3/M4 having shipped citing a `draft` — see the gate finding (`3ef6519`).

---

---

## 12. External review, 2026-08-01 — disposition

**Verdict: invariant accepted in principle; retrospective deferred for major
amendment.** The reviewer states the rule better than the spec did:

> **Maintenance without new evidence may narrow trust, but must not manufacture
> authority, confidence, currency, or provenance.**

**Every falsifiable item was checked against the running code before disposition.
Nine stand as written, one is refined, and four are worse than claimed.**

| # | item | verified | disposition |
|---|---|---|---|
| 1 | `valid_from` immutable vs `min` | **refined** | See below — the *shipped* code is consistent; **N1's wording and the T2 design are not.** Still blocking. |
| 2 | adversarial confirmation dates | **partly already fixed, and worse** | `observed_at = max(...)` **already shipped**, so back-dating is handled. **Future-dating is not — and `max` makes it permanent.** |
| 3 | same author class ≠ authority | **stands** | `graph.py:119` compares `author_of_evidence` equality and nothing else. Accept the fail-closed rule. |
| 4 | N7 is not the general invariant | **stands** | Overclaim. N7 tests one UNVERIFIED→GROUNDED transition; M2/M3/M4 need not cross it. |
| 5 | the 28-site manifest is absent | **stands** | §3 has **11 operation rows**, not 28 call sites. The claim that clean sites are listed is false. |
| 6 | §8 reintroduces the withdrawn claim | **stands** | §8 still reads *"an audit of every maintenance-time operation"* and *"nine mutation sites"*. Both were withdrawn in §1. |
| 7 | M4 has no frozen behaviour | **stands, and worse** | The weaker option **already shipped**, and it survives exactly one upgrade. Demonstrated below. |
| 8 | decay needs bounds | **stands, and worse** | `MemoryConfig` is an unvalidated `@dataclass`. `decay_factor=2.0`, `NaN`, `-1.0` all accepted — **which makes N4 false**. |
| 9 | crash safety overclaimed | **stands, and worse** | Not a hypothetical: `lifecycle.py:122` deletes **all** cold episodes *before* writing any replacement. |
| 10 | status vs Q2 | **stands** | 0.4.5 was tagged, released and published to PyPI on 2026-07-31. Q2 asks a pre-release question about it. |

### On item 1 — the reviewer's conclusion is right; the premise needs one correction

*"Those cannot all be true"* — in the **shipped** code they can, narrowly.
Absorption mutates `edge.valid_from` at `graph.py:128`, but `store.add_edge(edge)`
is at `graph.py:143`: the edge **is not yet persisted**. Under *creation =
persistence* N1 holds, which is why its test passes.

**That defence is worth exactly nothing going forward, and the item stays
blocking**, because (a) N1's wording says *"after creation by any operation"* and
does not state that reading, and (b) **T2's design applies `valid_from = min` to
an existing survivor**, which breaks it for real. A contract that survives only
under an unstated reading of one word is not a contract. **Recommend the
reviewer's first option — immutable edge identity** — since it is what the code
already does at the only place it currently matters.

### Two defects verification found that the review did not reach

**(a) `confirm()` returns a `valid_from` it did not set.** M2 removed the false
date from the model's context and **left it in the API return value**:

```
>>> m.confirm("u", "e-1", date="2026-03-15")
{'confirmed': 'e-1', 'valid_from': '2026-03-15'}
>>> edge.valid_from
2026-01-01
```

**This is M2's own defect, in a different surface.** The spec says the fix is
shipped. It is shipped in `render_edges` and not in the return contract a host UI
reads.

**(b) A future-dated confirmation is irreversible.** `_event_dt` performs no
skew check, and the `max()` that correctly defeats back-dating is what makes
future-dating permanent:

```
confirm(date="2099-01-01")  → observed_at = 2099-01-01
confirm(date="2026-08-01")  → observed_at = 2099-01-01   # max() locks it in
```

The edge cannot lapse, decay, or be flagged stale for 73 years. **One
host-supplied date permanently removes an edge from the entire lifecycle.**
This strengthens the reviewer's item 2 from *"can keep an edge artificially
fresh"* to **unrecoverable without direct store surgery**.

### Demonstration for item 7 — the M4 note survives one hop

`record_outcome` rebuilds `summary` on every upgrade, so the appended note is
overwritten rather than accumulated:

```
initial (system)      author=system  (system) unreviewed: use of 'works_as: CFO'
after challenged      author=system  (system) challenged: ...
after corrected(user) author=user    (user) corrected: ... [prior judgment was system-authored]
after 2nd challenged  author=system  (system) challenged: ... [prior judgment was user-authored]
```

**The `system → user → system` history is reduced to "prior was user."** M4
shipped as a fix for authorship erasure and **still erases authorship**, one step
later, while also still overwriting the structured field. The reviewer's *"a note
is not structured provenance"* is right; the sharper statement is that this note
is **destroyed by construction on the next upgrade**.

### Item 9 is the shipped order, not a race

```python
for e in cold:  store.delete_episode(e.id)     # lifecycle.py:122
for r in new:   store.add_episode(...)         # lifecycle.py:124
```

Delete-all-then-write. A crash between the loops loses the cold episodes **with
no replacement at all** — total loss, not the partial states the review lists.
*"A partial `maintain` is safe because every operation narrows"* is false in the
worst available direction.

### What this does not change

The invariant, M1's whole-set minimum-trust rule, the M5 ruling, and the split
of M6/M7/M8 are all accepted by the reviewer and stand. **The failure is not the
architecture. It is that a retrospective made coverage and closure claims its
artifacts do not support** — the same claim-versus-artifact gap as the `_cover`
docstring, the `valid_from` changelog, and the r2 headline. **Fourth instance,
and the first where an outside reader found it before we did.**

---

## 13. Second external review, 2026-08-01 — disposition

**Verdict: architectural invariant approved; retrospective deferred for a
focused v3.** Every item was checked against the document. **All ten stand.**

**The central finding, and it is correct:** v2 **appended** §7a–§7e and §12
rather than **replacing** the v1 text they overturn, so §2c, §3's M-sections, N2,
N3, N7 and the finding ledger still specify the withdrawn rules. **A contributor
reading the normative sections gets the old system.**

**I wrote the rule and broke it in the same commit.** `fbf4396` added *"A
retraction that is not applied by `grep` is not applied"* to §8 **and** the
appended §7a sections. One `git show` shows both. That is the fourth
claim-versus-artifact gap recurring one level up: I described the correct method
and did not execute it.

| # | item | verified | disposition |
|---|---|---|---|
| 1 | ledger contradicts implementation status | **stands** | §11 says *"all five findings that remain here are closed"* while the header says three are unimplemented. **"Closed" was true of the *disposition* and false of the *code*, and the table does not distinguish them.** Adopt the reviewer's seven-column ledger. |
| 2 | no normative M2 contract for 0.4.6 | **stands** | N2 still reads only *"`confirm()` advances `observed_at`"*. **The 0.4.6 behaviour is in the changelog and in §12 and nowhere normative.** A released fix asserted but not pinned. |
| 3 | M3 may still trust an adversarial label | **stands — and on this document's own terms** | §2c lists **host-supplied `author`** as an uncontrolled input whose adversarial case is *"host may claim `system`"*. §7b then lets *"a new user-authored observation"* clear staleness. **The only evidence of "user-authored" is the field §2c says the host may lie about.** Circular. Research and I both signed this off. **Blocking — posted as R3.** |
| 4 | N9 names a partial order it never defines | **stands** | I wrote a **field list**, not a relation, and a property test cannot implement one. The reviewer supplies the product rule; adopt it, including `post.observed_at <= pre.observed_at` and the categorical fields as **equality**. Consolidation is set→object and needs its own rule. |
| 5 | N7's withdrawn claim is still normative | **stands** | The table still calls it *"the general form of both advisories"* and §6 still says *"N7 is the one that matters"*; §9's reviewer brief still asks the question v2 answered. |
| 6 | M4 chain needs head/concurrency semantics | **stands** | §7a fixes the shape and not the ordering. **A host-supplied timestamp must not decide authority** — use a store-assigned monotonic sequence with an atomic head transition. |
| 7 | §7c still offers an alternative | **stands** | *"new merged edge (or merge record)"* — not equivalent. Freeze the new-edge construction, and **delete the surviving M5 sentence** (§ line 282) that still calls `min` "the sole exception". |
| 8 | decay tests under-cover the frozen rule | **stands** | N4b names only `decay_factor`; N4c only `confidence`. §7d froze more than that. Needs `confidence_floor`, boundary-accept regressions, and assignment coverage of **every** bounded mutable trust field. |
| 9 | the manifest was not in the review package | **stands — my process failure** | I built the artifact, cited its counts, and **did not send it**, so the one item that exists to make coverage independently checkable was the one item the reviewer could not check. Ship `specs/generated/0002-audit-manifest.md` + `audit_manifest.py` + `audit_dispositions.py` with v3. |
| 10 | crash-safe strategy left open | **stands, and may stay open** | Two strategies is acceptable for a retrospective. **It is not acceptable alongside "all findings closed"** — which is item 1 again, and the reason item 1 is the root. |

### What v3 must not do

**Not grow a third review appendix.** §12 and §13 are themselves the append
pattern, one level up. **v3 folds both into the normative sections and keeps a
short changelog of what moved** — otherwise the next reviewer reads a document
whose corrections outweigh its content.

### One thing to carry to `0006`

**Item 3 is not confined to this spec.** `0006` relaxes M3's rule on
`source_id`, which is **also host-supplied**. Research's constraint was *never
model-supplied*; the reviewer's point is that **host-supplied is not sufficient
when the rule's entire job is to establish authenticity.** If R3 lands on *"the
call path must establish it"*, `0006`'s §3 matrix inherits that requirement.
