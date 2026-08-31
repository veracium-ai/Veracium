# Feature spec: the agent-facing trust surface

Spec-Status: draft

| | |
|---|---|
| **Version** | **v4** — one addition to §6a on dev's re-read: the Phase B REVERSAL CASES are recorded as a stated DEBT (clean undo / scoped-reversal reaching a second edge / intervening-state refusal), owed and pinned model-free before Phase B's first run, with the reason for deferring given — *pin before THE RUN* (0027 R3-6), never *pin before the design settles*. Converts an unpinned surface from a gap a reviewer finds into an obligation the spec states. No other change from v3. | **v3** — reversal fold, on dev's option-(b) ruling. New **§4c-iii**: an applied resolution must be reversible, and the inverse data is **0029's, not this spec's** — Phase B DEPENDS on the transaction-time carrier rather than duplicating pre-state capture (agreement-by-coincidence between two carriers of one fact is the standing hazard). Three constraints: undo is a FORWARD journaled transition following 0022's reinstate pattern (history never un-happens); SCOPED to the applying `txn`, never expressible as a bare "revive edge X"; and FAIL-CLOSED on intervening state, refusing with a diff rather than cascading. Adds V-UNDO-FORWARD / V-UNDO-SCOPED / V-UNDO-FAILCLOSED. **The dependency lands on Phase B ONLY — Phase A ships alone, unchanged.** 0031 becomes V-RECON's SECOND CONSUMER (belongs in the seam manifest's S1). Prompted by AreevAI/areev shipping "every apply stores its inverse" (competitive triage 2026-08-31). | **v2** — dev internal-review fold. **D-1** the capability composes with AUTHOR and never overrides it (author/relation/revocation rows added to §3), plus new **§3a** reconciling the capability→`EvidenceContext` bridge with 0011's explicit refusal to mint `direct()` by omission (`__init__.py:361`) — minting by DECLARATION is not minting by OMISSION, and the per-event→deployment widening is stated as the honest cost. **D-2** the proposal carrier PINNED at DDL level (new §4b-ii) with the schema-version ordering dependency on 0029 left deliberately unresolved, and the erasure gap closed (V-ERASE-PROPOSALS). **D-3** both carriers named: `mcp_max_open_proposals` (default 32, range 1–256, refuses rather than evicts) and `provenance_raises_discarded` (stripped operator counter). §1 additionally carries the LIVE Bedrock evidence for T4-3. | **v1** — first candidate. Folds two owner rulings taken 2026-08-31 on measured evidence: decision 1 (MCP provenance self-attestation → option **c**, host-attested capability) and decision 2 (trust verbs → `forget`/`correct`/`confirm` not agent-exposed; `dispute` proposal-form only). Both resolve to ONE principle — **the host attests, the model proposes** — which is why they are one spec with two separable phases. |
| **Author / session** | research (veracium-research); adopted by dev 2026-08-31 at v4 (the internal cycle — dev's D-1/D-2/D-3, the option-(b) reversal ruling, the §6a debt sentence — closed from both seats before adoption) |
| **Evidence** | harness Tier 5 (`cases/tier45_manifest.json` v1.1) and Tier 6 (`cases/verbs_manifest.json` v1.0), both frozen with expectations pre-committed before their first run, both model-free. Every behavioural claim below is MEASURED, and §9 names the two places measurement corrected the reasoning. |

### Spec-Requires (accepted specs this consumes)

0011 §4d/§4e (`EvidenceContext`, the absent-context floor, `CorrectionAuthorisation`),
0008 (confirmation), 0026 §3b/§3c (the restrict-only relay floor — the design
precedent this spec generalises), 0023 §4a (quarantine-at-birth), 0022 (revocation).

**Phase B additionally requires 0029** (transaction-time carrier) for §4c-iii's
reversal — see there for why the inverse data is 0029's and not this spec's.
**The dependency lands on Phase B ONLY: Phase A ships alone, unchanged.**

---

## 1. Problem and motivation

Veracium's trust model assumes a **host**: a trusted application that
authenticates a principal, establishes intent, and declares where content came
from. Every trust-bearing input is designed to be settled by that host.

The MCP surface has no host in that sense. The party filling in the arguments
**is the model**. Two consequences, both measured rather than argued:

**(1) The absent-context floor is defeatable by the party it exists to
constrain.** `remember` over MCP passes no `EvidenceContext`, so
`_resolve_context(None, None)` returns the `derived(THIRD_PARTY)` floor and the
edge lands `USE_ONLY` — correct, and for the right reason: *"the party relaying
it cannot attest first-party capture."* But `derived_from` is an **optional
argument that same party controls**, and `_resolve_context` honours a declared
value as a positive declaration. Passing `derived_from="user"` therefore yields
a **MENTIONABLE, assertable** edge (harness P3-3, confirmed through
`remember_impl` itself). This is the exact shape the `author="system"` removal
was introduced to prevent — *"a trust-bearing field must not be settable by the
party whose trust it describes"* — left open on the adjacent field.

**Measured live, end to end, and it inverts the obvious reading of this
gap.** Running the agent tier on a real model (Bedrock, pinned
`us.anthropic.claude-haiku-4-5-20251001-v1:0`) against the product's own MCP
server: the agent is told *"Remember: my favorite color is blue"*, calls
`remember` with just the text, and the edge lands

```
    author=user   derived_from=third_party   disclosure=use_only   assertable=False
```

The agent did nothing wrong — it had no argument to pass that would have helped.
So **over the shipped MCP surface a user's OWN directly-stated fact is never
assertable, and `answer` will never volunteer it.** An agent-driven deployment
cannot produce a single MENTIONABLE fact.

That reframes the elevation gap above: `derived_from="user"` is **not merely an
exploit — it is the only way an agent can store an assertable fact at all**,
which is why it exists. The consequence for this spec's design is decisive:
**removing the argument outright would leave the MCP surface permanently unable
to produce assertable facts.** The host-attested capability is therefore not
merely the safer option; it is the only one that leaves the surface FUNCTIONAL.
§9's remove-vs-restrict sequence is bounded by this: removal is an acceptable
INTERIM posture precisely because it changes nothing about what the surface can
already do, and it is not acceptable as an END STATE.

The gap is **bounded**, and the bound matters for scoping: the 0026 relay floor
is restrict-only and keyed on the marker, not on how `MENTIONABLE` was reached,
so marker-bearing relayed content is still floored back to `USE_ONLY` even under
self-attestation (harness P3-5, predicted before it was run). The exposed
surface is relayed content the extractor renders **without** a relay marker.

**(2) The error/change distinction is unreachable through the only interface an
agent has — and its absence writes false history.** Veracium separates
`corrected` (was never true) from `superseded` (changed); they carry different
retention dispositions and the 0028/0030 as-of machinery is built on the
distinction. Over MCP an agent can only *restate*, and restatement produces
`superseded`. So "no, I never worked at Acme — you got that wrong" is recorded
as *worked at Acme, then it changed*. That is not a limitation of the agent's
power; it is the store recording something that did not happen.

**What is NOT a problem, measured.** The verbs are not uniformly dangerous and
the risk is not what unaided intuition suggests:

| verb | marginal power over `remember` alone | measured |
|---|---|---|
| `confirm` | **none found** | refuses quarantined AND use_only store-side; cannot launder |
| `dispute` | **real** — converts accumulation into replacement on non-functional relations | reversible: the truth returns via `remember`. DoS, not data loss |
| `correct` | largest short of `forget` | both tested laundering paths HELD (relay floor; supersession authority) |
| `forget` | total | destroys quarantined evidence and superseded history — the audit trail itself |

The baseline that makes those *marginal* is that `remember` alone — already on
MCP — displaces any **functional** relation by restatement. An agent needs no
verb to replace a functional fact.

## 2. Field contracts touched

- `Provenance.disclosure` / `derived_from` — unchanged in meaning. What changes
  is **who may set them and in which direction**.
- No change to `Edge.assertable`, `DISPOSITIONED_REASONS`, or any classifier.
- New: a host **capability declaration** (Phase A) and a **proposal** record
  (Phase B). Neither is an edge and neither is extractor-reachable.

## 2c. Untrusted inputs — REQUIRED, blocking

Everything arriving over MCP is untrusted, including the arguments that describe
trust. The design rule this spec adds:

> **A model-supplied trust argument may only RESTRICT. It may never RAISE.**

This is not new machinery — it is 0026 §3b's restrict-only floor generalised
from the relay lexicon to the whole agent-facing surface. `author` already fails
closed on an unrecognised value (`_AUTHOR`, `"system"` deliberately absent);
this extends the same discipline to `derived_from`, which today fails **open**
in the raise direction.

### 2c-ii. Assertions about reach — REQUIRED

- A model-supplied value cannot produce a class less restrictive than the
  host capability's baseline (V-NO-RAISE).
- A proposal cannot change any edge's classification (V-INERT-PROPOSAL).
- There is no path from the MCP surface to a trust mutation (V-RESOLVE-HOST).

## 3. Trust-class matrix — REQUIRED, blocking

| capability | model declares | effective content class |
|---|---|---|
| `none` (DEFAULT) | nothing | `derived(THIRD_PARTY)` — today's behaviour, unchanged |
| `none` | `derived_from="user"` | `derived(THIRD_PARTY)` — **the raise is refused, not honoured** |
| `none` | `derived_from="third_party"` / `"assistant"` | as declared — a restriction, honoured |
| `direct` | nothing | first-party capture attested BY THE HOST |
| `direct` | `derived_from="third_party"` / `"assistant"` | as declared — the model knows better than the blanket attestation; a restriction, honoured |
| `direct` | `derived_from="user"` | first-party — a no-op restatement of the host's own attestation, not an elevation |

**The capability composes with AUTHOR, and never overrides it** (D-1). The
matrix above varies only `derived_from`; `_disclosure_for` min-caps on BOTH
legs, so the author rows must be stated or a reviewer will rightly ask what
`direct` means for a third-party-authored event:

| capability | author | relation | class |
|---|---|---|---|
| `direct` | `third_party` | ordinary | `USE_ONLY` — **the author leg still caps**; attestation is about CAPTURE, not about who authored the content |
| `direct` | `assistant` | ordinary | `USE_ONLY` — 0001 I11, unaffected |
| `direct` | any | `third_party_claim` | `QUARANTINED` — the relation leg is checked FIRST and is untouched by this spec |
| `direct` | any | any, source standing-revoked | `QUARANTINED` — 0023 quarantine-at-birth is applied AFTER and is unaffected |

The capability raises only the floor that ABSENCE OF DECLARATION imposes. It
moves nothing that a positive signal already decided.

### 3a. The capability → `EvidenceContext` bridge (D-1) — REQUIRED

This must be stated explicitly, because 0011 refused the adjacent thing in so
many words: `Memory.remember` *"deliberately does NOT mint `direct()` on the
caller's behalf: doing so would recreate trusted-by-omission one layer up"*
(`__init__.py:361`).

Phase A does mint `direct()` per call on this surface, so the reconciliation is
the whole design and belongs in the open:

- **What 0011 refused was minting by OMISSION** — the library silently treating
  an undeclared event as first-party because nobody said otherwise. That is
  trusted-by-omission and it stays refused: with no capability declared,
  absence still floors, exactly as today.
- **What Phase A adds is minting by DECLARATION** — an explicit, out-of-band,
  identifiable party asserting a property of its own deployment, defaulting to
  `none`. The trusted cell is entered by a declaration that can be pointed at,
  never by silence.
- **It IS a widening of granularity, and that is the honest cost.** 0011's
  `direct()` is a PER-EVENT positive ingress declaration; a deployment-level
  capability is a blanket claim that EVERY event on this surface is first-party
  captured. That is a strictly stronger claim than 0011's, and it is sound only
  where it is structurally true — a server embedded in the user's own client.
  A server behind a public agent must leave the default, and §8 records that
  this spec moves the attestation to the host without verifying the host.

The capability is a property of the **deployment**, declared once at server
construction. It is not per-call and not model-reachable.

## 3b. Authorization and scope — full specs only

Phase B introduces no new privileged path. Resolving a proposal calls the
**existing** host verb with the host's own authenticated principal, so
`CorrectionAuthorisation` and supersession authority apply exactly as they do
today. That is the point: the agent's reach ends at *proposing*.

## 4. Behaviour

### 4a. Phase A — the host attestation capability

A `capability` declared at MCP server construction, from a closed set
`{none, direct}`, defaulting to `none`. **Absence is never the trusted cell**
(the 0011 rule this spec inherits): an omitted, malformed, or unrecognised
capability resolves to `none`, and a malformed one RAISES at construction rather
than silently degrading — a deployment that meant to attest and typed it wrong
must not run un-attested and think it is attesting.

`derived_from` remains on the tool surface, restrict-only per §2c: it is
resolved against the capability's baseline and the MORE RESTRICTIVE of the two
wins.

**The lattice is TWO-VALUED, not three** — verified in `_disclosure_for`, and
worth stating because the natural assumption is wrong: `THIRD_PARTY` and
`ASSISTANT` both yield `USE_ONLY`, so for the purpose of "may this be
volunteered" they are the SAME level. The order is:

```
    {THIRD_PARTY, ASSISTANT}  ->  USE_ONLY     (restrictive)
    first-party / attested    ->  MENTIONABLE  (permissive)
```

So "restrict-only" has exactly one meaningful direction: a model-supplied value
may move an event from the permissive cell to the restrictive one, never back.
A declaration that swaps `THIRD_PARTY` for `ASSISTANT` is lateral — it changes
the recorded content class (which is real, and kept) without changing
disclosure. A model-supplied value that would move toward MENTIONABLE is
discarded, and the discard is counted (§4d).

### 4b. Phase B — proposed trust operations

One new MCP tool, `propose`, taking a kind from a CLOSED set and the target
edge id:

| kind | proposable | why |
|---|---|---|
| `dispute` | **yes** | reversible; measured blast radius is suppression, recoverable via `remember` |
| `correction` | **yes** — carries the corrected value AND the error-vs-change claim | this is the false-history fix; execution stays host-bound |
| `confirm` | **no** | measured marginal power: none. Cost without benefit, and it raises trust |
| `forget` | **no** | irreversible, whole-user, destroys the audit trail |

A proposal is a RECORD, not a mutation. It is inert: it changes no edge's
`disclosure`, `assertable`, `active`, or `invalidation_reason`. It is
agent-authored, so its own content is never assertable — a proposal is not a
fact, and must not become one by being stored.

### 4b-ii. The proposal record — the carrier, pinned (D-2)

0029's F5 lesson applies verbatim: a record whose shape is implied across prose
is a deferred choice, and deferred choices cost a review round. Pinned:

```sql
CREATE TABLE proposal (
    id           TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL,
    kind         TEXT NOT NULL,   -- CLOSED: 'dispute' | 'correction'
    target_edge  TEXT NOT NULL,
    payload      TEXT,            -- correction: the proposed value; dispute: NULL
    claim        TEXT,            -- correction only: the error-vs-change claim
    proposer     TEXT NOT NULL,   -- the agent principal; NEVER 'user'
    evidence_ref TEXT NOT NULL,   -- the turn this arose from (Q2's provenance)
    state        TEXT NOT NULL,   -- 'open' | 'accepted' | 'refused' | 'expired'
    created_at   TEXT NOT NULL,   -- store-minted, never caller-supplied (0029 §4c)
    resolved_at  TEXT,
    resolved_by  TEXT             -- the host principal that resolved it
);
CREATE INDEX ix_proposal_open ON proposal(user_id, state);
```

- `proposer` is never `user`: a proposal is an AGENT's claim, and Q2's
  authorship-confusion vector is defeated at the schema, not at the renderer.
- `expired` is a TERMINAL REFUSED state, per §4c-ii Q4 — never a path to
  `accepted`.
- **Schema implication:** an additive version bump with the full 0013/0018
  registration obligations (accepted-shape matrix, constructor + every migrated
  form). Shipped `SCHEMA_VERSION` is **12**; 0029 claims 13, so this is **14 if
  0029 lands first and 13 if it does not** — an ordering dependency, deliberately
  not resolved to a number here, because guessing it is how two specs claim one
  version.
- **V-ERASE-PROPOSALS (the gap D-2 names):** proposals are USER DATA.
  `forget_user` must delete a user's proposals in the SAME transaction as the
  edges — the 0027/0029 V-ERASE pattern, now owed on a third table. Erasure
  totality lands in exactly one place: `forget_user`'s literal table tuple
  (sqlite.py:1769-1774), the same single point 0029's `edge_event` lands in.

### 4c. Resolution

A host API `resolve_proposal(user_id, proposal_id, *, accept: bool, actor)`
executes the underlying verb through the existing path with the host's
principal, or records the refusal. Resolution is the ONLY thing that mutates.
An unresolved proposal has no effect on any read surface but the proposal
inventory itself.

### 4c-ii. The proposal queue is a social-engineering surface — REQUIRED, blocking

Phase B does not remove the trust lever; it **moves it to a human**. That human
is then reachable *through* the model, which is a surface this spec must own
rather than inherit. Raised by dev in round 2 as untested; this is the analysis.

The threat is not that a proposal executes itself — V-INERT-PROPOSAL forbids
that. It is that an attacker-controlled proposal is **rendered to a person whose
acceptance carries the host's authority**. Six vectors, and the design response
to each:

| # | vector | response |
|---|---|---|
| Q1 | The proposal's text is attacker-chosen and displayed to the resolver ("the user said their address is now …") | the queue MUST render proposal content as **quoted, attributed, untrusted material** — never in system voice. This is the recall-rendering distinction (content vs assertion) applied to a second surface |
| Q2 | **Authorship confusion** — the resolver reads "the user requests" when the truth is "the assistant proposes" | resolution MUST display the proposal's provenance: proposer, `evidence_ref`, and the turn it arose from. The resolver is deciding about an AGENT's claim, and must see that |
| Q3 | **Queue flooding / alert fatigue** — bury one hostile proposal among many plausible ones so the resolver rubber-stamps | a **bounded** number of open proposals per user. The absence of a cap IS the vulnerability; an unbounded queue is a fatigue weapon |
| Q4 | **Expiry-to-accept** — a proposal that times out is silently applied | expiry MUST refuse, never accept. **Fail closed** — this is the house rule and it settles §10's old lifetime question rather than leaving it open |
| Q5 | **Inert-but-visible** — even a never-accepted proposal delivers attacker text to a human. An inert record is still a DISPLAY surface | proposal content is subject to the same rendering discipline as quarantined content: it may be shown, never asserted, and never rendered as instruction |
| Q6 | **`correction` is strictly worse than `dispute`** — dispute only removes; correction *installs* attacker-chosen content under the resolver's authority | **friction proportional to blast radius**, which §1 measured: a `dispute` proposal may be one-click; a `correction` proposal MUST show the new value diffed against the current one, and MUST NOT be accepted by a single undifferentiated action |

Q6 is the load-bearing one. The measured asymmetry — `dispute` is reversible
suppression, `correction` installs a user-authored assertable fact AND marks the
displaced truth as never-having-been-true — should show up as an asymmetry in
the *interface*, not only in the docs. A design that makes both kinds one click
has thrown away the distinction the measurement bought.

**Limit, stated plainly:** none of §4c-ii is adjudicable by the harness. Every
other claim in this spec is measured against store state; these are
human-factors properties of a rendering surface, and the harness measures
neither humans nor rendering. They are design obligations carried on reasoning,
and they should be reviewed as such — §8 records this.

### 4c-iii. Reversal of an applied resolution — Phase B, DEPENDS ON 0029

An accepted proposal changes trust state, so it needs a defined way back.
§4c-ii Q1's social-engineering vector ends with a resolver who approved
something they should not have; a design that gates approval without providing
recovery has only relocated the failure, not answered it.

**The inverse data is 0029's, not this spec's.** Phase B DEPENDS on the
transaction-time carrier rather than storing its own inverse: every event
carries the edge's full canonical serialization, so a resolved correction's
inverse — the prior's pre-correction state — is in the journal **by
construction**. A 0031-local inverse store would be a second, weaker
implementation of exactly the property 0029 is in external review defending,
and agreement-by-coincidence between two carriers of one fact is the standing
hazard this line refuses. Share the function.

Sequencing is acceptable-to-good: 0029 is AHEAD of 0031 in review, the phases
were already designed separable, and **the dependency lands on Phase B only —
"Phase A ships alone" survives untouched** (§5).

Undo in this system is not restoring bytes. Three constraints:

**(1) Undo is a FORWARD, JOURNALED transition — never a rewrite.** Reversing a
resolution retires the installed replacement and revives the prior through NEW
events carrying their own `txn`, following 0022's reinstate pattern — the only
revival class this line permits — executed through a host API with the host
principal, exactly as resolution itself is. The journal records BOTH that the
correction happened and that it was reversed. **History never un-happens.**

**(2) SCOPED reversal, not generic revival.** The undo reverses exactly this
resolution's effects — the edges its apply touched, identified by the applying
transaction's `txn` — and nothing else. It MUST NOT be expressible as "revive
edge X". That lever is precisely what 0022/0023 exist to refuse, and offering
it here would reopen the non-revival guarantee through a new door.

**(3) FAIL CLOSED on intervening state.** If anything has built on the
replacement since the apply — a supersession, an absorption, a confirmation —
the touched edges' current serializations will not match the journal's
post-apply states, and the undo **REFUSES**, showing the resolver exactly what
changed so they can proceed through ordinary verbs with fresh judgment. **No
cascade rewrite, ever.** The journal's full-state payloads make this one
comparison per touched edge.

This makes 0031 the **second consumer of V-RECON**, which belongs in the joint
seam manifest's S1 alongside 0030's.

### 4d. Named carriers (D-3)

Two carriers get names here rather than at implementation, per house pattern:

- **`mcp_max_open_proposals`** — a `MemoryConfig` field, default **32**,
  accepted range **1–256** (the 0027 §4d default+range discipline). It bounds
  §4c-ii Q3's fatigue vector. On exceeding it the surface **refuses new
  proposals**; it never evicts old ones, because eviction is itself the attack
  (flood the queue to displace a pending correction).
- **`provenance_raises_discarded`** — the §4a discarded-raise counter, an
  OPERATOR counter, added to the existing strip list in `remember_impl`
  alongside `agreement_floored`/`agreement_recorded` (the 0015/0025/0026
  pattern). A model that learns how often its elevation attempts are refused
  learns to probe, so the count must never reach the tool result. Its
  operator-facing exposure is §10.4.

## 5. Regime analysis

- **Existing hosts, no capability declared:** byte-identical behaviour to today
  in every respect except that a model-supplied `derived_from="user"` stops
  raising. That IS a behaviour change and §7 owns it.
- **Embedded/first-party deployments:** declare `direct` and recover the
  mentionable class they legitimately had, now by host attestation rather than
  by the model's say-so.
- **Phase A without Phase B:** coherent and shippable. Closes the measured gap;
  leaves the false-history gap open.
- **Phase B now also requires 0029.** Phase A is unaffected and still ships
  alone; Phase B waits on the carrier rather than duplicating it (§4c-iii).
- **Phase B without Phase A:** NOT recommended — proposals would ride a surface
  whose provenance is still model-elevatable.

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | check |
|---|---|
| **V-NO-RAISE** no model-supplied value yields a class less restrictive than the capability baseline; the raise is discarded and counted | `test_model_supplied_provenance_is_restrict_only` |
| **V-CAP-DEFAULT** absent/unrecognised capability resolves to `none`; a MALFORMED one raises at construction | `test_capability_absence_is_the_untrusted_cell` |
| **V-INERT-PROPOSAL** a proposal changes no edge's disclosure/assertable/active/reason | `test_proposal_mutates_nothing` |
| **V-PROPOSAL-CLASS** a proposal's own content is never assertable | `test_proposal_is_not_a_fact` |
| **V-RESOLVE-HOST** no MCP path reaches a trust mutation; resolution runs the existing verb with the host principal | `test_no_mcp_path_to_trust_mutation` |
| **V-CLOSED-KIND** `confirm` and `forget` are not proposable; an unregistered kind refuses | `test_proposal_kinds_closed` |
| **V-UNDO-FORWARD** reversal emits NEW events; no event is rewritten or deleted; the journal shows both the apply and its reversal | `test_undo_is_forward_only` |
| **V-UNDO-SCOPED** reversal touches exactly the edges of the applying `txn`; no surface expresses a bare "revive edge X" | `test_undo_is_scoped_to_its_txn` |
| **V-UNDO-FAILCLOSED** any intervening change to a touched edge REFUSES the reversal and reports the diff; nothing cascades | `test_undo_refuses_on_intervening_state` |
| **V-ERASE-PROPOSALS** after `forget_user`, zero proposals for the user remain, in the SAME transaction as the edges | `test_forget_user_erases_proposals` |
| **V-QUEUE-BOUND** at `mcp_max_open_proposals` the surface refuses new proposals and evicts none | `test_proposal_queue_refuses_not_evicts` |
| **V-COMPAT** capability `none` + no proposals ⇒ every existing surface byte-identical | `test_no_capability_behaviour_identical` |

### 6a. Acceptance measurement — REQUIRED, FINITE

**The instrument already exists**, which is unusual and worth stating: the
acceptance corpus is the frozen harness manifests, and the decisive case is
already pinned.

- **P3-3 must FLIP.** `cases/tier45_manifest.json` v1.1 pins
  `derived_from="user"` over MCP producing `disclosure=mentionable,
  assertable=true`. Under capability `none` this must become
  `use_only`/not-assertable. The harness test that currently pins the finding
  (`test_p3_3_records_the_elevation_as_a_finding`) is written to fail loudly on
  exactly this change, so the finding is retired **on purpose**, not silently.
- **P3-5 must NOT change** — the relay floor already caught that cell; a fix
  that alters it would mean the floor moved, not the surface.
- **T4-1…T4-6, P2, P4, P5, P6 must not change at all** (V-COMPAT at case
  grain) — **scoped**, per the 0027 V10-oracle lesson (dev, round 2): the
  byte-identity claim holds for `capability=none`, no proposals declared,
  and `principal=None`. Stated rather than implied, because an unscoped
  byte-identity claim is either unfalsifiable or false at the first
  configuration that differs.
- **Tier 6 B-1/B-2 must not change** — the restatement baseline is unaffected.
- **P1b MUST BE RE-RUN under `capability=direct`, and this is a NEW obligation
  Phase A creates rather than inherits.** Today the absent-context floor means
  nothing stored over MCP can be MENTIONABLE, which bounds direct-injection's
  blast radius for free: even a fully successful injection lands `use_only`.
  Phase A removes that bound by design — under `direct`, content CAN be
  mentionable, so an injection that persuades the extractor now reaches an
  assertable class. **Phase A therefore raises P1's stakes**, and its
  acceptance must re-measure the vector it changes rather than rely on the
  pre-Phase-A result.
  Measured pre-Phase-A baseline to compare against (Haiku 4.5 via Bedrock):
  bare injection → 0 edges + an episode naming the attempt; embedded injection
  → the legitimate facts extracted, the injected claim landing nowhere.
- New Phase B cases pinned before first run, per house discipline.
- **DEBT, stated rather than left for a reviewer to find:** Phase B's reversal
  cases — a clean undo, a scoped-reversal attempt reaching for a second edge,
  and an intervening-state refusal — are **OWED**, and will be pinned model-free
  before Phase B's first run. They are deliberately NOT pinned now: the
  pre-commitment rule is *pin before THE RUN* (0027 R3-6), never *pin before the
  design settles*, and freezing expectations against a design still in motion
  would invert the discipline's purpose. The three named cases are the agreed
  skeleton, so the eventual manifest's shape is settled even though its values
  are not.

Pass criteria, pre-committed: P3-3 flips; every other frozen case is
byte-identical in outcome; the new Phase B cases meet their pinned expectations
100%.

## 7. Failure modes and reversibility

- **Reversible:** capability defaults to `none`; Phase B is additive. Removing
  Phase B drops proposals and returns today's surface.
- **Phase A widens the injection surface, by design.** The absent-context floor
  is currently doing double duty: it withholds trust the surface cannot
  attest, AND it incidentally caps what a successful prompt injection can
  achieve. Phase A keeps the first job and gives up the second. That is the
  correct trade — a surface that can never assert anything is not usable —
  but it must be stated, and it is why §6a makes re-running P1b an acceptance
  obligation rather than a nice-to-have.
- **The real risk is a silent restriction.** A deployment that legitimately had
  mentionable content via `derived_from="user"` will, after Phase A, start
  flooring to `use_only` until it declares `direct`. That is a **behaviour
  change on a live surface** and must be released as one — CHANGELOG, a
  migration note, and ideally the discarded-raise counter visible to operators
  so the condition is diagnosable rather than mysterious ("the assistant stopped
  volunteering things it used to know").
- **Not reversible:** nothing.

## 8. Claims and limits

- **Claimed:** after Phase A, no model-supplied value raises a content class.
- **Claimed:** after Phase B, an agent can surface a user's correction *as a
  correction* without the model holding any trust lever.
- **NOT claimed:** that a host declaring `direct` is telling the truth. This
  spec moves the attestation from the model to the host; it does not verify the
  host. That is deliberate and is where the trust boundary belongs.
- **NOT claimed:** that §4c-ii's proposal-queue protections are MEASURED.
  They are the one part of this spec carried on reasoning rather than
  evidence — human-factors properties of a rendering surface, which the
  harness (which reads store state) cannot adjudicate. Review them as
  design obligations, not as findings.
- **NOT claimed:** any measurement of how often an injected instruction
  persuades a model to misuse a surface. Everything measured here is blast
  radius given a call, not the probability of the call.

## 9. Brief for the external reviewer

Two places where measurement corrected this author's reasoning, offered because
they are the parts most likely to be wrong elsewhere:

1. I predicted `correct()` on a quarantined edge would SUCCEED — it guards on
   `active` only, with no `assertable` check like `confirm`'s — and called it a
   laundering path. It **refuses** under `supersession-authority-v2`: *"a bare
   self-assertion cannot retire this prior."* The guard is the supersession
   authority rule, not a precondition on the target's class. The risk table in
   §1 is the corrected version.
2. I first framed the verb exclusions as an unstated accident. Two of the four
   (`dispute`, `correct`) already carry explicit MCP-exclusion rulings in their
   docstrings. Phase B is therefore partly PROMOTE-TO-SPEC, not rule-from-scratch.

**Remove-vs-restrict has a temporal answer, and it is measured.** On today's
MCP surface `derived_from` is a **pure elevation lever**: every value was run
through `remember_impl` and only one changes disclosure.

| `derived_from` | disclosure | assertable | stored |
|---|---|---|---|
| *omitted* | `use_only` | no | `third_party` |
| `"third_party"` | `use_only` | no | `third_party` |
| `"assistant"` | `use_only` | no | `assistant` |
| `"user"` | **`mentionable`** | **yes** | `user` |

The documented value is **behaviourally identical to omitting the argument** —
the floor already achieves what the tool docstring asks the model to do. Only
`assistant` differs at all, and only in the stored record, not in disclosure.
So *removal* costs almost nothing NOW, because the baseline is already maximally
restrictive and there is nothing meaningful to restrict toward; and
*restrict-only* becomes meaningful precisely when Phase A's `direct` capability
makes the baseline permissive. The two options are not rivals — they are the
same policy before and after Phase A. This spec therefore recommends removal as
the interim posture and restrict-only as the Phase A design.

Sharpest remaining question for review: And is
`correction` safe to propose given that its *execution* still requires the host
principal — or does a proposal queue become a social-engineering surface against
the human who resolves it?

## 10. Open questions

1. Should the capability be finer than `{none, direct}` — e.g. per-tool, or
   carrying an expiry?
2. Does a resolved proposal need its own audit record distinct from the verb's
   existing episode?
3. ~~Proposal lifetime~~ — **settled in §4c-ii Q4: expiry REFUSES, never
   accepts.** What remains open is only whether the refusal needs its own
   disposition in `DISPOSITIONED_REASONS`' style, or is adequately covered by
   the proposal record's own terminal state.
4. Should the discarded-raise counter be exposed to operators (diagnosability)
   against the probing risk in §4d?
