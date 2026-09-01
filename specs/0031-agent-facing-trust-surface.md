# Feature spec: the agent-facing trust surface

Spec-Status: draft

| | |
|---|---|
| **Version** | **v6** — round-1 external fold (RETURN, six blocking findings). **F1**: V-NO-RAISE was stated on the whole trust model and CHECKED on one coordinate; §2c now enumerates the product's four consumers and §2c-i replaces the six-row matrix with a LATTICE statement — under `none` the baseline is the bottom element of the sublattice these legs reach, so restrict-only is INERT there and meaningful exactly and only under `direct`. v5's "lateral" claim for `THIRD_PARTY`→`ASSISTANT` is RETRACTED (§4a): lateral on disclosure, a raise on authority. **F2**: `author` was a model-supplied argument DEFAULTING TO THE TOP OF THE LADDER, masked today by the derived_from floor and UNMASKED by Phase A — the author default IS the elevation. Ruled against all three of the reviewer's options and against dev's lean: `author` loses its default and takes the CAPABILITY's baseline, restrict-only from there; and `direct` is amended to attest the authorship axis it was already unlocking, on the new rule that **an attestation may be untrusted but must not be unknowable** (§3a). **F3** capability pinned to concrete carriers, absence-vs-invalid taken verbatim. **F4/F5/F6** folded per the joint split. | **v5** — one addition on the owner's S2 ruling (2026-08-31), no mechanism change: §5 gains the ORDERING PRECONDITION that Phase A must not ship before the `valid_from` predicate lands. Phase A is what makes that predicate necessary rather than desirable — today a not-yet-valid edge is assertable but only via a HOST-SIDE write with attested capture (an MCP write floors to USE_ONLY: harness S2 + T4-3), and `capability=direct` removes exactly that mitigation, converting a host-only anomaly into an agent-reachable over-assertion. Phase A remains independent of 0029 and Phase B; this is its ONE external precondition. | **v4** — one addition to §6a on dev's re-read: the Phase B REVERSAL CASES are recorded as a stated DEBT (clean undo / scoped-reversal reaching a second edge / intervening-state refusal), owed and pinned model-free before Phase B's first run, with the reason for deferring given — *pin before THE RUN* (0027 R3-6), never *pin before the design settles*. Converts an unpinned surface from a gap a reviewer finds into an obligation the spec states. No other change from v3. | **v3** — reversal fold, on dev's option-(b) ruling. New **§4c-iii**: an applied resolution must be reversible, and the inverse data is **0029's, not this spec's** — Phase B DEPENDS on the transaction-time carrier rather than duplicating pre-state capture (agreement-by-coincidence between two carriers of one fact is the standing hazard). Three constraints: undo is a FORWARD journaled transition following 0022's reinstate pattern (history never un-happens); SCOPED to the applying `txn`, never expressible as a bare "revive edge X"; and FAIL-CLOSED on intervening state, refusing with a diff rather than cascading. Adds V-UNDO-FORWARD / V-UNDO-SCOPED / V-UNDO-FAILCLOSED. **The dependency lands on Phase B ONLY — Phase A ships alone, unchanged.** 0031 becomes V-RECON's SECOND CONSUMER (belongs in the seam manifest's S1). Prompted by AreevAI/areev shipping "every apply stores its inverse" (competitive triage 2026-08-31). | **v2** — dev internal-review fold. **D-1** the capability composes with AUTHOR and never overrides it (author/relation/revocation rows added to §3), plus new **§3a** reconciling the capability→`EvidenceContext` bridge with 0011's explicit refusal to mint `direct()` by omission (`__init__.py:361`) — minting by DECLARATION is not minting by OMISSION, and the per-event→deployment widening is stated as the honest cost. **D-2** the proposal carrier PINNED at DDL level (new §4b-ii) with the schema-version ordering dependency on 0029 left deliberately unresolved, and the erasure gap closed (V-ERASE-PROPOSALS). **D-3** both carriers named: `mcp_max_open_proposals` (default 32, range 1–256, refuses rather than evicts) and `provenance_raises_discarded` (stripped operator counter). §1 additionally carries the LIVE Bedrock evidence for T4-3. | **v1** — first candidate. Folds two owner rulings taken 2026-08-31 on measured evidence: decision 1 (MCP provenance self-attestation → option **c**, host-attested capability) and decision 2 (trust verbs → `forget`/`correct`/`confirm` not agent-exposed; `dispute` proposal-form only). Both resolve to ONE principle — **the host attests, the model proposes** — which is why they are one spec with two separable phases. |
| **Author / session** | research (veracium-research); adopted by dev (v4 2026-08-31 internal cycle; v5 the S2 ordering precondition; v6 = the round-1 fold — adopted 2026-09-01, the round-2 pin) |
| **Evidence** | harness Tier 5 (`cases/tier45_manifest.json` v1.1) and Tier 6 (`cases/verbs_manifest.json` v1.0), both frozen with expectations pre-committed before their first run, both model-free. Every behavioural claim below is MEASURED, and §9 names the two places measurement corrected the reasoning. |

### Spec-Requires (accepted specs this consumes)

0011 §4d/§4e (`EvidenceContext`, the absent-context floor, `CorrectionAuthorisation`),
0008 (confirmation), 0026 §3b/§3c (the restrict-only relay floor — the design
precedent this spec generalises), 0023 §4a (quarantine-at-birth), 0022 (revocation).

**Phase B additionally requires 0029** (transaction-time carrier) for §4c-iii's
reversal — see there for why the inverse data is 0029's and not this spec's.
**The dependency lands on Phase B ONLY: Phase A ships alone, unchanged.**

**ORDERING DEPENDENCY — deliberately NOT listed above (round-1 F6).** Phase A's
`valid_from` precondition (§5) is an **owner ruling of 2026-08-31, not an
accepted spec**: there is no `valid_from`-predicate spec in `specs/` — verified,
not assumed — so it cannot be cited as a canonical `Spec-Requires` entry and
this spec does not pretend otherwise. It is a formal ordering dependency with a
named owner, a named acceptance instrument (harness Tier 7 case S2, frozen), and
no accepted specification yet. **Phase A is not acceptable until that spec
exists, is accepted, and lands.** Recorded here as an unmet obligation rather
than as a satisfied citation, because the failure mode this spec keeps finding
in others is a dependency that reads as discharged when it is not.

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

*(This measured line is PRE-Phase-A. Under §4a it becomes
`author=third_party derived_from=third_party` — same disclosure, same
assertability, different stored author, because `author`'s default is removed.
Flagged here rather than only in §6a: a spec that prints a measurement its own
design invalidates must say so at the measurement.)*

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

> **A model-supplied trust argument may only move the event DOWN in the trust
> product. It may never raise it on ANY coordinate.**

This is not new machinery — it is 0026 §3b's restrict-only floor generalised
from the relay lexicon to the whole agent-facing surface. But v5 stated the rule
over the whole trust model and then **checked it on one coordinate**, which is
round-1 F1 and is corrected here.

**The product, enumerated.** `derived_from` and `author` are read by more than
`_disclosure_for`, so a value that is neutral on disclosure can still be a raise:

| coordinate | consumer | read at |
|---|---|---|
| disclosure | `_disclosure_for` | `ingest.py:141-158` |
| supersession authority | `effective` / `permitted` / `edge_effective` | `authority.py:53-82` |
| plan staleness (CAS token) | `scope_fingerprint` | `authority.py:86-102` |
| scope redaction | `ScopeView`'s unset-`derived_from` fill | `scope_read.py:387-388` |

The reviewer's counterexample is the **authority** coordinate. Under `none` the
third-party floor scores `min(3, 0) = 0`; a model-declared `assistant` scores
`min(3, 1) = 1`. That is a RAISE, with disclosure `use_only` on both sides — so
the declaration buys the power to retire assistant-authority material the floor
could not touch. The `min` in `effective` is exactly what makes this a PRODUCT
rather than two independent axes.

`author` already fails closed on an unrecognised value (`_AUTHOR`, `"system"`
deliberately absent); v5 extended that discipline to `derived_from`, which fails
**open** in the raise direction, and stopped there. §4a now extends it to
`author`'s DEFAULT as well — see F2 there, where the default is the elevation.

### 2c-i. Restrict-only is meaningful under `direct` and INERT under `none`

The rule does not need to be enumerated per value, and enumerating it is how v5
got it wrong. It follows from where the two baselines sit:

- **Under `none` the baseline is the BOTTOM ELEMENT** of the sublattice these
  legs reach: author `third_party` with `derived(THIRD_PARTY)` — jointly
  minimal, `use_only` AND effective authority 0. Nothing below it is reachable
  from these legs: `QUARANTINED` is a **relation-leg** verdict, returned before
  either trust leg is consulted (`ingest.py:149-150`), and §3 leaves the relation
  leg untouched. So under `none` there is **no restricting direction to move
  in** — every non-identity model-supplied value on either leg is a raise on at
  least one coordinate.
  **Therefore under `none`, `author` and `derived_from` are INERT:** accepted
  syntactically (the closed-set check still refuses an unrecognised value, and
  still RAISES rather than defaulting), then discarded and counted (§4d).
- **Under `direct` the baseline is the TOP** — author `user`, first-party
  capture — so every other closed-set value is a genuine descent on every
  coordinate, and restrict-only has real content.

So restrict-only is not a rule that happens to have no cases under `none`; it is
meaningful **exactly and only under `direct`**. That is a lattice statement
rather than a six-row matrix, which is the whole point of the correction: the
matrix drifted on a coordinate nobody re-checked, and the lattice cannot.

This also **subsumes** the reviewer's narrower remedy. He asked that under
`none`, `assistant` be "discarded or floored alongside `user`". Discarding it is
the consequence here, but derived from where the baseline sits rather than added
as a third row — so the next coordinate someone adds to the trust product is
covered without editing this section.

### 2c-ii. Assertions about reach — REQUIRED

- A model-supplied value cannot move the event UP on ANY coordinate of the
  trust product relative to the host capability's baseline (V-NO-RAISE) — the
  four coordinates are enumerated in §2c. *v5 said "cannot produce a class less
  restrictive", which names only disclosure; that phrasing IS F1, and it is
  corrected here rather than left as the one place the old reading survives.*
- Under `none`, no model-supplied value changes the stored record at all
  (V-INERT-UNDER-NONE, §2c-i).
- A proposal cannot change any edge's classification (V-INERT-PROPOSAL).
- There is no path from the MCP surface to a trust mutation (V-RESOLVE-HOST).

## 3. Trust-class matrix — REQUIRED, blocking

**Read §2c-i first: this table is a CONSEQUENCE of where the two baselines sit,
not an independent enumeration.** It is given because a reviewer wants the cells,
but if a cell here ever disagrees with §2c-i, **§2c-i is correct and this table
is the bug.** That is the exact direction v5's version failed in, so the
precedence is stated rather than left to be discovered again.

Both trust legs, both capabilities:

| capability | leg | model supplies | effective | why |
|---|---|---|---|---|
| `none` | — | nothing | author `third_party`, `derived(THIRD_PARTY)` | the baseline IS the bottom; today's behaviour, unchanged |
| `none` | `derived_from` | `"user"` | baseline | raise on both coordinates — discarded, counted |
| `none` | `derived_from` | `"assistant"` | baseline | **raise on AUTHORITY** (0 → 1) though disclosure is unchanged — discarded, counted (**F1**) |
| `none` | `derived_from` | `"third_party"` | baseline | identity |
| `none` | `author` | `"user"` | baseline | raise — discarded. **This is today's DEFAULT** (**F2**) |
| `none` | `author` | `"assistant"` | baseline | raise on authority (0 → 1) — discarded, counted |
| `none` | `author` | `"third_party"` | baseline | identity |
| `direct` | — | nothing | author `user`, first-party capture | the host's attestation (§3a) |
| `direct` | `derived_from` | `"third_party"` / `"assistant"` | as declared | genuine descent on every coordinate — honoured |
| `direct` | `derived_from` | `"user"` | as declared | identity — a no-op restatement of the host's own attestation |
| `direct` | `author` | `"third_party"` / `"assistant"` | as declared | genuine descent — honoured; the model knows better than a blanket attestation |
| `direct` | `author` | `"user"` | identity | the attested baseline, restated |

**D-1 AMENDED (F2).** v5 said the capability *composes with* `author` and never
overrides it. That was true while `author` carried its own model-supplied
default — and that default was the bug. Under §4a the capability **supplies the
author baseline**, so the two legs are no longer independent: one attestation
sets both, and the model may descend from it on either. The min-capping in
`_disclosure_for` and `effective` is untouched and still does all the capping;
what changed is where the legs' STARTING POINT comes from. Stating the amendment
rather than quietly rewriting it, because D-1 was dev's round-2 finding and a
fold that silently reverses a prior round's fix is how a spec loses its history.

The relation leg is untouched by this spec, in both capabilities:

| capability | relation | class |
|---|---|---|
| any | `third_party_claim` | `QUARANTINED` — checked FIRST, before either trust leg (`ingest.py:149-150`) |
| any | any, source standing-revoked | `QUARANTINED` — 0023 quarantine-at-birth, applied AFTER and unaffected |

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

**What `direct` attests is BOTH AXES, and v5 got this wrong (F2).** v5 said the
capability attests CAPTURE and "explicitly not authorship". But `MENTIONABLE`
requires an authorship claim — `_disclosure_for` reads the author leg FIRST
(`ingest.py:151`) — so v5's `direct` attested something insufficient for the
class it unlocked, and left the gap to be filled by a model-supplied `author`
defaulting to the top. The fix is not to weaken `direct`; it is to make it
attest the axis it was already relying on, and to say so.

**The test this spec now carries: an attestation may be UNTRUSTED; it must not
be UNKNOWABLE.** §8 already accepts that a host declaring `direct` might be
LYING — that is where the trust boundary belongs, deliberately. It cannot accept
a host that CANNOT KNOW: per-event authorship is not available to a stdio
deployment at all (§4e), so a per-event authorship attestation would be unsound
**even from a perfectly honest host**, and unsoundness is not a trust boundary,
it is a bug. `direct` is therefore defined at DEPLOYMENT grain as:

> every call on this server originates in a turn with the authenticated
> principal, **and the deployment accepts the model's authorship labelling as
> its own**.

Liability, not clairvoyance — which is knowable to the declaring party, and that
is the test. A deployment unwilling to stand behind its agent's labelling must
leave the default, which is the same instruction §3a already gave, now with a
stated reason rather than an intuition.

The capability is a property of the **deployment**, declared once at server
construction. It is not per-call and not model-reachable.

## 3b. Authorization and scope — full specs only

Phase B introduces no new privileged path. Resolving a proposal calls the
**existing** host verb with the host's own authenticated principal, so
`CorrectionAuthorisation` and supersession authority apply exactly as they do
today. That is the point: the agent's reach ends at *proposing*.

## 4. Behaviour

### 4a. Phase A — the host attestation capability

#### The capability, PINNED (F3)

v5 named the capability and never named its carrier. Pinned, concretely:

| what | pin |
|---|---|
| type | `class HostCapability(str, Enum): NONE = "none"; DIRECT = "direct"` in `mcp_server.py`, beside `_AUTHOR` |
| constructor | `build_server(mem, *, default_user, capability=None)` — keyword-only; `None` means ABSENT |
| env mapping | `VERACIUM_MCP_CAPABILITY`, read in `main()` beside the existing `VERACIUM_USER` (`mcp_server.py:252`) |
| tool-schema exclusion | **by construction, not by filtering** — `capability` is a parameter of `build_server`, never of the `@server.tool()` functions, and those signatures are what the framework reflects into the tool schema. There is no capability argument for a model to supply because none exists |
| resolution | `None` → `HostCapability.NONE`; anything else → `HostCapability(value)`, which raises on any value outside the closed set |

**Absence vs. invalid — v5 was self-contradictory and the reviewer is right
(F3).** v5 said an "omitted, malformed, or unrecognised capability resolves to
`none`, and a malformed one RAISES", which cannot both be true, and the
unrecognised-resolves-to-`none` half is wrong by this project's own closed-set
discipline — an unknown member of a closed set IS malformed. The rule, taken
verbatim from the verdict:

> **Only ABSENCE defaults to `none`. Every SUPPLIED invalid value raises.**

So a configuration typo can never silently change behaviour: a deployment that
meant to attest and mistyped it fails at construction instead of running
un-attested while believing it is attesting. Note the empty string is a
**supplied** value and therefore raises — an empty `VERACIUM_MCP_CAPABILITY` is
a typo, not an absence. Enforcement is the `HostCapability(value)` call itself,
so there is no second validator to drift out of step with the enum (`config.py`'s
`validate_semantic` earned that lesson: one validator, every call site).

#### `author` loses its default (F2)

`author` is today a model-supplied argument **defaulting to `"user"`**, the top
of the ladder (`mcp_server.py:47` and `:152`). Under Phase A:

- **Absent `author` resolves to the CAPABILITY's baseline**, never to `"user"`:
  `third_party` under `none`, `user` under `direct`. Both trust legs now draw
  their baseline from the same single carrier as the attestation itself.
- **Supplied `author` is restrict-only** against that baseline, exactly as
  `derived_from` is, with the closed-set check and its fail-closed raise
  unchanged.

**Why this was invisible until now, and why that matters more than the fix.**
Today the `author="user"` default contributes *nothing*: `_resolve_context(None,
None)` floors `derived_from` to `THIRD_PARTY`, `effective` mins to 0, and
`_disclosure_for` returns `USE_ONLY` on the derived_from leg. The default is
**masked**. Phase A moves that floor — and unmasks it. This is the round-5 law
of the 0029/0030 arc firing on this spec: *a fix that reassigns authority
creates a new pair that nothing binds.* The pair is `(capability,
author-default)`, and nothing in v5 bound it. Third instance of the law, and the
first found by someone other than its author.

**The baseline author under `none` is `third_party`, and `assistant` was
considered and refused.** `assistant` is arguably the more literal description —
the model does author the tool call. But it scores authority **1**, not 0, and
would be dragged to 0 only by the `derived_from` floor's `min`. That is a value
that is safe *because something else is currently masking it* — precisely the
structure that produced F2. A baseline must be jointly minimal on its own, so
`third_party` it is.

#### The two lattices, and why v5 conflated them

**The DISCLOSURE lattice is two-valued, not three** — verified in
`_disclosure_for`: `THIRD_PARTY` and `ASSISTANT` both yield `USE_ONLY`, so for
"may this be volunteered" they are the SAME level:

```
    {THIRD_PARTY, ASSISTANT}  ->  USE_ONLY     (restrictive)
    first-party / attested    ->  MENTIONABLE  (permissive)
```

That observation is correct, it is load-bearing — **and it is what caused F1.**
The disclosure lattice is two-valued; the **authority ladder is four-valued**
(`USER 3 > SYSTEM 2 > ASSISTANT 1 > THIRD_PARTY 0`). Reasoning about a pair of
coordinates while only one lattice is in view is the whole bug, and it produced
this sentence, now **RETRACTED**:

> ~~A declaration that swaps `THIRD_PARTY` for `ASSISTANT` is lateral — it
> changes the recorded content class (which is real, and kept) without changing
> disclosure.~~

It is lateral on disclosure and a **raise on authority**. It is not kept: under
`none` it is discarded and counted (§2c-i).

**If the model's claim is worth recording, it needs a different carrier.** The
instinct behind "which is real, and kept" was not silly — a model reporting
"this came from the assistant" may well be telling the truth, and throwing it
away loses information. But `Provenance.derived_from` **is the trust lever**;
one cannot keep the record there and refuse its effect. Recording it would
require a non-trust-bearing carrier (an episode annotation, or a
`claimed_derived_from` field read by nothing that decides), which is new
substrate this spec does not spend. Named here as a deliberate open option
(§10.5) rather than silently dropped, because the reviewer should see that the
information loss was priced rather than overlooked.

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
is a deferred choice, and deferred choices cost a review round. v5 pinned a
shape; round-1 **F4** showed the pin was **comments, not constraints** — the
reviewer EXECUTED it and it accepted six rows it forbids in prose. Co-designed
with dev (the `CurrentState` precedent), the carrier is now two tables: the
proposal row holds current state under compare-and-set, and resolutions are
**append-only history** — the 0029 pattern where state changes are rows, not
rewrites.

```sql
CREATE TABLE mcp_proposal (
    user_id      TEXT NOT NULL,
    id           TEXT NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN ('dispute','correction')),
    proposer     TEXT NOT NULL CHECK (proposer = 'model'),
    target_edge_id      TEXT NOT NULL,
    target_state_digest TEXT NOT NULL CHECK (length(target_state_digest) = 64),
    correction_payload  TEXT CHECK (
        (kind = 'dispute'    AND correction_payload IS NULL) OR
        (kind = 'correction' AND correction_payload IS NOT NULL
                             AND length(correction_payload) <= 4096)),
    claim        TEXT CHECK (
        (kind = 'dispute'    AND claim IS NULL) OR
        (kind = 'correction' AND claim IS NOT NULL
                             AND claim IN ('error','change'))),
    evidence_ref TEXT CHECK (evidence_ref IS NULL
                             OR length(evidence_ref) BETWEEN 1 AND 512),
    note         TEXT CHECK (note IS NULL OR length(note) <= 4096),
    created_at   TEXT NOT NULL,
    expires_at   TEXT NOT NULL,
    state        TEXT NOT NULL DEFAULT 'open'
                 CHECK (state IN ('open','accepted','refused','expired')),
    resolved_at  TEXT,
    applied_txn  INTEGER,
    CHECK ((state = 'open'     AND resolved_at IS NULL     AND applied_txn IS NULL) OR
           (state = 'accepted' AND resolved_at IS NOT NULL AND applied_txn IS NOT NULL) OR
           (state IN ('refused','expired')
                              AND resolved_at IS NOT NULL AND applied_txn IS NULL)),
    PRIMARY KEY (user_id, id)
);

CREATE TABLE mcp_proposal_resolution (      -- APPEND-ONLY; no UPDATE path exists
    user_id      TEXT NOT NULL,
    proposal_id  TEXT NOT NULL,
    seq          INTEGER NOT NULL,
    action       TEXT NOT NULL CHECK (action IN ('accept','refuse','expire','reverse')),
    at           TEXT NOT NULL,
    applied_txn  INTEGER,
    reversal_txn INTEGER,
    CHECK ((action = 'accept'  AND applied_txn IS NOT NULL AND reversal_txn IS NULL) OR
           (action = 'reverse' AND applied_txn IS NULL     AND reversal_txn IS NOT NULL) OR
           (action IN ('refuse','expire')
                                AND applied_txn IS NULL    AND reversal_txn IS NULL)),
    PRIMARY KEY (user_id, proposal_id, seq)
);
```

- **`target_state_digest`** — sha256 of the target's canonical serialization at
  proposal time. Stale-proposal detection, and it is **V-RECON's serialization
  doing double duty** rather than a second definition of "the same edge".
- **EVERY `CHECK` over a nullable column must state its NULL case explicitly,
  because NULL never fails a naive CHECK.** SQL is three-valued: `NULL IN
  ('error','change')` evaluates to NULL, and a `CHECK` refuses only on FALSE —
  so a constraint can exist, look right, and silently admit the exact row it was
  written to forbid. Found by EXECUTION, not by reading: the first draft of the
  `claim` constraint accepted a `correction` with `claim IS NULL`, which is the
  one case the column exists to require. This is "comments are not schema
  constraints" (F4) one level down — *a constraint that exists but is NULL-blind*
  — and it is the same shape as the reviewer's own row 5. **The remaining seven
  CHECKs were audited against NULL-fed rows and all refuse correctly**, because
  each already branches on `IS NULL` / `IS NOT NULL`; the `claim` draft was the
  only one that let a bare `IN` carry the requirement.
- **`claim` is a CLOSED DOMAIN with a VERB MAPPING**, which is the reviewer's
  F4 bullet and the carrier for §1's second problem. Without it the spec keeps
  its motivation and loses its mechanism:

  | `claim` | means | verb executed on accept | resulting reason |
  |---|---|---|---|
  | `'error'` | the prior was never true | `Memory.correct` (`__init__.py:1573`) | `corrected` (`schema.py:409`, disposition `drop`) |
  | `'change'` | the prior was true and changed | the ordinary write path | `superseded` |

- **`proposer` is a one-valued CHECK today** (`'model'`), which is deliberate and
  not an oversight: it refuses the reviewer's `proposer='user'` row at the
  schema, keeps the row self-describing in an export, and is the column that
  WIDENS when an authenticated transport arrives (§4e). It is construction-
  derived and is not a tool argument.
- **Reversal identity/state lives in the resolution table, not on the proposal
  row.** `reverse` is a resolution EVENT: an accepted-then-reversed proposal is
  two rows. The proposal row's state stays `accepted`, because **the acceptance
  happened** — a reversal forward-undoes its effects and does not un-happen it
  (§4c-iii's doctrine, now expressed in the carrier rather than asserted beside
  it).
- **What the schema does NOT enforce, stated rather than left to be found.**
  The DDL cannot express "an `action='reverse'` row requires a prior
  `action='accept'` row for the same proposal". That is enforced by schedule 4
  (§4c-i), which reads `applied_txn` and refuses without it. Named explicitly
  because "comments are not schema constraints" cuts both ways: an obligation
  discharged by a schedule rather than a constraint must SAY which schedule, or
  it is the same defect facing the other way.
- **Schema implication:** an additive version bump with the full 0013/0018
  registration obligations (accepted-shape matrix, constructor + every migrated
  form). Shipped `SCHEMA_VERSION` is **12**; 0029 claims 13, so this is **14 if
  0029 lands first and 13 if it does not** — an ordering dependency, deliberately
  not resolved to a number here, because guessing it is how two specs claim one
  version.
- **V-ERASE-PROPOSALS:** proposals are USER DATA. `forget_user` must delete a
  user's rows from **both** tables in the SAME transaction as the edges — the
  0027/0029 V-ERASE pattern, on two tables now rather than one. Erasure totality
  lands in exactly one place: `forget_user`'s literal table tuple
  (sqlite.py:1769-1774), the same single point 0029's `edge_event` lands in.

### 4c. Resolution — differentiated by blast radius (F5)

v5 specified `resolve_proposal(user_id, proposal_id, *, accept: bool, actor)`.
That is **precisely the one undifferentiated acceptance action §4c-ii Q6
forbids** — this spec's own rule, contradicted by this spec's own API, four
sections apart. Corrected: there is no `accept: bool` and no single accept
entry point.

| operation | signature | friction |
|---|---|---|
| refuse | `refuse_proposal(user_id, proposal_id, *, actor, expected_state)` | none — refusal is the safe direction |
| accept a dispute | `accept_dispute(user_id, proposal_id, *, actor, expected_state)` | may be one action; measured blast radius is recoverable suppression |
| accept a correction | `accept_correction(user_id, proposal_id, *, actor, expected_state, acknowledged_value, acknowledged_claim)` | the resolver must **echo back** the value and the error-vs-change claim being approved; a mismatch REFUSES |
| expire | not an API — a host sweep over `expires_at` (schedule 2), terminal, never a path to `accepted` | — |

**The friction lives in the API's TYPE, not in the interface's manners.** This
is the load-bearing change, and the reason it belongs here rather than in a UI
note: §4c-ii Q6 asked a rendering surface to behave well, and a rendering
surface can ignore a document. It cannot ignore a required argument.
`accept_correction` **cannot be called** without reproducing the value and the
claim, so a one-click correction UI is not something this spec discourages — it
is something that cannot be built against this API. A `dispute` needs no such
echo, so the asymmetry the measurement bought (§1) is now an asymmetry in the
*type signature*.

`acknowledged_claim` closes a gap that echoing the value alone would leave: the
resolver must approve **which kind of history is being written**, since
`'error'` marks the displaced fact as never-having-been-true and `'change'` does
not. Approving a value without approving the claim approves half the mutation.

Every operation resolves through the **existing** host verb with the host's own
authenticated principal, so `CorrectionAuthorisation` and supersession authority
apply exactly as they do today. Resolution is the ONLY thing that mutates. An
unresolved proposal has no effect on any read surface but the proposal
inventory itself.

#### 4c-i. Atomic schedules — all four `BEGIN IMMEDIATE` (co-designed with dev)

The 0029 F4 discipline: take the writer lock **before any read that feeds a
decision**.

1. **PROPOSE** — `BEGIN IMMEDIATE` → count open proposals for the user → at the
   limit, typed refusal (refuse, never evict) → `INSERT` (schema-checked) →
   `COMMIT`. Count and insert share the lock, so two instances cannot both see
   room for the last slot.
2. **RESOLVE** (refuse / expire) — `BEGIN IMMEDIATE` → CAS `... WHERE state =
   'open'` → `changes() = 0` ⇒ typed ALREADY-RESOLVED refusal → append the
   resolution row → `COMMIT`. Expiry racing a refusal resolves atomically one
   way or the other; there is no third outcome and no silent double-resolve.
3. **ACCEPT-AND-APPLY** — ONE transaction end to end: `BEGIN IMMEDIATE` →
   recompute the target's live digest, mismatch ⇒ typed STALE refusal with zero
   writes → allocate `txn` → apply the host verb's writes and their journal
   events → CAS `open` → `accepted` with `applied_txn` → append the resolution
   row → `COMMIT`. The reviewer's "a committed correction remains recorded as
   open" is **unrepresentable**: the mutation and the state flip share one
   commit.
4. **REVERSE** — `BEGIN IMMEDIATE` → for every edge of `applied_txn`, compare
   the live serialization against the journal's post-apply state → any mismatch
   ⇒ typed INTERVENING-STATE refusal carrying the diff, zero writes → forward
   events under a new `txn` → append the resolution row → `COMMIT`.

Each schedule is owed two-instance forced interleavings at implementation, with
the `DEFERRED` variant as its **negative control** — seam-model rule zero: every
assertion ships with the thing that makes it fail.

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
- **`mcp_proposal_ttl_hours`** — a `MemoryConfig` field, default **168** (7
  days), accepted range **1–8760**, the same default+range discipline. It fills
  `expires_at` at insert (store-minted, never caller-supplied) and is what
  schedule 2's sweep reads. The reviewer's F4 "expiry timestamp or lifetime
  policy" needs BOTH: the column is the timestamp, this is the policy.
- **`provenance_raises_discarded`** — the §4a discarded-raise counter, an
  OPERATOR counter, added to the existing strip list in `remember_impl`
  alongside `agreement_floored`/`agreement_recorded` (the 0015/0025/0026
  pattern). A model that learns how often its elevation attempts are refused
  learns to probe, so the count must never reach the tool result. Its
  operator-facing exposure is §10.4.

### 4e. What the transport can and cannot carry (F6) — REQUIRED

Phase B's attribution story must be buildable on the server that exists.
Enumerated from `mcp_server.py` as shipped, not from recollection:

**The facts.** The server is FastMCP over **stdio**, launched BY an MCP client,
one anonymous client per server process. **Every tool argument is
model-supplied** — `author`, `derived_from`, `date`, and `user_id` itself
(defaulting to `build_server`'s `default_user`). The framework exposes **no
authenticated caller identity and no turn identifier** to handlers. The
reviewer's "the available MCP server exposes no authenticated caller or turn
carrier" is exactly right, and it is **structural to stdio, not an omission** —
which is why the answer is to design around it rather than to file a bug.

**What this spec therefore commits to:**

1. **The host process IS the identity boundary.** Over stdio, identity is the
   deployment's construction-time configuration — one principal per server
   process. **`proposer` is derived from construction config, never a tool
   argument**, and it lives in the same place as the capability, so the two
   attestations share one carrier and one trust story.
2. **Model-supplied substitutes are forbidden BY SCHEMA, not by validation.** No
   `proposer`, turn, or identity parameter exists on the `propose` tool at all.
   Absence-by-construction is the same move that defeats §4c-ii Q2, and it is
   strictly stronger than rejecting a bad value: there is no value to reject.
3. **The originating-turn field is DROPPED from Phase B v1.** §4c-ii Q2 wants
   the resolver to see the turn a proposal arose from, and this transport cannot
   supply it truthfully. An unverifiable field inside a trust carrier invites
   exactly the misreading Q2 exists to prevent, so it is better absent than
   present-and-unlabelled. It returns with an authenticated transport.
4. **`evidence_ref` stays, as a REFERENCE the host looks up — never as trusted
   content.** The model may say where to look; it does not thereby say what is
   true.
5. **Multi-user-per-process deployments are OUT OF SCOPE for Phase B v1**, and
   this is stated rather than assumed away: over stdio the transport cannot
   distinguish callers, so `user_id` is deployment-scoped exactly as `remember`'s
   is. An authenticated transport (HTTP with auth) is future work with its own
   review round, and it is also where the reviewer's F2 options (a) a host-bound
   per-event author carrier and (b) a host-fed direct-ingress tool become
   available. **Both require an authenticated transport, which is why neither is
   a Phase A alternative** (§4a).

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
- **⚠ ORDERING PRECONDITION — Phase A must not ship before the `valid_from`
  predicate lands (owner-ruled 2026-08-31).** Phase A is what makes this
  necessary rather than merely desirable. Today an edge whose `valid_from` has
  not yet arrived is still assertable — `Edge.assertable` consults no time
  predicate — but reaching that state needs a HOST-SIDE write with attested
  direct capture, because an MCP write with no context floors to `USE_ONLY`
  (measured: harness Tier 7 / S2 and T4-3). **Phase A removes exactly that
  mitigation:** under `capability=direct`, MCP writes can reach `MENTIONABLE`,
  which converts a host-only anomaly into an agent-reachable over-assertion —
  an agent could assert, today, a fact that becomes true tomorrow. The owner
  has ruled the predicate closed separately (option (b)), sequenced after the
  0029/0030 round-3 archive and BEFORE this phase, with the frozen S2 case as
  its acceptance instrument. Phase A remains independent of 0029 and of Phase
  B; this is its one external precondition, and it exists because Phase A
  widens a surface that is currently narrow for an unrelated reason.

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | check |
|---|---|
| **V-NO-RAISE** no model-supplied value raises the event on ANY of the product's four coordinates — disclosure, supersession authority, `scope_fingerprint`, scope redaction; the raise is discarded and counted | `test_model_supplied_provenance_is_restrict_only_on_every_coordinate` |
| **V-INERT-UNDER-NONE** under `none`, EVERY supplied `author`/`derived_from` value leaves the stored record identical to the baseline — the case F1 was made of (`assistant` must not reach authority 1) | `test_none_baseline_is_the_bottom_element` |
| **V-AUTHOR-BASELINE** absent `author` resolves to the capability baseline and NEVER to `"user"`; the shipped default is gone | `test_author_has_no_default_of_its_own` |
| **V-CAP-DEFAULT** only ABSENCE resolves to `none`; EVERY supplied invalid value — including the empty string — raises at construction | `test_capability_absence_is_the_untrusted_cell` |
| **V-DDL-ENFORCED** the reviewer's six rows are refused BY THE SCHEMA and their six passing complements accepted, plus **C13: a `correction` with `claim IS NULL` is REFUSED** — thirteen executed cells, no comment doing a constraint's job and no CHECK blind to NULL | `test_proposal_ddl_refuses_and_accepts` |
| **V-CHECK-NULL-EXPLICIT** every `CHECK` over a nullable column is exercised with a NULL-fed row; a constraint that a NULL slips through is a defect, not a gap | `test_every_nullable_check_states_its_null_case` |
| **V-RESOLVE-DIFFERENTIATED** no API accepts a correction without `acknowledged_value` AND `acknowledged_claim`; no single call resolves both kinds | `test_no_undifferentiated_acceptance` |
| **V-ATOMIC** each of the four schedules holds under forced two-instance interleaving, with its `DEFERRED` variant as the negative control that fails | `test_schedules_are_serializable` |
| **V-INERT-PROPOSAL** a proposal changes no edge's disclosure/assertable/active/reason | `test_proposal_mutates_nothing` |
| **V-PROPOSAL-CLASS** a proposal's own content is never assertable | `test_proposal_is_not_a_fact` |
| **V-RESOLVE-HOST** no MCP path reaches a trust mutation; resolution runs the existing verb with the host principal | `test_no_mcp_path_to_trust_mutation` |
| **V-CLOSED-KIND** `confirm` and `forget` are not proposable; an unregistered kind refuses | `test_proposal_kinds_closed` |
| **V-UNDO-FORWARD** reversal emits NEW events; no event is rewritten or deleted; the journal shows both the apply and its reversal | `test_undo_is_forward_only` |
| **V-UNDO-SCOPED** reversal touches exactly the edges of the applying `txn`; no surface expresses a bare "revive edge X" | `test_undo_is_scoped_to_its_txn` |
| **V-UNDO-FAILCLOSED** any intervening change to a touched edge REFUSES the reversal and reports the diff; nothing cascades | `test_undo_refuses_on_intervening_state` |
| **V-ERASE-PROPOSALS** after `forget_user`, zero proposals for the user remain, in the SAME transaction as the edges | `test_forget_user_erases_proposals` |
| **V-QUEUE-BOUND** at `mcp_max_open_proposals` the surface refuses new proposals and evicts none | `test_proposal_queue_refuses_not_evicts` |
| **V-COMPAT** (NARROWED, F6) capability `none` + no proposals ⇒ every existing surface byte-identical **EXCEPT the two changes §6a requires**: P3-3's flip, and the stored `author_of_evidence` on an MCP write with no explicit author | `test_no_capability_behaviour_identical_except_the_required_flips` |

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
- **A SECOND required change, which v5 did not have and the reviewer did not
  ask for.** Removing `author`'s default (§4a) changes what is STORED, not only
  what is disclosed. Re-derived against the frozen manifest rather than
  reasoned about: of the 19 Tier 4/5 cases, exactly four are `mcp_remember`
  (P3-1, P3-2, P3-3, P3-5) and **all four supply `author` explicitly**, so the
  default's removal touches none of them mechanically. The case it does touch
  is the LIVE one, P1-1, which omits `author` — and §1's own measured Bedrock
  line, which is a printed fact in this spec. Under Phase A `none` that line
  becomes `author=third_party derived_from=third_party disclosure=use_only
  assertable=False`: same disclosure, same assertability, **different stored
  author**. V-COMPAT is narrowed to admit exactly this and P3-3, and no more.
- **P3-5's outcome does not change — and that is the problem.** v5 said "P3-5
  must NOT change; a fix that alters it would mean the floor moved, not the
  surface." The outcome indeed does not change. But under Phase A `none` both
  of its inputs (`author="user"`, `derived_from="user"`) are discarded raises,
  so the edge is `use_only` **from the baseline alone** — before the 0026 relay
  floor is consulted at all. P3-5 was written to prove the relay floor
  independently catches a self-attested edge; after Phase A its result is
  **over-determined**, and it would pass with the relay floor deleted. That is
  *a check that cannot fail is worse than no check*, this arc's own law, landing
  on this spec's own acceptance corpus.
  **Therefore P3-5 is owed a `capability=direct` variant**, pinned before the
  run, where the baseline IS mentionable and the relay floor is once again the
  only thing standing between the marker-bearing note and an assertable edge.
  Without that variant, Phase A silently retires a passing test's meaning while
  leaving it green — the worst of the available outcomes, because nothing
  reports it.
- **T4-1…T4-6, P2, P4, P5, P6 must not change at all** (V-COMPAT at case
  grain) — **scoped**, per the 0027 V10-oracle lesson (dev, round 2): the
  byte-identity claim holds for `capability=none`, no proposals declared,
  and `principal=None`. Stated rather than implied, because an unscoped
  byte-identity claim is either unfalsifiable or false at the first
  configuration that differs. These are all `ingest`-kind cases supplying an
  explicit author, so neither §4a change reaches them — checked against the
  manifest, not assumed.
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
5. **(new, F1)** Should a model's discarded `derived_from`/`author` claim be
   RECORDED in a non-trust-bearing carrier — an episode annotation, or a
   `claimed_*` field read by nothing that decides — so the information is kept
   without the lever? §4a prices the loss; this asks whether to spend the
   substrate. Deliberately not answered here: it is new substrate, and the fold
   that needed it is complete without it.
