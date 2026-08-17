# Feature spec: non-revival under maintenance — a revoked source cannot re-enter (A3b)

Spec-Status: draft
Spec-Requires: 0005, 0009, 0012, 0021, 0022

*From research's design proposal
(`veracium-research/proposals/a3-source-revocation-design-proposal.md`,
2026-08-17, greenlit, with dev's corrections folded), decomposed by dev
into 0022 (A3a — the operation) and this spec (A3b — the rider rows and
the lifecycle-op conformance family). No review rounds yet; see
`## Review closure`.*

***The coupling with 0022 is MACHINE-CHECKED and acceptance is ATOMIC:
`Spec-Requires` is MUTUAL — 0022 requires 0023 and 0023 requires 0022 —
so the existing gate refuses either alone, the 0016/0018 and 0020/0021
precedent. The reason, stated at full strength: 0022's sweep without this
spec is a boundary with an UNLOCKED BACK DOOR — the sweep retires
everything the revoked source wrote and the very next ingest, import or
maintenance pass lets the same source's content back in, so the boundary
holds for exactly as long as nothing happens. This spec without 0022's
sweep governs only the FUTURE, leaving every record the source already
wrote standing and assertable. Each half alone is worse than misleading,
because each looks like the feature.***

## 1. Problem and motivation

Revocation that only reaches the past is not revocation. If a host
revokes a compromised connector on Monday and the connector's next sync
lands on Tuesday, an operator who reads the completeness statement
believes the source is gone while the store quietly refills. The same
holds for every other path content takes into the assertable set:
re-ingest of the identical event, a reinforcement that refreshes a
surviving record's standing, an absorption that merges revoked content
into a live record, a consolidation that synthesizes it into a new
episode, an expiry-renewal that resurrects a lapsed fact on a revoked
observation, and an import of an export file made before the revocation.

**What happens if we do nothing:** 0022 ships a tool whose guarantee
decays from the moment it returns, and the failure is SILENT — nothing in
the store says "this came back". That is the same shape as the two
advisories this project already carries and the same shape as 0004's
finding: a trust decision that does not reach every surface is a trust
decision that did not happen.

**Prior art, cited rather than reinvented:** GPM (2608.12476) states a
non-revival clause for revoked memory. Ours differs in two ways worth
naming, because they are what makes it enforceable here: it is
**source-joined** (the condition is a standing revocation on a resolved
identity, not a semantic match on content) and it is
**transformation-scoped** (stated per lifecycle operation, in the matrix
that already exists, rather than as a global assertion nobody can check).

**The enforcement is nearly free, and that is the decomposition's whole
argument.** 0021's §3 operation matrix is already TOTAL and already
MECHANICALLY enforced: `COMBINING_SITES` is a registry in the code and a
combining path absent from it fails `test_scope_operation_matrix_is_total`.
The rider rows land in that matrix, so the day this spec is accepted the
totality machinery starts failing the build for any combining operation
that has no revocation disposition. We inherit machine enforcement on day
one instead of writing a new mechanism.

**Alternatives rejected.**

- **Rely on 0022's sweep alone, and tell operators to re-run it.**
  Rejected: a guarantee whose maintenance is the operator's homework is
  not a guarantee, and the window between refills is exactly when the
  model reads the store.
- **REFUSE writes from a revoked source outright** (raise at ingest).
  Rejected: refusal destroys the evidence that the source is still
  emitting — which is precisely what an operator investigating a
  compromise needs — and it turns a trust decision into an availability
  incident for the host's pipeline. Quarantine-at-birth retains
  everything, asserts nothing, and leaves the audit trail intact. It is
  also the lower-blast-radius answer under the forged-source cell 0022
  §3b names.
- **Write the rider rows directly into 0021.** Rejected: 0021 is
  ACCEPTED, and editing an accepted spec's normative matrix in place
  re-opens it. The rows are DRAFTED HERE for same-commit landing at this
  pair's acceptance — the rider precedent 0021 itself used for its 0014,
  0016/0018 and 0019 carriers.
- **A per-record `revoked` flag written at ingest.** Rejected: it is a
  second copy of a fact the standing state already carries, it goes stale
  the moment a revocation is lifted, and 0020's Q1 already settled this
  shape — policy over identity, no new per-record field.

## 2. Field contracts touched

| field | read / written | its documented contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Provenance.disclosure` | written at ONE site | today `_disclosure_for(author, relation, derived_from)` decides it at ingest, and **nothing lowers or raises it afterwards** (0004 verified this mechanically) | the gate, render, proactive, export | the function gains a FOURTH input — whether the record's resolved source stands revoked — and returns `QUARANTINED` when it does. **The site does not move and no second writer appears** (**N2**): the contract that made 0004's analysis possible is preserved, and this spec depends on it |
| `Provenance.origin` / `source_id` | READ | 0006: namespacing; resolved at read | the digest, the ledger, 0020's scope key | read at WRITE time now, to resolve and digest for the standing-state lookup. No field is added and none is written |
| the ingest result dict (`facts`/`quarantined` counts) | written | the per-event summary the host logs | hosts, telemetry | a quarantined-at-birth record counts in `quarantined`, exactly like any other quarantined claim. **No new key**, so no consumer breaks; the operator's signal that a revoked source is still emitting is that count plus the audit line |
| absorption candidate selection (`graph.py`) | changed | same-class subsumption merge, extended by 0021 with a same-scope requirement through `_absorption_scope_gate` | `apply_supersession_plan` | extended once more, at the SAME seam: a record whose resolved source stands revoked is not a candidate on either side. This is the third rail on one gate, not a third gate |
| supersession authority (`apply_supersession`) | changed | 0003's ladder decides whether the incoming may retire the prior | the plan primitive, refusals | a revoked-source incoming may NOT retire a standing record; the refusal is the SHIPPED content-free refusal record, not a new carrier |
| consolidation candidate selection (`lifecycle.partition_cold`) | changed | 0021: cold candidates partition by resolved identity; UNRESOLVED derivatives are excluded from every pool | maintenance | revoked-source records are excluded from every pool by the same rule and at the same site — the precedent is exact |
| 0012 reinforcement | changed in ACCOUNTING only | the incoming restatement is persisted as its own edge with its own provenance and the prior is left byte-untouched; reinforcement transfers NOTHING | the planner's `reinforced` count, renewal | the incoming edge still persists (quarantined, per the disclosure rule above) but is NOT counted as a reinforcement and never renews the prior's currency. Since reinforcement already transfers nothing, this is a small change with a large claim attached, and **N3** is what makes the claim testable |
| the import disclosure cap (`portability.py`) | changed | 0005: an imported record is capped to THIRD_PARTY / `USE_ONLY`, or stays `QUARANTINED` | import | the cap gains one more floor: a record whose resolved identity stands revoked in the DESTINATION is capped to `QUARANTINED`. The capping site already exists and already counts what it capped |
| `COMBINING_SITES` | extended | 0021: the mechanical totality registry for the operation matrix | `test_scope_operation_matrix_is_total`, the generated manifest | every combining site gains a revocation disposition; a site without one FAILS the build (**N9**) |

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | invariant that pins it |
|---|---|---|---|---|---|
| the `source_id` a host supplies at ingest — **PRODUCERS row: the host's entry point AND THE STORE'S OWN MACHINERY (the import path, migration back-fill, and every maintenance output that inherits or clears identity under 0021)** | absent → NO digest, so no standing revocation can match: the record lands under today's rules. Stated, not hidden (**N11**) | out of bounds → refused by the shipped model validation before this spec sees it | an identity no revocation names → today's behaviour exactly | a writer OMITS `source_id` to escape a standing revocation | the same cell 0022 names: absence buys unreachability and costs the writer every grouping benefit. **N11** makes it a named, tested behaviour rather than a discovered one |
| the standing revocation set, read at write time | no rows → **every path behaves byte-identically to today** (**N12**) | a malformed row → REFUSED at read by 0022's validator, and the write path inherits the refusal rather than defaulting to "not revoked" | an action string this version does not know → refused; never silently treated as "not revoked" | a planted row that makes an honest source look revoked | fail-closed in the RESTRICTING direction only: a refusal to read the table must never let a write proceed as unrevoked, so the read is inside the write transaction and its failure aborts the write (**N10** covers the direction; §7 covers the mode) |
| an imported export file's provenance (FORMAT 7) | absent identity → no digest, no match; the 0005 cap still applies | non-dict / null provenance → the whole import refuses, as today | a `version` newer than this build understands → the existing rule strips unknown fields; identity fields are not new | **a file crafted so its records claim a source that is NOT revoked here** | this is 0005's boundary, not a new one: imported records are ALREADY capped to third-party/`use_only`, so a false identity buys at most what any import buys, never assertability (**N8**) |
| the local-origin resolution at import | — | — | a foreign origin → kept as its own (0006), so it matches a destination revocation only if the destination revoked THAT pair | a locally-authored record exported and re-imported to escape a revocation | 0006's same-store round-trip rule makes the identity resolve identically, so the record RE-QUARANTINES on arrival — the FORMAT-7 round-trip cell (**N8**) |
| the relation vocabulary at ingest | — | — | an unknown relation → today's handling, unchanged | a relation chosen to dodge the quarantine branch | the standing-revocation input is evaluated INDEPENDENTLY of relation and author, so no content-shaped input can steer it (**N1**) |

## 2c-ii. Assertions about reach — REQUIRED

**Every command below was RUN, in this repository, on 2026-08-17, and the
result column records its real output.** Re-run at implementation.

| assertion | command that establishes it | result (RUN 2026-08-17) |
|---|---|---|
| **disclosure is written at exactly ONE site, and never lowered afterwards** — the property this spec's write-time gate depends on and must not break | `grep -rn "disclosure\s*=" --include=*.py src/veracium/` | seven hits, of which exactly ONE is a WRITE at ingest: `ingest.py:181` (`disclosure = _disclosure_for(...)`) feeding `:199`. The others are READS (`schema.py:280/286` the derived properties, `graph.py:254` the same-class comparison, `scope_read.py:384`) and ONE further write — `portability.py:396`, the 0005 IMPORT CAP, which is a boundary cap and is the second site this spec must extend |
| **the absorption gate seam already exists and already takes one extension** | `grep -n "_absorption_scope_gate" src/veracium/graph.py` | `graph.py:188` (the gate) and `:307` (`same_scope = _absorption_scope_gate(store, edge)`, consulted in the candidate loop). 0021 put it there; the revocation rail rides the SAME seam |
| **the consolidation partition seam already exists** | `grep -n "partition_cold" src/veracium/lifecycle.py` | `lifecycle.py:132` (the function) and `:274` (`for key, members in partition_cold(store, user_id, cold)`) — the exact site where 0021 excludes UNRESOLVED derivatives from every pool |
| **the totality registry this spec's rows inherit is real and mechanical** | `grep -n "COMBINING_SITES\|__all__" src/veracium/combining.py` | `combining.py:30` (`__all__ = ["OPERATIONS", "COMBINING_SITES", "SiteSpec"]`) and `:73` (the registry). `specs/combining_sites.py --check` fails when the code and the registry disagree, which is what **N9** rides |
| **reinforcement persists the incoming edge and transfers nothing** — so the change here is an ACCOUNTING change, not a data one | `grep -n "reinforcement transfers NOTHING" -B 2 -A 3 src/veracium/graph.py` | `graph.py:76-80` — *"the incoming restatement is PERSISTED as its own edge with its own provenance, and the prior is left byte-untouched — reinforcement transfers NOTHING (not `observed_at`, not `confidence`, not `valid_from`)"* |
| **the import path ALREADY caps disclosure, so the revocation floor is one more clause at a live site** | `grep -n "capped = model.model_copy" -A 8 src/veracium/portability.py` | `portability.py:392-399` — the cap sets `author_of_evidence`/`derived_from` to THIRD_PARTY and disclosure to `QUARANTINED` if it already was, else `USE_ONLY`, counting every record it capped at `:400` |
| **the export/import format is FORMAT 7 today** (the round-trip cell's version) | `grep -n "^FORMAT_VERSION" src/veracium/portability.py` | `portability.py:51` — `FORMAT_VERSION = 7  # specs/0016 D2 (0019 rider A3)` |
| **quarantine is a DERIVED property of disclosure, not a settable flag** — which is why the rule lands in the disclosure function and not in a new column | `grep -n "def quarantined" -A 6 src/veracium/schema.py` | `schema.py:274-280` — `quarantined` is a `@property` returning `relation == QUARANTINE_RELATION or provenance.disclosure == Disclosure.QUARANTINED`; `assertable` at `:289-293` excludes it |

*(One of these moved the design while it was being written: research's
proposal says "quarantined-at-birth", and the fourth command shows there
is no birth flag to set — quarantine is derived from `disclosure`, so the
rule had to land in the one function that writes it. The second write site
at `portability.py:396` was found the same way, by the first command, and
is the reason **N8** exists as a separate invariant rather than a cell of
**N1**.)*

## 3. The operation matrix — the RIDER ROWS, total by construction

These are the rows that land in 0021's §3 operation matrix (drafted here,
same-commit at acceptance — §7b). **Directional where the operation is**,
because prior-vs-incoming asymmetry is where the 0.4.1 defect lived:

| operation | timing | prior revoked, incoming live | incoming revoked, prior live | both revoked | rule and why |
|---|---|---|---|---|---|
| ingest (the write itself) | write | n/a | the incoming lands QUARANTINED at birth | same | it is retained and never assertable; refusal would destroy the evidence that the source is still emitting (§4a) |
| supersession | write | the incoming may retire the prior under 0003's ladder, unchanged — a revoked source's record has no special protection | **REFUSED**: a revoked-source incoming may not retire a standing record; the prior stays active and a content-free refusal is recorded | refused | restrict-only: the revoked side never gains the power to remove content. The refusal carrier is the shipped one (§4d) |
| absorption | write | the prior is NOT a candidate; the incoming accumulates as a separate edge | the incoming is NOT a candidate; both persist separately | neither absorbs | a merge inherits lineage, so a revoked source must not enter a survivor by either door. Rides `_absorption_scope_gate` (§4f) |
| reinforcement | write | n/a — the prior is not touched by reinforcement in any case | the incoming persists (quarantined) but is NOT counted as reinforcement and renews nothing | same | 0012 already transfers nothing; what this closes is the CURRENCY claim (§4c) |
| consolidation | maintain | excluded from every pool | excluded from every pool | excluded | the LLM cross-record synthesis site — the one path that can launder revoked content into new text (§4e) |
| expiry / decay / staleness | maintain | unchanged (ageing is not revival) | a revoked-source observation does not clear staleness or extend currency | unchanged | renewal is the one place ageing runs BACKWARDS, and it is exactly the revival path (§4g) |
| wiki compilation | maintain | — | — | — | compiled from the assertable set, so a quarantined-at-birth record never enters it; and 0022's retirements drop the cache through 0004's reason vocabulary. **No rule of its own is needed, and saying so is a row** |
| import (FORMAT 7) | boundary | — | records whose resolved identity stands revoked in the DESTINATION are capped to QUARANTINED at the existing cap site | same | 0005's boundary gains one floor; the round-trip case re-quarantines (§4h) |

**Totality is MECHANICAL, inherited on day one:** `COMBINING_SITES` and
the generated manifest already fail
`test_scope_operation_matrix_is_total` for any combining operation
missing its row, so a combining path added later without a revocation
disposition fails the build rather than silently defaulting to "allowed"
(**N9**). Ingest, expiry and import are not combining operations, so they
are covered instead by **N1**, **N2** (the single-writer AST sweep) and
**N8**.

Then, explicitly:

- **Can this cause a user-asserted fact to become non-assertable?** Yes,
  in one direction: a user-authored record written under a revoked source
  lands quarantined. That is the intended semantics of revoking the
  source a user's own connector writes under, and it is the forged-source
  cell 0022 §3b names and bounds.
- **Can it cause non-user content to gain user-grade authority,
  confidence, or currency?** **No.** Every rule here REMOVES a capability
  from the revoked side. `test_non_revival_grants_nothing` enumerates the
  temptations — the most tempting being "a refused supersession must not
  promote the prior" (**N10**).
- **Can it clear `needs_confirmation`?** No; nothing here touches it.
- **Does it merge, drop, or overwrite provenance?** No. Records are
  written with a lower disclosure, or not merged at all. Nothing existing
  is rewritten.

**Write-time or maintain-time?** **Both, and the split is deliberate.**
Write-time rules (ingest, supersession, absorption, reinforcement)
consult the standing state as new evidence arrives, which is the
legitimate moment to decide what a new record may claim. Maintain-time
rules (consolidation, renewal) only ever EXCLUDE; no maintain-time rule
here refreshes currency or raises a flag, so the T2 prohibition —
maintenance may not manufacture freshness from recognition — is respected
by construction.

## 3b. Authorization and scope

- **No new caller-facing surface.** There is no API to enable this. The
  gate is consulted inside the store and inside ingest, so a host cannot
  turn it off for its own writes, and no configuration reaches it. This
  is 0021's policy-independence lesson applied verbatim: a rule about
  what the store ACCEPTS cannot be a per-process setting, or an honest
  host and a careless one produce different stores.
- **Per user**, because 0022's standing state is per user. A revocation
  for user A quarantines nothing for user B (**N11** covers the
  identity-absent cell; the user boundary is 0022's **R13**).
- **Does anything become visible to a principal who could not see it
  before?** **No — strictly less.** A quarantined-at-birth record is not
  assertable and never enters the wiki or the grounded block; it remains
  visible to the operator surfaces (`introspect`, `export_memory`) that
  already show quarantined claims. Under 0020, scoped principals see no
  more than before.
- **What an observer can infer.** A host watching its own ingest counts
  can tell that a source is revoked, because its facts land in the
  `quarantined` count. That is the operator's own signal about the
  operator's own store, and it is the point.

## 4. Behaviour

### 4a. Quarantined-at-birth — one function, one site

`_disclosure_for` gains a fourth input: whether the record's RESOLVED
source identity stands revoked for this user at write time. When it does,
the result is `Disclosure.QUARANTINED`, whatever the author and relation
would otherwise have given.

Three things about this are load-bearing rather than incidental:

1. **There is no "birth flag" to set.** `Edge.quarantined` is a DERIVED
   property of `disclosure` (§2c-ii), so quarantine-at-birth is
   expressible only as a disclosure decision. A spec that asked for a new
   column here would have been asking for a second source of truth for a
   value the model already derives.
2. **The site does not move and no second writer appears** (**N2**).
   0004's analysis of the wiki depends on disclosure having exactly one
   write site; adding a second would break a property another accepted
   spec reasons from. The AST sweep that pins it is the same pattern
   0004's own W7 uses.
3. **It applies to every record the event produces** — the edges AND the
   episode — because both carry provenance and both reach the model
   through different paths.

The record is RETAINED. Nothing is refused, nothing is dropped, the
`quarantined` count in the ingest result rises, and one audit line
records that a write from a revoked source was quarantined (content-free:
the digest, the count, no text).

### 4b. What the standing state costs at write time

The gate is one lookup of the derived standing set per write, keyed by
the resolved digest. A store with NO revocation rows has an empty set and
takes the same branch it takes today (**N12** — byte-identical stored
state and reads). The set is small by nature (one row per revoked source
per user), and the lookup happens inside the write transaction so that a
failure to read it ABORTS the write rather than proceeding as unrevoked.

### 4c. Reinforcement — the currency claim, closed

0012 already persists the incoming restatement as its own edge and leaves
the prior byte-untouched, so a revoked source's restatement transfers
nothing today. What it CAN do today is make a fact look current, because
each edge ages against its own `observed_at` and a fresh edge keeps the
fact alive. Under a standing revocation the incoming edge is quarantined
(§4a), is **not counted as a reinforcement**, and **never renews the
prior's currency** (**N3**). The claim this closes is not "data moved" —
it is "a revoked source can keep a fact from ageing out by repeating
it".

### 4d. Supersession — refused, with the shipped carrier

A revoked-source incoming may not retire a standing record. The refusal
uses the SHIPPED content-free refusal record (0003's), not a new carrier:
the prior stays active, the incoming is stored (quarantined), both are
visible, and the refusal is durable and queryable. **The direction
matters and both cells are stated in §3:** a LIVE incoming may still
retire a revoked-source prior under 0003's ladder, because a revoked
source's record earns no protection from being revoked — that would be a
grant.

### 4e. Consolidation — excluded from every pool

A record whose resolved source stands revoked is not a consolidation
candidate, at the same site where 0021 excludes UNRESOLVED derivatives
(`partition_cold`). Consolidation is the LLM cross-record synthesis site
and therefore the one path that can launder revoked content into NEW text
that carries none of its provenance — the general form 0021 states as
*every LLM re-rendering the machinery doesn't control is a laundering
site*. Exclusion, not filtering-after: the revoked record never reaches
the prompt.

### 4f. Absorption — not a candidate on either side

The candidate loops additionally require that neither side's resolved
source stands revoked. This rides `_absorption_scope_gate`, the seam 0021
already added for scope, which means the rule is one more rail on one
gate rather than a third gate — and a cross-revoked prior accumulates as
a separate edge, which is today's cross-class and cross-scope behaviour
extended one axis.

### 4g. Expiry-renewal — ageing forward only

Expiry and decay are scope-blind and revocation-blind: ageing is not
revival, and a revoked source's record ageing out is the correct
outcome. **Renewal is the exception that needs the rule**, because it is
the one place the lifecycle runs backwards: an observation that clears
staleness or extends currency must not come from a revoked source
(**N7**). This is the same reasoning as §4c, at the other end of the
lifecycle.

### 4h. Import — the FORMAT-7 round-trip

An import is a boundary, and 0005 already caps every imported record's
disclosure. The rider adds one floor: **a record whose RESOLVED identity
stands revoked in the DESTINATION store is capped to `QUARANTINED`**, at
the existing capping site, counted by the existing counter.

The round-trip case is the one worth stating, because it is the obvious
escape and it closes by inheritance rather than by new machinery:
0006 makes a locally-authored record's identity resolve identically after
an export and re-import into the SAME store (absent origin resolves to
that store's singleton on both sides). So exporting a revoked source's
records before revoking and importing them afterwards RE-QUARANTINES them
on arrival (**N8**). A file from a DIFFERENT store carries its own
foreign origin and therefore matches a destination revocation only if the
destination revoked that foreign pair — which is correct, and is the
honest limit: a determined operator can move content between stores, and
no import-side rule can tell that content's original source from a
plausible claim, because identity is namespacing, not authentication.

### 4i. What a LIFT does — and the ASYMMETRY we are declaring

Lifting a revocation (0022 §4f) restores ORDINARY behaviour for FUTURE
writes immediately and with nothing to unwind: every rule above consults
the standing state at the moment of the write, so there is no
write-time state to reverse.

**It does NOT un-quarantine records that already landed quarantined at
birth, and this asymmetry is declared rather than discovered.** 0022's
retirements reverse by supersession and its recomputes reverse by
recomputation; a quarantine written into `disclosure` would reverse only
by a SECOND disclosure writer, which would break the single-write-site
property (§4a, **N2**) that 0004 reasons from and that this spec depends
on. We are not adding that writer for v1.

The operator's remedies are the ones this codebase already uses
everywhere: the source is live again, so its next event lands ordinarily;
or the content is restated. Nothing is lost in the meantime — quarantined
records are retained, exported and shown by `introspect`. **N13** pins
the asymmetry in BOTH directions so it cannot erode either way: a lift
must not silently start rewriting disclosure, and a future decision to
allow it must be a spec change (§10, **Q2**).

### 4j. Interfaces and migration

**No new public API.** No new field, no new CLI verb, no new MCP tool.
The behaviour changes only in the presence of a standing revocation, and
0022 owns the surface that creates one. **A store with no revocation rows
is byte-identical in stored state and in every read to a store that never
upgraded** (**N12**) — the migration invariant, and the reason this pair
rides the ordinary release path.

## 5. Regime analysis

| regime | behaviour |
|---|---|
| no revocation ever recorded | every path takes today's branch; stored state and reads byte-identical (**N12**). This is the regime almost every store is in, so it is the one that must be provably free |
| one revoked source, low write volume | one set lookup per write; quarantined records accumulate in the `quarantined` count |
| **a revoked source that keeps syncing at volume** (the realistic compromised-connector case) | every event lands quarantined and RETAINED, so the store GROWS while asserting nothing. **The regime the tests must reach**: enough events that quarantined records outnumber assertable ones, because that is when an operator's `introspect` view and their storage bill both change. Retention of quarantined content is a real cost and is stated in §8 rather than discovered in production |
| many revoked sources | the standing set is one row per source per user; the lookup is a set membership test, not a join |
| consolidation over a store where most cold candidates are revoked-source | pools shrink below the min-batch threshold and consolidation becomes a NO-OP for that user — a visible, honest degradation rather than a silent laundering |
| a store mid-rolling-upgrade, one writer without this spec | the old writer does NOT consult the standing state, so revoked content can still enter through it. **The claim is therefore narrowed exactly as 0021 narrowed W1: non-revival holds on stores operated exclusively by 0023-capable writers**, and the deployment requirement is stated plainly in §8. Reads stay fail-closed throughout, because 0022's sweep and the gate both act on what is IN the store |
| import of a large pre-revocation export | every record is checked against the destination's standing set at the existing cap site; the cap counter reports how many were floored |
| cold vs warm | no caching is introduced; the standing set is read per transaction. If a future implementation caches it, the cache must be invalidated inside the same transaction that appends a revocation row — a named implementation obligation, not an optimisation to discover later |

## 6. Invariants and executable checks — REQUIRED, blocking

**Status: STAGE-5 OBLIGATIONS — none of the named tests exists yet
(draft).** The conformance family (**N1**–**N8**) is one file so that the
lifecycle sweep is legible as a whole:
`tests/test_0023_non_revival.py`.

| invariant | executable check |
|---|---|
| **N1** ingest under a standing revocation lands QUARANTINED at birth, on every record the event produces (edges AND the episode), independently of author and relation | `test_revoked_source_ingest_is_quarantined_at_birth` |
| **N2** `disclosure` still has exactly ONE ingest writer plus the ONE import cap, and no third writer exists anywhere | `test_disclosure_writers_are_exactly_the_two_known_sites` (an AST sweep — the 0004 W7 pattern; a new writer FAILS the build) |
| **N3** a revoked source's restatement is not counted as a reinforcement and never renews the prior's currency; the prior is byte-unchanged | `test_revoked_source_does_not_reinforce` |
| **N4** absorption takes a revoked-source record as a candidate on NEITHER side; both records persist separately | `test_absorption_refuses_a_revoked_source_on_either_side` (both directions, as separate cells) |
| **N5** a revoked-source incoming may not retire a standing record — the prior stays active and a content-free refusal is recorded; the REVERSE direction still works (a live incoming may retire a revoked-source prior) | `test_revoked_source_cannot_supersede` |
| **N6** consolidation excludes revoked-source records from every pool, at `partition_cold`; a pool that falls below threshold is a no-op, never a partial merge | `test_consolidation_excludes_revoked_sources` |
| **N7** renewal: a revoked-source observation clears no staleness and extends no currency; ordinary ageing is unaffected | `test_revoked_source_does_not_renew` |
| **N8** the FORMAT-7 import round-trip: records whose resolved identity stands revoked in the DESTINATION arrive QUARANTINED, including the export-then-revoke-then-reimport sequence into the SAME store | `test_import_round_trip_requarantines` |
| **N9** the operation matrix is TOTAL: every combining site carries a revocation disposition, enforced by the shipped registry | `test_scope_operation_matrix_is_total` (0021's, extended) + `specs/combining_sites.py --check` |
| **N10** non-revival is RESTRICT-ONLY: no operation gains anything under a standing revocation — enumerated temptations, including "a refused supersession must not promote the prior" and "an excluded consolidation candidate must not be re-scored" | `test_non_revival_grants_nothing` |
| **N11** a record with no `source_id` has no digest and is never affected by any standing revocation, at any of the sites above | `test_unidentified_writes_are_never_quarantined_by_revocation` |
| **N12** a store with NO standing revocation is byte-identical in stored state and in every read to a store that never upgraded | `test_no_revocation_is_byte_identical` |
| **N13** a lift restores ordinary behaviour for FUTURE writes with nothing to unwind, and does NOT rewrite the disclosure of records already written — the declared asymmetry, pinned in both directions | `test_lift_does_not_rewrite_existing_disclosure` |

Standing checks that must not regress: injection asserts 0 · cross-user
leaks 0 · trust canaries 0 · supersession probes pass · malformed edges 0.

**Measurement counterpart, named and NOT claimed here:** research's
D-extension gains a revoked-source resurfacing probe class (does
revoked-source content surface in answers after a revocation, at source
granularity). That is the live/value-level twin of this conformance
family; it is research's obligation, it runs under value-level
containment, and no row above depends on it.

## 7. Failure modes and reversibility

- **How it fails SILENTLY.** The dangerous failure is a NEW write path
  added later that does not consult the standing state — a second ingest
  entry point, a new maintenance operation, a bulk importer. It would
  look correct in every test that does not know to look for it, and the
  first symptom would be revoked content in an answer. That is why the
  totality is MECHANICAL (**N9**) and why the disclosure writers are
  pinned by an AST sweep (**N2**) rather than by a grep someone ran once.
  Neither mechanism is new; both are inherited.
- **The second silent mode** is the mixed-writer window (§5): a
  pre-0023 process writing to a shared store. The claim is narrowed in
  §8 rather than defended.
- **Reversibility.** Complete for future writes and immediate — lift the
  revocation and the next write behaves ordinarily, because the state is
  consulted at write time and nothing is stored per record. NOT reversible
  in v1: the disclosure of records already quarantined at birth (§4i, the
  declared asymmetry). No configuration reaches any of this, by design
  (§3b), so there is no setting to get wrong.
- **Partial failure.** A failure to read the standing set aborts the
  write; a write is never completed as unrevoked because the lookup
  failed. Consolidation's per-pool failure semantics are 0021's,
  unchanged: excluding revoked records changes what is in a pool, not how
  a pool fails.
- **New attack surface.** None added: no new caller-facing surface exists
  (§3b). The write-time gate reads a table only the host's own
  `revoke_source` can append to, and its effect is always to reduce what
  new content may claim.

### 7a. Complete public-surface inventory

| carrier | change |
|---|---|
| `src/veracium/ingest.py` | `_disclosure_for` gains the standing-revocation input; the site does not move (**N1**, **N2**) |
| `src/veracium/graph.py` | the absorption candidate rail on `_absorption_scope_gate`; the supersession refusal cell |
| `src/veracium/lifecycle.py` | `partition_cold` excludes revoked-source records; renewal consults the standing state |
| `src/veracium/portability.py` | one more floor on the existing 0005 import cap (**N8**) |
| `src/veracium/combining.py` + `specs/generated/0021-combining-sites.md` | a revocation disposition per combining site; the generated manifest regenerates (**N9**) |
| `audit.py` | one content-free line when a write is quarantined by revocation and when a merge candidate is excluded |
| `tests/test_0023_non_revival.py` | the lifecycle-op conformance family (**N1**–**N8**) |
| CLI / MCP / public API | **UNCHANGED** — there is nothing to call |
| docs | what a host sees when a revoked source keeps writing: retained, counted, never asserted; and the §4i asymmetry |
| CHANGELOG / marketing | §8's wording, including the mixed-writer narrowing |

### 7b. Cross-spec carriers

| spec | touchpoint | disposition |
|---|---|---|
| **0022** | **MUTUAL `Spec-Requires` — acceptance is ATOMIC** | the standing state, the digest key, the reversal semantics and the forged-source threat model are that spec's and are INHERITED here, not restated. Neither accepts alone: the sweep without these rows is a boundary with an unlocked back door; these rows without the sweep govern only the future |
| **0021** | **THE DRAFTED MATRIX RIDER — same-commit landing at this pair's acceptance** | *(the rider)* §3's operation matrix gains a REVOCATION column carrying the §3 rows above, directional where the operation is; `COMBINING_SITES` gains a revocation disposition per site, and `test_scope_operation_matrix_is_total` fails for any combining operation lacking one. **No accepted rule of 0021 is amended** — the scope rules stand unchanged and the revocation rail is an additional, independent condition on the same seams (`_absorption_scope_gate`, `partition_cold`). Where both conditions apply, the record must satisfy BOTH; neither can widen the other |
| **0005** | the import trust boundary and its existing disclosure cap | EXTENDED at the live site: one more floor, capping to `QUARANTINED` when the resolved identity stands revoked in the destination. 0005's own rules — third-party capping, whole-import refusal on malformed provenance — are inherited unchanged, and this floor can only LOWER what an import may claim |
| **0012** | reinforcement and the independence condition | the incoming edge still persists byte-unchanged, per that spec; what changes is the ACCOUNTING (not a reinforcement) and the CURRENCY consequence (no renewal). 0012's transfer rule is untouched |
| **0009** | the outcome-authorship chain and the import primitive `commit_outcome_import_plan` | the import floor applies to records arriving through that primitive; no plan member, expected-state rule or atomicity contract changes. Declared in `Spec-Requires` because the import path this spec extends is that primitive's |
| **0004** | the wiki | **nothing to add.** A quarantined-at-birth record is not assertable, so it never enters the compiled wiki; and 0022's retirements drop the cache through the reason vocabulary. Stated as a row because "no rule needed" is a claim, and an unexamined one is how a derived view outlives a trust decision |
| **0003** | the supersession ladder and the refusal record | the refusal cell uses the SHIPPED content-free refusal carrier; the ladder itself is unchanged — this adds a precondition, never a new authority |
| **0020** | scoped recall | orthogonal. A quarantined record is not assertable to any principal; scope decides visibility, revocation decides assertability, and neither reads the other |
| **0013 / 0018** | migration | none of this spec's own: it consumes 0022's table. No schema change, no format change, no breaking window |

## 8. Claims and limits

**What we will say** — the exact wording:

> **Non-revival.** While a source stands revoked, its content cannot
> re-enter the assertable set by any path: new events from it are
> retained but quarantined, it cannot reinforce, absorb, supersede,
> consolidate or renew, and importing a file that carries its records
> re-quarantines them on arrival.

**What this does NOT establish.**

- **It is not authentication** (0022's C2, inherited). A revoked source's
  content re-labelled under a different `(origin, source_id)` is, to this
  machinery, different content from a different source. Identity is
  namespacing.
- **It holds on stores operated exclusively by 0023-capable writers.**
  A pre-0023 process writing to a shared store does not consult the
  standing state, so during a rolling upgrade content can still enter
  through it. Upgrade every writer before relying on the invariant. This
  is the same narrowing 0021 took for its partition rule, for the same
  reason, and it is stated here rather than discovered by a reviewer.
- **It does not un-do a quarantine.** Lifting a revocation restores
  ordinary behaviour for future writes only (§4i).
- **Quarantined content is RETAINED, and that costs storage.** A revoked
  source that keeps syncing keeps filling the store with records that
  will never be asserted. That is the deliberate trade against refusal
  (§1), and an operator with a high-volume compromised connector should
  disconnect it, not rely on this to stop the writes.
- **No measurement is claimed here.** The resurfacing probe class is
  research's D-extension obligation and is named, not cited as evidence.

## 9. Brief for the external reviewer

**What we are least sure of:**

1. **The §4i asymmetry.** A lift restores future behaviour but does not
   un-quarantine what already landed, because reversing it means a second
   disclosure writer and 0004 reasons from there being one. We think that
   is the right v1 trade, but it is the seam where a real operator's
   expectation ("I un-revoked it, why is it still quarantined?") diverges
   most from what the machinery does. If you think the asymmetry is worse
   than the second writer, say so — that is the finding we want.
2. **Where the write-time gate is READ.** We put the standing-set lookup
   inside the write transaction so that a read failure aborts the write.
   That is fail-closed, but it also means a corrupt revocation row makes
   the store unwritable for that user rather than merely unrevoked.
   Attack that choice; we are not certain the failure direction is right
   for a store whose ingest is a production pipeline.
3. **The claim that quarantine is enough.** We assert that a
   quarantined-at-birth record cannot reach the model, resting on
   `assertable` excluding quarantined and on the wiki compiling from the
   assertable set. If you can find any path — proactive assembly, the
   contested groups, a render of history — where a quarantined record's
   TEXT reaches rendered context, that breaks the central claim of this
   spec, and it is exactly the class of thing this project has missed
   before (the wiki itself was such a path).

**Where we suspect we have overstated:** "cannot re-enter by ANY path" in
§8. It is true of the paths enumerated in §3, and §3's totality is
mechanical only for COMBINING operations — ingest, expiry and import are
covered by named invariants rather than by a registry, which is a weaker
guarantee than the sentence sounds.

**What would change our minds:** a demonstration that quarantine-at-birth
is the wrong default because the retained volume is unmanageable in a
real compromise, which would push us toward a refusal mode as an explicit,
operator-chosen option (§10, **Q1**).

**Reviewer-safe copy:** nothing here is deployment-specific.

## 10. Open questions

| # | question | state |
|---|---|---|
| **Q1** | should a host be able to choose REFUSAL instead of quarantine-at-birth for a revoked source's writes? | `pre-release` — dev + research, before implementation. v1 quarantines (§1's rejected alternative gives the reasoning), but a host with a high-volume compromised connector may reasonably want the writes to stop. Leaning: keep v1 single-mode and revisit with a real operator's numbers; a mode switch is a configuration that changes what the store ACCEPTS, which §3b argues against |
| **Q2** | should a lift un-quarantine records that landed quarantined at birth? | `pre-release` — dev, before implementation. v1 says NO and **N13** pins it (§4i). Doing it means a second disclosure writer, which breaks a property 0004 reasons from; doing it WELL means re-deriving each record's disclosure through the write path that produced it, which is not decidable from the record alone. Both halves are stated so this is a decision, not an omission |
| **Q3** | the mixed-writer ENFORCEMENT: a store-version bump refusing pre-0023 writers | `deferred` — the same shape as 0021's own deferred enforcement question, and it should ride the same window rather than minting one. Until a release takes it, §8 carries the operational narrowing |
| **Q4** | should the audit line for a quarantined-at-birth write carry the digest, or only a count? | `pre-release` — dev. The digest is content-free and makes "which source is still writing" answerable from the audit sink alone; a count alone is smaller and leaks nothing at all. Leaning: the digest, because the operator investigating a compromise is the whole audience |

## Review closure

*(PROCESS §4a — one row per review finding, with evidence that is openable
or executable. **This spec is a pre-review DRAFT: no round has been run, so
there are no findings and no rows.** The section exists from day one
deliberately — both 0020 and 0021 hit this gate mid-implementation and had
to reconstruct it, and the CI gate refuses an `accepted` spec without it.*

*One convention is fixed NOW, because it is easier to adopt than to
retrofit: **rounds with 0022 will be COUPLED, so counts will have TWO
BASES** — the PER-ROUND count (how many distinct findings a round's report
raised, which is what the verbatim report says) and the PER-SPEC count
(`specs/reviews.py` sums per spec, and a finding landing on both specs is
recorded in both rows, so the per-spec totals are necessarily larger). No
single number is "the" count; the round reports are authoritative for what
was raised and this table for what closed it.)*

| round | finding | class | owner | disposition | evidence |
|---|---|---|---|---|---|
| — | *no review rounds yet (draft)* | — | — | — | — |
