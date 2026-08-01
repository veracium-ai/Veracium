# Feature spec: the maintenance provenance invariant

Spec-Status: in review

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

> **in review** — internally reviewed twice by research; external review **held on M7 alone** (Q5, decided 2026-08-01). M5 resolved; **M6 and M8 carry specified fixes** (§11a, §11c); M7 needs an internal trust-semantics decision.

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
| **Version** | v1 |
| **Status** | *see `Spec-Status:` at the top — canonical.* Internally reviewed twice by research; external review **held on M7 alone** — M5 resolved, M6/M8 specified (§11a/§11c), **three fixes queued behind one decision (Q5)**. Header previously read *"internal review not yet requested"*, which was stale. |
| **Internal reviewers** | research *(trust semantics; and paper 2 is on this exact subject — see §8)* |
| **External review** | required — full spec (touches `graph.py`, `lifecycle.py`, `__init__.py`) |
| **Decision + date** | — · **3 of 8 findings already SHIPPED** in 0.4.5 (M2/M3/M4) and 0.4.4 (M1); M5–M8 open, see §11 |
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
| **host-supplied `author`** (`mcp_server.py:26`, `cli.py:299`) | rejected by enum | rejected by enum | rejected by enum | **host may claim `system`, which shares `MENTIONABLE` with `user`** — this is M3's reachability | **M3 fix: `needs_confirmation` clears only on same-author evidence or `confirm()`** |
| **host-supplied `actor`** (`record_outcome`) | defaults `user` | n/a | maps via `_OUTCOME_ACTORS` | **last writer's label silently wins** | **M4 fix: append, never overwrite** |
| **host-supplied `date`** (`confirm()`, `remember()`) | defaults today | `_event_dt` falls back to now | — | **a future or back-dated value moves `valid_from`** | **M2 fix: `valid_from` immutable; confirmation date goes to `observed_at`** |
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

### M6 — `import_memory` has no trust boundary (design gap, queued trigger)

**Found by research, verified here.** `portability.import_memory` does
`Edge.model_validate(rec)` then `store.add_edge(edge)`: **every trust-bearing
field reconstructed from a file** — `author_of_evidence`, `disclosure`,
`confidence`, `valid_from`, `derived_from` — with no re-derivation, no capping,
and a raw store write, so the ingest path's trust machinery never runs. Against
this spec's own lens it re-derives **all four**, from a file. Reproduced:

```
import_memory(bob_store, alices_export.jsonl, user_id="bob")
  → author=user  disclosure=mentionable  derived_from=None  assertable=True
```

**Alice's testimony is now Bob's own assertable fact.**

**In the restore case this is correct** — preserving provenance is the point.
Three things compound to make it otherwise: `user_id=` exists *to remap records
into a different user*, i.e. its purpose is crossing a principal boundary; a
docs recipe is already queued recommending exactly that ("seed a new project
from a team memory export"); and the demand it answers is for **shared/inherited
memory**, so the population most likely to follow it is the population importing
content they did not author.

**⚠️ Correction (research, verified here): this is NOT host-facing only. It is
a shipped CLI verb.** `cli.py:278` registers `import`, `cli.py:280` adds
`--user` (*"remap the records into this user id"*), `cli.py:149` passes it
through. **`veracium import alices_export.jsonl --user bob` is available to
anyone with the package installed.** Record it as **CLI-reachable,
operator-initiated** — the earlier phrasing is what gets re-checked if this is
ever revisited.

**And the mechanism is sharper than "fails to cap".** `author_of_evidence=USER`
is a claim **relative to the store owner**, and `--user` changes what it is
relative to. Nothing is falsified or mis-parsed: Alice's edge honestly says
*"authored by the user of this store"*, and re-homing it makes that sentence
mean Bob. **The re-attribution is a side effect of the remap, not a missing
check** — which is exactly why grepping provenance assignments could never have
found it, and why it reads as correct on inspection. It also relocates the fix:
**the cap belongs at the remap**, the only place the referent changes.

**The finding is not "import is broken."** It is that import has no trust
boundary, the API has a parameter whose purpose is to cross one, and a queued
doc would tell users to. **Ship the recipe before the boundary and third-party
content has a supported path to enter as first-party assertable fact — working
as designed, no bug, no advisory to write.**

**Rule (research's, adopted):** no `user_id=` (restore) → preserve provenance
unchanged. With `user_id=` (cross-principal) → third-party by construction: cap
to `use_only`, set `derived_from=THIRD_PARTY`, unless the caller explicitly
asserts otherwise. Costs nothing in restore, needs no new concept, makes the
convenient call the safe one. **⏳ Hold the cross-project-inheritance docs recipe
until this lands.**

### M7 — `correct()` elevates non-assertable facts, and `confirm()` refuses to

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

**Proposed fix, three lines:** refuse `correct()` on a non-assertable edge using
`confirm()`'s existing error text, and either honour `actor` or delete it.

### M8 — the wiki caches a trust decision and serves it after revocation

**Found by research, reproduced here.** §3 marks `compile.py` clean and the
architectural note covers *a correct filter defeated by upstream corruption of
its input*. **This is a third failure shape: the filter is correct, its input is
correct, and the OUTPUT is cached across subsequent trust changes.**

`compile.py:74` recompiles only after `wiki_recompile_after_writes` store
versions (**default 8**), and `__init__.py:225` appends the wiki to
**`grounded_parts`**. So a revocation takes effect on the edge immediately and
**not on the wiki**:

```
default wiki_recompile_after_writes = 8
wiki built: True
after dispute():
  edge active       : [False]
  'Acme' in GROUNDED: True      <-- disputed fact still asserted
```

**A user's explicit trust action is silently ineffective on the one surface that
matters — what the model reads.** Same for a late supersession, correction or
quarantine.

**Reachability, measured rather than inferred.** `cli.py:198` sets
`wiki_recompile_after_writes = 10**9 if has_wiki else 0`, so **once a wiki
exists the CLI never recompiles**. But `dispute` and `correct` are **not CLI
verbs** — `grep -n "add_parser" src/veracium/cli.py` lists telemetry ·
selfcheck · diagnostics · export · import · forget · recall · remember ·
introspect. **So the unbounded case is not "CLI user disputes and nothing
happens"; it is the mixed path: a host revokes through the API, an operator
later reads the same store with `veracium recall`, and that path never
recompiles — so the revoked fact stays in the grounded block indefinitely.**
Narrower than "the CLI is unbounded", and still real.

**Fix costs nothing and fails closed: a trust-reducing event DROPS the wiki
rather than recompiling it.** `invalidate_edge` with reason in
`{disputed, corrected, superseded}`, and any quarantine, empties the cache. No
LLM call, no latency; you lose curated breadth until the next natural recompile
and never assert revoked content.

**Finding for the spec, not an advisory** — attacker-free, and self-healing
within 8 writes on the library default. But it is **the same shape as both
advisories**: a derived artifact preserving a trust decision after the decision
changed.

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
| **N1** `valid_from` is never mutated after creation by *any* operation | `test_valid_from_immutable_across_every_mutation_site` — parametrised over confirm / reinforce / absorb / expire / consolidate | CI |
| **N2** `confirm()` advances `observed_at`, not `valid_from` | `test_confirm_advances_liveness_not_first_known` | CI |
| **N3** `needs_confirmation` clears only on same-author evidence or `confirm()` | `test_cross_author_cannot_clear_staleness` | CI |
| **N4** no operation raises `disclosure` toward assertable | `test_no_maintenance_op_widens_disclosure` — property-based over a random op sequence | CI |
| **N5** `author_of_evidence` is never overwritten without retaining the prior value | `test_outcome_upgrade_retains_prior_authorship` | CI |
| **N6** consolidation provenance derives from the whole set (0.4.4) | existing `test_consolidation_provenance.py` | CI |
| **N7** a full `maintain()` cycle over simulated months never moves an edge from UNVERIFIED to GROUNDED | `test_maintenance_never_promotes_across_the_gate` — **the general form of both advisories** | CI + bench |

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
- **Partial failure:** `maintain()` is idempotent and per-edge; a crash leaves a
  partially-maintained store, which is safe because every operation narrows.
- **New attack surface:** none. This spec only removes capability.

---

## 8. Claims and limits

- **What we will say:** *"0.4.5 fixes three provenance defects found by an audit
  of every maintenance-time operation, prompted by two advisories in the same
  class. `confirm()` no longer moves a fact's first-known date; a staleness flag
  can no longer be cleared by a different author; outcome authorship is no longer
  overwritten."*
- **What this does NOT establish.**
  - **Not that the class is now closed.** It establishes that nine mutation sites
    were enumerated and checked on **2026-07-31 at commit `06c6f13`**. N7 is the
    only check that generalises; the rest are instance checks.
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
| Q2 | Should M2/M3/M4 ship as 0.4.5 without an advisory? None is a trust-boundary bypass; M2 puts a false date in model context. | **blocking** | Quentin | before release |
| Q3 | Does the paper-2 conflict in §8 need a stated policy, or is per-case judgement enough? | `pre-release` | research | before paper 2 runs |
| Q4 | Should `needs_confirmation` be per-author rather than a single boolean? Would dissolve M3 structurally. | `deferred` | dev | own design round |
| **Q5** | **M7: what is a correction?** (a) mirror `confirm()` and refuse on non-assertable edges, or (b) inherit the corrected edge's trust class instead of hardcoding `USER`. Dev leans **(b)**; **(a) has the better precedent argument.** Plus: `actor` reaches only an f-string and must be resolved either way. **§11b.** | **blocking — HOLDS EXTERNAL REVIEW** | research | before 0002 is sent |

---

## 11. Finding status (verified against code, 2026-08-01)

| # | finding | status |
|---|---|---|
| **M1** | consolidation derived provenance from `cold[0]` | ✅ **shipped 0.4.4** + advisory GHSA-hcj3-8jqc-wqrp |
| **M2** | `confirm()` mutated `valid_from` | ✅ **shipped 0.4.5** |
| **M3** | cross-author clearing of `needs_confirmation` | ✅ **shipped 0.4.5** |
| **M4** | `record_outcome` overwrote authorship | ✅ **shipped 0.4.5** |
| **M5** | merge-time `confidence = max(...)` | 🟢 **RESOLVED 2026-08-01 — no code change needed today.** T1 keeps `max`; T2 keeps the survivor's own confidence. T2 is unwritten, so this is now a **constraint on the T2 design** rather than a fix. Note what the resolution corrects in *my* framing: I offered a blast-radius measurement (one consumer, no ranking effect) as the argument, and research's ruling names that as answering **"how bad is it"** when the question was **"is it justified."** Severity bounds the cost of being wrong; it says nothing about legitimacy. |
| **M6** | `import_memory` has no trust boundary | 🟡 **FIX SPECIFIED (§11a), not yet implemented.** Cap at the remap with existing 0.1.7 machinery. **The cross-project-inheritance docs recipe stays held** until it ships. |
| **M7** | `correct()` elevates non-assertable facts | 🔴 **open — needs an internal decision, see Q5 (§11b).** Two defensible fixes that disagree about what a correction *is*. **This is the one finding holding external review**, by explicit decision 2026-08-01: sending the spec with it open invites a review of the gap rather than of the argument. |
| **M8** | wiki serves a revoked trust decision | 🟡 **FIX SPECIFIED (§11c), not yet implemented.** Drop the cache in `store.invalidate_edge` — a real single choke point. **§11c also strikes an unreachable clause from the original finding.** `compile.py` stays **guarded** (`8ad5167`). |

**So the spec is half-executed:** the three shipped findings are the ones that
were straightforward corrections; **the four open ones each need a decision or a
design, not just a patch.** M5 is research's, M6 needs the remap-cap rule, M7
needs `confirm()`'s guard applied to `correct()`, M8 needs the drop-on-revocation
rule.

**External review is outstanding and should not be requested until M5–M8 carry
proposed resolutions** — sending a spec whose findings are half-open invites a
review of the gaps rather than the argument. **Reaffirmed 2026-08-01 with the
cost now visible:** M5 is resolved and M6/M8 carry specified fixes below, so
**M7 alone holds the review, and three fixes are queued behind it.** That is
accepted deliberately rather than by drift — see Q5.

---

## 11a. M6 — the fix: cap at the remap

**Where.** `portability.import_memory`, at the point `user_id=` is applied
(`portability.py:85`, `rec["user_id"] = target_uid`). Not at `add_edge`, and not
in `Edge.model_validate` — **the remap is the only place the referent changes**,
which is the whole mechanism of the finding.

**The rule.**

> When `user_id=` is supplied **and differs from the export header's
> `user_id`**, every imported edge is capped: `derived_from = THIRD_PARTY`
> (already-capped edges keep their own value — `min`, never raised).

**Restore is untouched** — no `user_id=`, or the same one, imports byte-for-byte
with provenance preserved. That case is the reason `import` exists and
preserving provenance there is correct.

**Why cap rather than rewrite `author_of_evidence`.** The record is not false.
Alice's edge honestly says *"authored by the user of this store"*; re-homing it
changes what that sentence refers to. Overwriting the author to `THIRD_PARTY`
would **destroy a true statement to fix a referent problem**, and it would lose
the fact that this was somebody's first-person testimony — which a later
operator may need. Capping leaves the record intact and makes the *effective*
trust correct, which is exactly the 0.1.7 contract: **`derived_from` may cap,
never raise.** No new machinery, and no dependency on `specs/0003`.

**Consequence, stated plainly:** after a remapping import, nothing from the file
is assertable in the target store. **That is the intended outcome** — the
population this feature serves is importing content it did not author. A host
that wants an imported fact asserted has the same answer `confirm()` gives:
that affirmation is new user-authored evidence and belongs in `remember()`.

**Checks.** `test_remapping_import_caps_trust` (Alice→Bob: `assertable` False,
`derived_from` `THIRD_PARTY`) · `test_restore_preserves_provenance_exactly`
(round-trip with no remap is byte-identical) · `test_import_cap_never_raises`
(an edge already carrying `derived_from=THIRD_PARTY` and `author=THIRD_PARTY` is
unchanged).

---

## 11b. M7 — NOT specified; the decision is Q5

**Deliberately left open.** Both candidates are one-liners; they disagree about
**what a correction is**, and picking by ease would settle a trust-semantics
question by accident.

| | (a) mirror `confirm()` | (b) inherit the corrected edge's class |
|---|---|---|
| rule | refuse to `correct()` a non-assertable edge | the replacement edge takes the original's `author_of_evidence` / `disclosure` instead of hardcoded `USER` |
| a correction is… | **an assertion** — so it is new user evidence and belongs in `remember()` | **an edit** — the value was wrong; who reported it did not change |
| third-party typo fix | **blocked** | works; result stays a third-party claim |
| precedent | **stronger** — `confirm()`'s docstring already makes this argument, and correcting a value is a *stronger* assertion than affirming one | **stronger** — *maintenance may narrow, never widen*; hardcoding `USER` is the widening, and this is the shape the rest of the system obeys |

**Dev leans (b)**; **(a) has the better precedent argument.** Recorded that way
on purpose — the two arguments point opposite ways and I do not want the lean
to read as a resolution.

**Independent of (a)/(b): `actor` must be resolved.** It appears twice — the
signature and an episode f-string — so it reaches nothing that affects trust. A
caller passing `actor="system"` is **silently ignored where it matters**, and
`record_outcome` right next to it *does* validate actor↔outcome. Either make it
govern or remove it; leaving a parameter that looks like it sets authorship and
does not is its own hazard, independent of which fix lands.

---

## 11c. M8 — the fix: drop the cache at the choke point

**Where.** `store.invalidate_edge`. **Verified to be a real single choke point**
— every invalidation in the codebase goes through it:

```
$ grep -rn "invalidate_edge(" --include=*.py src/veracium/
lifecycle.py:45  "lapsed"     lifecycle.py:49  "decayed"
graph.py:136     "absorbed_duplicate"   graph.py:141  "superseded"
__init__.py:462  "disputed"   __init__.py:612  "corrected"
```

**Putting it in `Memory.dispute()`/`correct()` would miss `graph.py`'s
supersession**, which is the path an attacker reaches — so the store layer is
not a stylistic preference here.

**Which reasons drop the wiki:** `disputed` · `corrected` · `superseded`.
**Not** `lapsed` / `decayed` — those are time-based staleness, not a revoked
trust decision, and dropping curated breadth on every decay cycle pays a real
cost for no trust gain. `absorbed_duplicate` is **arguable and currently
excluded**: the content survives in the surviving edge, so the wiki is not
serving anything revoked. Flagged rather than decided.

**Drop, do not recompile** — no LLM call, no latency, fails closed. Curated
breadth is lost until the next natural recompile; revoked content is never
asserted.

### ⚠️ Correction to the M8 finding: one clause is unreachable

The original text says the fix covers *"and any quarantine."* **There is no
post-ingest quarantine path.** Verified mechanically rather than recalled:

```
$ grep -rn "disclosure\s*=" --include=*.py src/veracium/
ingest.py:117   disclosure = _disclosure_for(author, relation, derived_from)
ingest.py:128   disclosure=disclosure, ...
```

`disclosure` is written in **exactly one place**, at ingest, and never lowered
afterwards. The clause describes an event that cannot occur, and it is **struck
rather than implemented** — building a handler for it would have produced dead
code that reads as coverage.

**Worth naming as a method note:** this is the third time in this spec that a
claim survived because it sounded right. It came from my own summary of
research's finding, not from research.

**Checks.** `test_dispute_drops_the_wiki` (the reproducer becomes the fixture) ·
`test_third_party_supersession_drops_the_wiki` (the `graph.py` path, which is
why the fix is in the store) · `test_decay_does_not_drop_the_wiki` (the
exclusion is deliberate, so it is pinned).
