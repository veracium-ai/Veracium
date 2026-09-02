# Feature spec: the agent-facing trust surface

Spec-Status: draft

| | |
|---|---|
| **Version** | **v10** — the round-4 external fold (RETURN, six findings; credited: checksums, candidate==adopted confirmed by the reviewer a THIRD consecutive time, the 33 cells, the 38-corpus run, the Q2 and digest repairs). **F1 (dev design):** the payload is TYPED — a JSON object of exactly `object`/`note`/`effective_date`, duplicate-refusing decoder (0030's discipline on a WRITE surface), unknown keys REFUSED with the 0030-contrast stated (persisted-read tolerance ≠ incoming-argument tolerance), presence conditioned on `claim` INSIDE the payload; parse authority at BOTH sites (propose under the writer lock; apply re-parses because persisted data rots); the constructions name their exact minting; `acknowledged_effective_date` joins the trio (REQUIRED iff change, REFUSED for dispute AND error — approving a backdated change without seeing the date was the residual half-approval); DDL gains `json_valid` with its honest limit stated. **F2 (dev design, pre-validated by execution):** the round-3 ownership table cited a §6a cross-table gate that EXISTED NOWHERE — the phantom-citation class in our own spec, the promising sentence our own. **V-RESOLUTION-LEDGER is now fenced SQL in §6a**, extract-at-test-time so the audit cannot drift from its promise; seven violation histories each fire exactly their clause; append-only-across-runs split PREVENTION (absence-by-API) / DETECTION (cross-run content-hash half, a Phase B acceptance obligation). **F3 (dev design):** THE AFFINITY RULE, PART TWO — COERCION, one trap further over again: affinity runs BEFORE every CHECK, so DDL predicates describe the STORED representation, never the caller's binding; `"7"` coerces in and passes typeof (executed both seats; STRICT changes nothing lossless — executed, not recalled; `True` binds as 1, so bool is excluded from int EXPLICITLY). The invariant SPLITS: DDL owns stored-representation domains (claims narrowed to non-coercible); the schedules own binding types via a pinned validation preamble. **F4 (dev design):** the FK obligation was UNDER-SCOPED — the constructor is not the only door. Connection-path INVENTORY (4 file-backed sites, 4 `:memory:` scratch) with the classifier CRITERION stated so the next site cannot be missed; the 0007 rider becomes a CENTRAL CONNECTION FACTORY (per-site pragmas are the one-carrier class as connection code); the sentinel's flip condition covers every inventoried path so partial enablement fails it; plus an inventory-completeness sweep, labeled as a sweep. **F5 (research):** the retired V-NO-RAISE umbrella was still LIVE at §2c-ii — the round-3 sweep hunted the PHRASE just fixed, not the SYMBOL being retired; a symbol retirement sweeps the symbol's name and classifies use-vs-mention. Zero uses remain; two mentions narrate the retirement. **F6 (research ruling):** the corpus claim is NARROWED, not bootstrapped — **source-contained, not execution-contained** — because vendoring platform-specific wheels (pydantic-core) makes "self-contained" true on the sealer's platform and silently false elsewhere: the same over-claim in better clothes. Receipt versions pinned; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; the claim stated identically in rerun.sh, the corpus README, and §6a. | **v9** — the round-3 external fold (RETURN, seven findings; credited: checksums, ASSERT-14's currency property confirmed independently AGAIN, the 24 cells, the one-carrier bridge). **THE ROUND'S SHAPE IS THE ONE-CARRIER CLASS, CAUGHT SHALLOW:** F1 = round-2's fix reached §2c and missed §2c-i + the matrix + the V-NO-RAISE invariant row (which contradicted V-OBLIGATIONS-SEPARATE two rows below it — one table, two rules); F2 = the turn-drop reached §4b-iii and §4e and missed the Q2 table row that MOTIVATED it; F4's residue = the verb-mapping table still said "the ordinary write path" after the constructions were pinned. All swept by grep-count this time, not by the next reviewer. **F1:** all residual descent-on-every-coordinate language removed; V-NO-RAISE REPLACED by four per-obligation invariants (V-DESCEND-DISCLOSURE, V-DESCEND-AUTHORITY, V-RESTRICT-SHAPING, V-FINGERPRINT-STABLE-OR-STALE — the last asserting NO ordering, because a digest has none). **F2:** Q2's row now names exactly what the resolver sees — stored content, kind, claim, proposer, unresolved `evidence_ref` — and nothing else. **F3 (dev design):** PROPOSE gains in-lock target existence/ownership validation and THE STORE-MINTED DIGEST — sha256 over the live canonical serialization read under the same writer lock; `target_state_digest` is never a tool argument, and stale-detection becomes sound by construction. **F4 (dev design):** `Store.apply_proposal` signature + input contract pinned (`acknowledged_*` required iff correction, refused for dispute); the THREE in-transaction constructions each name the plan machinery they ride; `'change'` requires the payload's effective date — a change without a date is refused, the error-vs-change distinction made operational. **F5 (dev design):** `applied_txn` EQUALITY written from one local variable in one commit (divergence unrepresentable, not audited-for); `seq` domain in DDL, allocation `MAX(seq)+1` under the writer lock, append-only by ABSENCE-BY-API with the owner named; the cross-table gate strengthened to exactly-one-accept + equality + gapless-monotone. **F6 (dev design):** THE TYPE-AFFINITY RULE, derived not enumerated — SQLite CHECKs on `length()`/`GLOB`/`BETWEEN` are BLOB-blind (`GLOB` on a BLOB is NULL; a 64-byte BLOB satisfies `length()=64`), `IN`-lists are safe by construction; every such predicate gains `typeof()`, every integer column gains typeof+domain. *The affinity trap is the NULL trap one type over* — we learned NULL-blindness for values in round 2 and not for types. FK evidence to be rewritten against the store's PINNED OPENING SEQUENCE (today's fact: `SqliteStore` reports `foreign_keys = 0`, which is WHY the cross-spec obligation on 0007's connection open exists). **F7:** normative digest citations are FULL SHA-256 values (an ellipsized digest is the location-index defect in digest form); the path is `corpus/` (the archive's name wins the two-carrier split); the corpus ships the `harness` package its drivers import, the exact source revisions the raw results identify, the pinned P3-6/P3-7 companion, and `corpus/rerun.sh` — one archive-local command reproducing the deterministic corpus. | **v8** — the round-2 external fold (RETURN, six findings). NOTE the reviewed artifact was the HELD first seal (`d0fce0a9…`, v6), dispatched before the hold cleared; no finding touches the P3-5 block, so all apply to v7 unchanged. **F1 — the four-coordinate "lattice" was OVERSTATED, and it was this author's over-generalisation:** v6 enumerated four CONSUMERS correctly and then asserted ONE monotone rule over all of them without asking whether each is ORDERED. `scope_fingerprint` is a sha256 equality digest (verified) — no top, no bottom, no direction — so "descend" there is not a false requirement but a MEANINGLESS one, which is worse because it cannot be tested. Replaced by FOUR SEPARATE OBLIGATIONS: descend-only on disclosure and on supersession authority; restrict-only on scope shaping; **preserve-or-invalidate** on the fingerprint. **F2 — the `direct` bridge was UNIMPLEMENTABLE against the shipped grammar.** `_resolve_context(direct(), <any value>)` raises `ValueError: pass EITHER context= OR the legacy derived_from=, not both — two declarations of one fact is a host bug` (reproduced independently). The refusal is right and the spec was wrong: v6 proposed on this surface exactly the two-carriers-for-one-fact it forbids everywhere else. Mapping PINNED — `direct`+absent → `direct()`; `direct`+supplied → `derived(X)`; `none` → the floor; never both. The restriction is honoured THROUGH the declaration, never beside it. **F3 — the identity boundary was asserted and unenforced:** `user_id` comes OFF the Phase A/B tool schemas (absence-by-schema, as for `proposer`), the exact `propose` signature is pinned, and Q2's display requirement is reconciled with §4e's dropped turn — the resolver sees stored content, kind, claim, proposer and an unresolved `evidence_ref`, never a turn that cannot be known. **F4/F5 co-designed with dev and code-verified:** `Memory.correct` commits its plan then writes its episode separately (two commits, uncomposable from outside), so `Store.apply_proposal` is pinned as the transaction-owning primitive, with an ADDITIVE in-transaction variant of `apply_supersession_plan` as its prerequisite; the DDL gains `resolver`, a foreign key with the `PRAGMA foreign_keys=ON` obligation (an unpragma'd FK is a comment wearing a constraint's clothes — the round-1 defect in a new costume), a hex digest CHECK, and an OWNERSHIP TABLE naming DDL vs schedule vs §6a gate for every invariant. **F6** the acceptance corpus ships in the package. | **v7** — ONE correction, no mechanism change, and the reason it needs a version at all is the point: v6's bytes were ADOPTED and sealed, then §6a's P3-5 disposition changed, so two different documents would otherwise both answer to "v6". **The correction:** v6 said the `capability=direct` variant is owed because after Phase A the relay floor would be "the only thing standing" and "nothing reports it". Both are WITHDRAWN — **P2-1** (host-side, `context=direct`, the same relay marker, expecting `use_only`) with **P2-2** as its marker-free control is the floor's standing guard; delete the floor and P2-1 fails. P3-5 loses its OWN discriminating power; the floor does not go untested. The variant is still owed, on the spec's own re-run reasoning: Phase A opens a NEW path to a mentionable baseline — the MCP surface — which P2-1 does not exercise. **Why it took a round trip:** the correction reached the README and never reached this file's adopted copy; two carriers of one fact, updated independently. Registered in `specs/withdrawn_phrases.py` so the phrasing cannot return unnoticed. | **v6** — round-1 external fold (RETURN, six blocking findings). **F1**: V-NO-RAISE was stated on the whole trust model and CHECKED on one coordinate; §2c now enumerates the product's four consumers and §2c-i replaces the six-row matrix with a LATTICE statement — under `none` the baseline is the bottom element of the sublattice these legs reach, so restrict-only is INERT there and meaningful exactly and only under `direct`. v5's "lateral" claim for `THIRD_PARTY`→`ASSISTANT` is RETRACTED (§4a): lateral on disclosure, a raise on authority. **F2**: `author` was a model-supplied argument DEFAULTING TO THE TOP OF THE LADDER, masked today by the derived_from floor and UNMASKED by Phase A — the author default IS the elevation. Ruled against all three of the reviewer's options and against dev's lean: `author` loses its default and takes the CAPABILITY's baseline, restrict-only from there; and `direct` is amended to attest the authorship axis it was already unlocking, on the new rule that **an attestation may be untrusted but must not be unknowable** (§3a). **F3** capability pinned to concrete carriers, absence-vs-invalid taken verbatim. **F4/F5/F6** folded per the joint split. | **v5** — one addition on the owner's S2 ruling (2026-08-31), no mechanism change: §5 gains the ORDERING PRECONDITION that Phase A must not ship before the `valid_from` predicate lands. Phase A is what makes that predicate necessary rather than desirable — today a not-yet-valid edge is assertable but only via a HOST-SIDE write with attested capture (an MCP write floors to USE_ONLY: harness S2 + T4-3), and `capability=direct` removes exactly that mitigation, converting a host-only anomaly into an agent-reachable over-assertion. Phase A remains independent of 0029 and Phase B; this is its ONE external precondition. | **v4** — one addition to §6a on dev's re-read: the Phase B REVERSAL CASES are recorded as a stated DEBT (clean undo / scoped-reversal reaching a second edge / intervening-state refusal), owed and pinned model-free before Phase B's first run, with the reason for deferring given — *pin before THE RUN* (0027 R3-6), never *pin before the design settles*. Converts an unpinned surface from a gap a reviewer finds into an obligation the spec states. No other change from v3. | **v3** — reversal fold, on dev's option-(b) ruling. New **§4c-iii**: an applied resolution must be reversible, and the inverse data is **0029's, not this spec's** — Phase B DEPENDS on the transaction-time carrier rather than duplicating pre-state capture (agreement-by-coincidence between two carriers of one fact is the standing hazard). Three constraints: undo is a FORWARD journaled transition following 0022's reinstate pattern (history never un-happens); SCOPED to the applying `txn`, never expressible as a bare "revive edge X"; and FAIL-CLOSED on intervening state, refusing with a diff rather than cascading. Adds V-UNDO-FORWARD / V-UNDO-SCOPED / V-UNDO-FAILCLOSED. **The dependency lands on Phase B ONLY — Phase A ships alone, unchanged.** 0031 becomes V-RECON's SECOND CONSUMER (belongs in the seam manifest's S1). Prompted by AreevAI/areev shipping "every apply stores its inverse" (competitive triage 2026-08-31). | **v2** — dev internal-review fold. **D-1** the capability composes with AUTHOR and never overrides it (author/relation/revocation rows added to §3), plus new **§3a** reconciling the capability→`EvidenceContext` bridge with 0011's explicit refusal to mint `direct()` by omission (`__init__.py:361`) — minting by DECLARATION is not minting by OMISSION, and the per-event→deployment widening is stated as the honest cost. **D-2** the proposal carrier PINNED at DDL level (new §4b-ii) with the schema-version ordering dependency on 0029 left deliberately unresolved, and the erasure gap closed (V-ERASE-PROPOSALS). **D-3** both carriers named: `mcp_max_open_proposals` (default 32, range 1–256, refuses rather than evicts) and `provenance_raises_discarded` (stripped operator counter). §1 additionally carries the LIVE Bedrock evidence for T4-3. | **v1** — first candidate. Folds two owner rulings taken 2026-08-31 on measured evidence: decision 1 (MCP provenance self-attestation → option **c**, host-attested capability) and decision 2 (trust verbs → `forget`/`correct`/`confirm` not agent-exposed; `dispute` proposal-form only). Both resolve to ONE principle — **the host attests, the model proposes** — which is why they are one spec with two separable phases. |
| **Author / session** | research (veracium-research); adopted by dev (v4-v9 per the cells; v10 = the round-4 fold — adopted 2026-09-02, the round-5 pin; frozen from adoption to seal) |
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

> **A model-supplied trust argument may never make the event MORE TRUSTED, on
> any consumer of the field it sets.**

Deliberately no longer phrased as "descend in the product" — see the four
separate obligations below. **Round-2 F1 RETRACTS the single-order framing**,
and it was this author's over-generalisation: v6 enumerated four CONSUMERS
correctly and then asserted ONE monotone rule across all of them, without asking
whether each is ORDERED. Two are; one is a shaping rule; one is a digest with no
order at all, where "descend" is not a wrong requirement but a meaningless one.

This is not new machinery — it is 0026 §3b's restrict-only floor generalised
from the relay lexicon to the whole agent-facing surface. But v5 stated the rule
over the whole trust model and then **checked it on one coordinate**, which is
round-1 F1 and is corrected here.

**The product, enumerated.** `derived_from` and `author` are read by more than
`_disclosure_for`, so a value that is neutral on disclosure can still be a raise:

| # | consumer | read at | kind | the obligation |
|---|---|---|---|---|
| 1 | `_disclosure_for` | `ingest.py:141-158` | **ORDERED** (two-valued: `USE_ONLY` < `MENTIONABLE`) | DESCEND-ONLY — a model-supplied value may move toward `USE_ONLY`, never toward `MENTIONABLE` |
| 2 | `effective`/`permitted`/`edge_effective` | `authority.py:53-82` | **ORDERED** (four rungs, `USER 3 … THIRD_PARTY 0`) | DESCEND-ONLY — never a higher rung than the capability baseline yields |
| 3 | `ScopeView`'s unset-`derived_from` fill | `scope_read.py:387-388` | **SHAPING**, not a trust level | RESTRICT-ONLY — the shaped record may withhold more, never reveal more |
| 4 | `scope_fingerprint` | `authority.py:86-102` | **NOT ORDERED** — a sha256 equality digest (verified: it returns `hashlib.sha256(...).hexdigest()`); no top, no bottom, no direction | **PRESERVE-OR-INVALIDATE** — a provenance change either leaves the fingerprint identical, or any plan computed against the old one is rejected as `PlanStale`. It must never be described as descending, because a digest cannot |

**Four obligations, not one rule with four instances.** Coordinates 1 and 2 are
genuinely ordered and the round-1 F1 counterexample lives on 2. Coordinate 3 is
a shaping rule whose direction is about disclosure of the RECORD, not its trust
class. Coordinate 4 has no order whatever: `scope_fingerprint` is the CAS token
for `apply_supersession_plan`, so the only coherent obligation is that a change
is either invisible to it or invalidates the plan — and "over-sensitivity only
costs a retry; it never misses a stale read" is the shipped comment's own
framing. Requiring it to "descend" was not a strong claim that turned out false;
it was a category error, which is worse, because it cannot be tested at all.

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
  capture — so every other closed-set value is a genuine restriction under
  BOTH ordered obligations (disclosure and authority descend), leaves shaping
  strictly narrower, and changes the fingerprint only in the
  preserve-or-invalidate sense — restrict-only has real content here, stated
  per obligation because the obligations are separately shaped (§2c).

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

- A model-supplied value satisfies ALL FOUR obligations in §2c relative to the
  host capability's baseline, each under ITS OWN invariant — V-DESCEND-DISCLOSURE,
  V-DESCEND-AUTHORITY, V-RESTRICT-SHAPING, V-FINGERPRINT-STABLE-OR-STALE. *(Round-4
  F5: this line still branded the four with the retired umbrella name. The
  round-3 sweep missed it because it hunted the PHRASE just fixed — "descent on
  every coordinate" — and the old ROW, not the SYMBOL being retired; a symbol
  retirement sweeps the symbol's name and classifies each hit use-vs-mention,
  which finds a reference in any grammatical clothing. One use lived here; the
  two survivors below are mentions narrating the retirement.)* *v5 said "cannot produce a class less restrictive",
  which names only disclosure — that phrasing was round-1 F1. v6 then over-
  corrected into a single order over four consumers, which was round-2 F1. The
  obligations are stated separately here because they are separately shaped.*
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
| `direct` | `derived_from` | `"third_party"` / `"assistant"` | as declared | a genuine restriction under each obligation that orders (disclosure, authority descend; shaping narrows; fingerprint: preserve-or-invalidate) — honoured |
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

#### The capability → `EvidenceContext` mapping, PINNED (round-2 F2)

v6 described `direct` as minted per call **while** a lower supplied
`derived_from` is honoured. **That is unimplementable against the shipped
grammar, and the reviewer reproduced it — as did this author, independently:**

```
_resolve_context(EvidenceContext.direct(), EvidenceAuthor.user)        -> ValueError
_resolve_context(EvidenceContext.direct(), EvidenceAuthor.assistant)   -> ValueError
_resolve_context(EvidenceContext.direct(), EvidenceAuthor.third_party) -> ValueError
```

> `pass EITHER context= OR the legacy derived_from=, not both — two
> declarations of one fact is a host bug` (`ingest.py:112-130`)

**The refusal is right and the spec was wrong.** "Two declarations of one fact
is a host bug" is the same principle this spec argues everywhere else — one
carrier per fact — so v6 was proposing, on this one surface, exactly what it
forbids elsewhere. The fix is not to relax the grammar; it is to pass ONE
carrier and let it carry the restriction.

| capability | model supplies | the SINGLE carrier passed |
|---|---|---|
| `direct` | nothing | `EvidenceContext.direct()` |
| `direct` | `derived_from = X` (any closed-set value) | `EvidenceContext.derived(X)` |
| `none` | anything or nothing | the absent-context floor — no context, no `derived_from` (§2c-i: both are inert here) |
| any | — | **never both carriers** |

The restriction is therefore honoured **THROUGH the declaration, never beside
it**: under `direct`, a model saying "this came from a third party" produces
`derived(THIRD_PARTY)` — one carrier, the descent recorded in it. Verified:
`_resolve_context(direct(), None)` yields `derived_from = None`, which is the
first-party cell, and `effective(USER, None) = 3` as §3's matrix requires.

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
    target_state_digest TEXT NOT NULL CHECK (
                        typeof(target_state_digest) = 'text'
                        AND length(target_state_digest) = 64
                        AND target_state_digest NOT GLOB '*[^0-9a-f]*'),
    correction_payload  TEXT CHECK (
        (kind = 'dispute'    AND correction_payload IS NULL) OR
        (kind = 'correction' AND correction_payload IS NOT NULL
                             AND typeof(correction_payload) = 'text'
                             AND json_valid(correction_payload)
                             AND length(correction_payload) <= 4096)),
    claim        TEXT CHECK (
        (kind = 'dispute'    AND claim IS NULL) OR
        (kind = 'correction' AND claim IS NOT NULL
                             AND claim IN ('error','change'))),
    evidence_ref TEXT CHECK (evidence_ref IS NULL
                             OR (typeof(evidence_ref) = 'text'
                                 AND length(evidence_ref) BETWEEN 1 AND 512)),
    note         TEXT CHECK (note IS NULL OR (typeof(note) = 'text'
                                              AND length(note) <= 4096)),
    created_at   TEXT NOT NULL CHECK (typeof(created_at) = 'text'),
    expires_at   TEXT NOT NULL CHECK (typeof(expires_at) = 'text'),
    state        TEXT NOT NULL DEFAULT 'open'
                 CHECK (state IN ('open','accepted','refused','expired')),
    resolved_at  TEXT CHECK (resolved_at IS NULL OR typeof(resolved_at) = 'text'),
    applied_txn  INTEGER CHECK (applied_txn IS NULL
                                OR (typeof(applied_txn) = 'integer'
                                    AND applied_txn >= 1)),
    CHECK ((state = 'open'     AND resolved_at IS NULL     AND applied_txn IS NULL) OR
           (state = 'accepted' AND resolved_at IS NOT NULL AND applied_txn IS NOT NULL) OR
           (state IN ('refused','expired')
                              AND resolved_at IS NOT NULL AND applied_txn IS NULL)),
    PRIMARY KEY (user_id, id)
);

CREATE TABLE mcp_proposal_resolution (      -- APPEND-ONLY; no UPDATE path exists
    user_id      TEXT NOT NULL,
    proposal_id  TEXT NOT NULL,
    seq          INTEGER NOT NULL CHECK (typeof(seq) = 'integer' AND seq >= 1),
    action       TEXT NOT NULL CHECK (action IN ('accept','refuse','expire','reverse')),
    at           TEXT NOT NULL CHECK (typeof(at) = 'text'),
    resolver     TEXT NOT NULL CHECK (typeof(resolver) = 'text'
                                      AND length(resolver) BETWEEN 1 AND 128),
    applied_txn  INTEGER CHECK (applied_txn IS NULL
                                OR (typeof(applied_txn) = 'integer'
                                    AND applied_txn >= 1)),
    reversal_txn INTEGER CHECK (reversal_txn IS NULL
                                OR (typeof(reversal_txn) = 'integer'
                                    AND reversal_txn >= 1)),
    CHECK ((action = 'accept'  AND applied_txn IS NOT NULL AND reversal_txn IS NULL) OR
           (action = 'reverse' AND applied_txn IS NULL     AND reversal_txn IS NOT NULL) OR
           (action IN ('refuse','expire')
                                AND applied_txn IS NULL    AND reversal_txn IS NULL)),
    PRIMARY KEY (user_id, proposal_id, seq),
    FOREIGN KEY (user_id, proposal_id) REFERENCES mcp_proposal(user_id, id)
);
```

**`PRAGMA foreign_keys=ON` at connection open is a PINNED STORE OBLIGATION —
discharged via a CENTRAL CONNECTION FACTORY, not per-site pragmas (round-4
F4).** SQLite enforces no foreign key without it, so an unpragma'd FK is *a
comment wearing a constraint's clothes* — the round-1 defect in a new costume,
and this spec would have shipped it in the fix for that very finding. Round 4
found the obligation UNDER-SCOPED: the constructor is not the only door.
The connection-path inventory (executed grep, both seats):

| site | class | can touch the proposal tables? |
|---|---|---|
| `store/sqlite.py:61` | THE constructor | yes — the sentinel's current coverage |
| `store/release_migration.py:811`, `:1013` | file-backed, migration | **YES** — migrations open the canonical store file |
| `store/migration.py:243` | file-backed, legacy migration | **YES** |
| `store/schema_version.py:604/:652/:1233/:1241` | `:memory:` scratch | no — never see a persistent file |

**The classifier CRITERION, so the next site gets classified rather than
missed:** a connection can touch the proposal tables iff its path argument can
name a persistent store file; a literal `":memory:"` connection cannot, ever.
Literal `:memory:` ⇒ scratch; anything else ⇒ file-backed and OWED THE FACTORY
— no third class. The factory (`_open_connection(path)`: busy_timeout +
`PRAGMA foreign_keys=ON`, one site) exists because per-site pragmas are N
obligations drifting independently — the one-carrier class as connection code;
a factory is one site to verify and shrinks the inventory to itself. The
sentinel's flip condition is restated over EVERY inventoried file-backed path
(partial enablement FAILS it), and an INVENTORY-COMPLETENESS sweep
(`test_connection_path_inventory_is_complete` — the every-control-sweep
pattern, labeled as a sweep, not behavior evidence) fails the moment a new
`sqlite3.connect` site appears unclassified.

#### Which mechanism owns which invariant (round-2 F5)

The reviewer's four remaining acceptances are not all row-shaped, and a row
`CHECK` cannot see another row. An obligation that does not name its mechanism
is the comments-are-not-constraints defect facing sideways, so every invariant
names its owner:

| invariant | owner |
|---|---|
| closed `kind`/`proposer`/`state`/`action`; claim & payload coherence; per-state coherence; field sizes; digest is 64 **hex** | **DDL** row `CHECK` |
| a resolution row references an existing proposal | **DDL** foreign key (+ the PRAGMA above) |
| `accepted` ⇒ an `accept` resolution row exists **with EQUAL `applied_txn`** | **schedule 3** — proposal row and accept row are written from ONE local variable in ONE commit (round-3 F5: both rows stored the value and nothing required equality; divergence is now unrepresentable, not audited-for) |
| `reverse` ⇒ a prior `accept` for the same proposal | **schedule 4** — it reads `applied_txn` from the accept row before writing anything |
| `seq` domain (`>= 1`, integer) | **DDL** (`typeof` + domain CHECK) |
| binding-type validation (caller's Python types; bool excluded from int) | **the store schedules** — the validation preamble, before any SQL binding; DDL structurally cannot see the binding type (round-4 F3) |
| `seq` allocation | **schedules 2/3/4** — `MAX(seq)+1` per `(user_id, proposal_id)` under the writer lock, in the resolution's own transaction |
| `seq` monotone and gapless; history APPEND-ONLY | **absence-by-API** (the store exposes no update/delete on the resolution table — the enforcement owner NAMED, not implied) + the **§6a V-RESOLUTION-LEDGER gate** (defined there — round-4 F2) audits immutability across runs via the journal |
| whole-table audits (every `accepted` has **EXACTLY ONE** accept row with equal `applied_txn`; every `reverse` has its prior accept; per-proposal `seq` gapless-monotone) | **§6a V-RESOLUTION-LEDGER gate** (defined there — round-4 F2) — outside any single row's reach by construction |

- **`target_state_digest`** — sha256 of the target's canonical serialization at
  proposal time. Stale-proposal detection, and it is **V-RECON's serialization
  doing double duty** rather than a second definition of "the same edge".
- **EVERY `CHECK` over a nullable column must state its NULL case, and every
  `CHECK` whose predicate is BLOB-blind must state its TYPE — the affinity trap
  is the NULL trap one type over (round-3 F6).** SQLite column types are
  affinities, not constraints: a 64-byte BLOB satisfies `length(x) = 64`, and
  `GLOB` on a BLOB evaluates NULL, which a CHECK passes — so the round-2 hex
  guard refused every wrong TEXT and admitted the wrong TYPE. Derived, not
  enumerated: predicates built on `length()`/`GLOB`/`BETWEEN` are BLOB-blind
  and gain a `typeof()` conjunct; `IN`-list predicates are safe (a BLOB equals
  no text literal, so they refuse by construction); every integer column gains
  `typeof` + domain. We learned NULL-blindness for VALUES in round 2 and not
  for TYPES; the rule above now covers both because it is one rule.
  **PART TWO — COERCION (round-4 F3), one trap further over again:** affinity
  conversion runs BEFORE every CHECK, so a `typeof()` conjunct — any DDL
  predicate — is a claim about the STORED representation, never about the
  caller's binding. Executed both seats: text `"7"` into an INTEGER column
  COERCES and passes `typeof(x)='integer'`; integer `7` into a TEXT column
  stores as `'7'` and passes; Python `True` binds as integer 1 and passes; only
  NON-coercible values (`"seven"`, `7.5`) refuse. **STRICT tables do not change
  the lossless cases** — executed, not recalled. No DDL can distinguish `"7"`
  from `7`, so the invariant SPLITS: **DDL owns the stored-representation
  domain** (its refusal claims narrowed to "non-coercible values"); **the store
  schedules own binding types** — a pinned validation preamble in every
  schedule: `str` for ids/actor/timestamps/payload, `int` and NOT `bool` for
  txn/seq (`isinstance(True, int)` is True in Python; refuse it explicitly),
  typed WRONG-ARGUMENT-TYPE refusal BEFORE any SQL binding.
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
- **THE PAYLOAD IS TYPED (round-4 F1) — `correction_payload` is a JSON OBJECT
  with EXACTLY these members:**

  | field | type | presence |
  |---|---|---|
  | `object` | non-empty string, 1..2048 | REQUIRED |
  | `note` | string ≤ 2048 | OPTIONAL |
  | `effective_date` | ISO-8601 UTC string | REQUIRED iff `claim='change'`; REFUSED iff `claim='error'` |

  Parse rules, all typed refusals: (1) **duplicate-refusing decoder** — 0030
  §4a-iii's discipline reused verbatim; last-wins parsing of
  `{"object":"a","object":"b"}` is the exact declassification vector 0030
  closed, here on a WRITE surface. (2) **Unknown keys REFUSED** — and the
  contrast with 0030's ignore-unknown is stated because it looks like an
  inconsistency and is not: that rule reads PERSISTED data written by dead
  schema versions; this is an agent's INCOMING argument, where an unknown key
  is a typo'd field silently dropped or a smuggling channel, both refusals.
  (3) Top-level must be an object; `{}` fails field requiredness. (4) The
  `effective_date` presence rule is conditioned on `claim` INSIDE the payload
  — the asymmetric-argument folklore rule applied one level down.
  **Parse authority, two sites:** the PROPOSE schedule parses and validates
  under the writer lock (a stored payload is valid BY CONSTRUCTION at insert);
  `apply_proposal` RE-parses at step (c) with the same rules, because persisted
  data can rot (0030's whole lesson) — a violation at apply is a typed
  CORRUPT-PAYLOAD refusal, zero writes, never a crash.
  **Honest limit at the DDL:** `json_valid` refuses arbitrary text; it CANNOT
  check fields, requiredness, or duplicate keys (SQLite's own parser is
  last-wins). Ownership: payload IS-JSON floor → DDL; payload FIELD contract →
  the store parse, both sites.
- **`claim` is a CLOSED DOMAIN with a VERB MAPPING**, which is the reviewer's
  F4 bullet and the carrier for §1's second problem. Without it the spec keeps
  its motivation and loses its mechanism:

  | `claim` | means | verb executed on accept | resulting reason |
  |---|---|---|---|
  | `'error'` | the prior was never true | `Memory.correct` (`__init__.py:1573`) | `corrected` (`schema.py:409`, disposition `drop`) |
  | `'change'` | the prior was true and changed | the SUPERSESSION construction (§4c-i schedule 3: replacement from the payload, `valid_from` REQUIRED, via the in-transaction plan variant) | `superseded` |

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

### 4b-iii. The tool schemas, pinned (round-2 F3)

**`user_id` comes OFF the Phase A and Phase B tool schemas.** §4e claims the
host process is the identity boundary; v6 left `user_id` a model-supplied
argument, so construction-time `default_user` bound nothing — the claim was
asserted and unenforced. This is absence-by-schema, the same move that defeats
Q2 for `proposer`: the parameter does not exist, so there is no value to
validate and nothing to refuse. Deployment-scoped `user_id` is captured at
construction, exactly as §4e's identity boundary requires.

```python
# Phase A: `remember` loses user_id; author becomes non-defaulting (§4a)
def remember(text: str, author: Optional[str] = None,
             event_type: str = "chat", date: Optional[str] = None,
             derived_from: Optional[str] = None) -> dict: ...

# Phase B: the ONE new tool. No user_id, no proposer, no turn identifier --
# each absent BY SCHEMA rather than rejected by validation.
def propose(kind: str,            # CLOSED: 'dispute' | 'correction'
            target_edge_id: str,
            correction_payload: Optional[str] = None,   # correction only
            claim: Optional[str] = None,                # 'error' | 'change'
            evidence_ref: Optional[str] = None,         # a REFERENCE to look up
            note: Optional[str] = None) -> dict: ...
```

`user_id`, `proposer`, `resolver` and any turn identifier are supplied by the
server from construction config. A deployment that needs multi-user-per-process
is out of Phase B v1 scope (§4e) — over stdio the transport cannot distinguish
callers, so the honest options are one process per principal or an
authenticated transport, not a model-supplied argument.

**Q2's contradiction, resolved in Q2's favour minus the impossible half
(round-2 F3).** §4c-ii Q2 required the resolution surface to display "the turn
it arose from"; §4e correctly DROPS the originating turn as unavailable over
stdio. v6 shipped both sentences. Q2's requirement is now: the resolver must see
**the proposal's stored content, its `kind` and `claim`, its `proposer`, and its
`evidence_ref` as an unresolved reference** — attribution sufficient to know
they are deciding about an AGENT's claim, which was Q2's actual purpose. The
turn is not shown because it cannot be known; §8 records that as a limit rather
than leaving a requirement no deployment can meet.

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

1. **PROPOSE** — `BEGIN IMMEDIATE` → count open proposals for the user (at the
   limit: typed refusal — refuse, never evict) → **TARGET VALIDATION** (round-3
   F3): the target edge exists and belongs to `user_id`, else a typed refusal
   with zero writes → **THE DIGEST IS MINTED BY THE STORE**: sha256 over the
   target's live canonical serialization, read under THIS writer lock.
   `target_state_digest` is **never a tool argument** — absence-by-schema, the
   same move as `proposer` and `user_id`: the model must not be able to claim
   what the target's state was, and v8's schedule counted and inserted without
   ever reading the target, leaving the one field stale-detection depends on
   with no defined minting site. Minting under the same lock also makes
   stale-detection sound BY CONSTRUCTION: the digest is the state at proposal
   time as the STORE saw it, not as anyone reported it → `INSERT`
   (schema-checked) → `COMMIT`. Count, validation, digest and insert share one
   lock, so two instances cannot both see room for the last slot and the digest
   cannot describe a world the insert did not happen in.
2. **RESOLVE** (refuse / expire) — `BEGIN IMMEDIATE` → CAS `... WHERE state =
   'open'` → `changes() = 0` ⇒ typed ALREADY-RESOLVED refusal → append the
   resolution row → `COMMIT`. Expiry racing a refusal resolves atomically one
   way or the other; there is no third outcome and no silent double-resolve.
3. **ACCEPT-AND-APPLY — `Store.apply_proposal`, SIGNATURE AND INPUT CONTRACT
   PINNED (round-3 F4):**

   ```python
   Store.apply_proposal(user_id: str, proposal_id: str, *, actor: str,
                        acknowledged_value: str | None,
                        acknowledged_claim: str | None,
                        acknowledged_effective_date: str | None) -> dict
   ```

   `actor` is 1..128 characters and becomes `resolver` on the resolution row.
   The two `acknowledged_*` are **REQUIRED iff `kind='correction'`** (echo-
   checked against the STORED payload and claim, typed refusal on mismatch)
   and **REFUSED if supplied for a dispute** — an argument that is sometimes
   meaningful and silently ignored otherwise is how APIs grow folklore.
   **`acknowledged_effective_date` (round-4 F1) is REQUIRED iff
   `claim='change'`** — echo-checked against the stored payload's
   `effective_date`, typed refusal on mismatch — **and REFUSED otherwise: for
   disputes AND for `claim='error'` corrections**, the same symmetry as its
   siblings. The resolver now approves the value, the KIND of history, and THE
   DATE that history takes effect; approving a backdated change without seeing
   the date was the residual half-approval.

   **THE THREE IN-TRANSACTION CONSTRUCTIONS, each naming the machinery it
   rides — "the ordinary write path" appears nowhere, because round-2 named a
   path and round-3 correctly asked which one:**
   - **DISPUTE** → the target's invalidation with reason `disputed`, through
     the in-transaction plan variant; journal events in the same `txn`.
   - **ERROR (`claim='error'`)** → the CORRECTION construction: replacement
     edge minted with `object` = payload.object, `note` = payload.note (absent
     ⇒ none), same subject/relation as the validated target; `effective_date`
     MUST be absent — refused at propose time and RE-refused at apply.
     Displaced prior takes reason `corrected`, through the in-transaction plan
     variant.
   - **CHANGE (`claim='change'`)** → the SUPERSESSION construction, target-
     specific: replacement built the same way, prior takes reason
     `superseded`, and `valid_from` comes from the payload's effective date —
     **REQUIRED for a change and refused when absent**, because a change
     without a date is exactly the false-history ambiguity the error-vs-change
     distinction exists to prevent; this is that distinction made operational
     at the API rather than descriptive in the docs.

   A store primitive that OWNS the transaction (round-2 F4):** v6 described this schedule without a
   primitive that could execute it, and the reviewer is right that it could not
   be assembled from the existing verbs: **`Memory.correct` commits its
   supersession plan internally and then writes its episode separately** — two
   commits, verified at the code — so no caller can wrap it with the proposal
   CAS in one transaction. Pinned:
   `BEGIN IMMEDIATE` → (a) read the proposal UNDER THE WRITER LOCK, requiring
   `state='open'` and not expired against a once-minted `now` → (b) live digest
   vs `target_state_digest`, mismatch ⇒ typed STALE refusal, zero writes →
   (c) echo checks for a correction, so §4c's friction is enforced at the
   PRIMITIVE and not only at the API → (d) the mutation IN-TRANSACTION →
   (e) 0029 journal allocation in the same transaction → (f) CAS
   `open`→`accepted` with `applied_txn`; `changes()==0` ⇒ **ROLLBACK EVERYTHING**
   and a typed ALREADY-RESOLVED refusal → (g) the episode append, absorbing
   `correct()`'s second commit → (h) the resolution row with `resolver=actor` →
   `COMMIT`.
   **PREREQUISITE, pinned as its own obligation:** `apply_supersession_plan`
   gains an **in-transaction variant** — the same writes with the caller owning
   `BEGIN`/`COMMIT` — while the self-committing form remains for every existing
   caller. That is the composability gap the finding names, closed ADDITIVELY
   rather than by changing a shipped verb's contract.
   The CAS at (f) is unreachable-to-miss under this schedule, since (a) read the
   state under the same writer lock; it is kept as defense in depth, and §6a
   carries a control PROVING the rollback (mutation gone, journal empty,
   proposal untouched) rather than asserting it. Both "a committed correction
   remains recorded as open" and its inverse stay **unrepresentable** — now with
   the primitive that makes the claim implementable rather than aspirational.
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
| Q2 | **Authorship confusion** — the resolver reads "the user requests" when the truth is "the assistant proposes" | resolution MUST display the proposal's STORED content, its `kind` and `claim`, its `proposer`, and its `evidence_ref` as an UNRESOLVED reference — and nothing else. No turn: §4e drops it as unknowable over stdio, and v8 fixed §4b-iii and §4e while leaving THIS row still demanding it — the one-carrier-of-a-fix class, in the table that motivated the fix. The resolver is deciding about an AGENT's claim, and must see that |
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
| **V-DESCEND-DISCLOSURE** no model-supplied value yields a less restrictive disclosure than the capability baseline; the raise is discarded and counted | `test_disclosure_descends_only` |
| **V-DESCEND-AUTHORITY** no model-supplied value yields a higher effective supersession authority than the baseline (the round-1 counterexample's axis) | `test_authority_descends_only` |
| **V-RESTRICT-SHAPING** the shaped record under a model-supplied value withholds at least what the baseline withholds — never reveals more | `test_shaping_restricts_only` |
| **V-FINGERPRINT-STABLE-OR-STALE** a model-supplied value either leaves `scope_fingerprint` unchanged or every plan computed against the old one refuses as `PlanStale`; the invariant asserts NO ordering, because a digest has none (round-3 F1: the old V-NO-RAISE said the fingerprint could be "raised", contradicting V-OBLIGATIONS-SEPARATE two rows below it — the one-carrier class inside one table) | `test_fingerprint_preserve_or_invalidate` |
| **V-INERT-UNDER-NONE** under `none`, EVERY supplied `author`/`derived_from` value leaves the stored record identical to the baseline — the case F1 was made of (`assistant` must not reach authority 1) | `test_none_baseline_is_the_bottom_element` |
| **V-AUTHOR-BASELINE** absent `author` resolves to the capability baseline and NEVER to `"user"`; the shipped default is gone | `test_author_has_no_default_of_its_own` |
| **V-CAP-DEFAULT** only ABSENCE resolves to `none`; EVERY supplied invalid value — including the empty string — raises at construction | `test_capability_absence_is_the_untrusted_cell` |
| **V-OBLIGATIONS-SEPARATE** the four obligations above are checked by FOUR invariants, never one umbrella: any future test or prose claiming a single order across them is the round-2/round-3 F1 defect recurring | `test_no_umbrella_ordering_claim` |
| **V-ONE-CARRIER** the capability→context mapping passes exactly one carrier; passing both raises, and the test asserts the shipped `ValueError` rather than restating it | `test_capability_maps_to_one_carrier` |
| **V-NO-USER-ID-ARG** no Phase A or Phase B tool schema exposes `user_id`, `proposer`, or a turn identifier — asserted against the built server's reflected schema, not the source | `test_tool_schemas_omit_identity_arguments` |
| **V-APPLY-ATOMIC** `Store.apply_proposal` commits mutation, journal, state flip, episode and resolution row together; a forced CAS miss leaves ZERO trace (mutation gone, journal empty, proposal untouched) | `test_apply_proposal_is_one_transaction` |
| **V-FK-ENFORCED** the foreign key actually bites — asserted on a connection opened the way the store opens it, so a missing `PRAGMA foreign_keys=ON` FAILS rather than passing silently | `test_resolution_fk_is_enforced_not_declared` |
| **V-RESOLUTION-LEDGER** the §6a fenced gate SQL, extracted at test time, returns zero rows on every audit SELECT over any legal history; each clause has a constructed history that fires exactly it | `test_resolution_ledger_gate` |
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

#### V-RESOLUTION-LEDGER — the whole-table gate, DEFINED (round-4 F2)

Round-3's ownership table cited "the §6a cross-table gate" and §6a defined
acceptance probes only — **the gate existed nowhere.** The phantom-citation
class (the joint arc's V-BIND lesson) in this spec, and the promising sentence
was our own. The fix is the extract-at-test-time discipline extended from the
DDL to the gate: **the gate IS this fenced SQL**, extracted and executed by the
committed test, so the audit that runs cannot drift from the text that
promises it. Every SELECT must return zero rows:

```sql
-- V-RESOLUTION-LEDGER: whole-table audit; every SELECT must return zero rows.
-- (1) accepted-proposal <-> exactly-one-accept-row, applied_txn EQUAL
SELECT p.user_id, p.id FROM mcp_proposal p WHERE p.state = 'accepted' AND
  (SELECT COUNT(*) FROM mcp_proposal_resolution r
    WHERE r.user_id = p.user_id AND r.proposal_id = p.id
      AND r.action = 'accept') != 1;
SELECT p.user_id, p.id FROM mcp_proposal p
  JOIN mcp_proposal_resolution r
    ON r.user_id = p.user_id AND r.proposal_id = p.id AND r.action = 'accept'
 WHERE p.state = 'accepted' AND r.applied_txn != p.applied_txn;
-- (2) an accept row implies an accepted proposal (the converse direction)
SELECT r.user_id, r.proposal_id FROM mcp_proposal_resolution r
  JOIN mcp_proposal p ON p.user_id = r.user_id AND p.id = r.proposal_id
 WHERE r.action = 'accept' AND p.state != 'accepted';
-- (3) reverse requires a PRIOR accept (lower seq), and at most one reversal
SELECT r.user_id, r.proposal_id, r.seq FROM mcp_proposal_resolution r
 WHERE r.action = 'reverse' AND NOT EXISTS (
   SELECT 1 FROM mcp_proposal_resolution a
    WHERE a.user_id = r.user_id AND a.proposal_id = r.proposal_id
      AND a.action = 'accept' AND a.seq < r.seq);
SELECT user_id, proposal_id FROM mcp_proposal_resolution
 WHERE action = 'reverse' GROUP BY user_id, proposal_id HAVING COUNT(*) > 1;
-- (4) per-proposal seq is gapless-monotone from 1
SELECT user_id, proposal_id FROM mcp_proposal_resolution
 GROUP BY user_id, proposal_id
HAVING MIN(seq) != 1 OR MAX(seq) != COUNT(*);
```


**Append-only-across-runs** — the one clause single-snapshot SQL cannot see:
PREVENTION stays absence-by-API (unchanged); DETECTION is the gate's cross-run
half — the audit persists `(user_id, proposal_id, seq, content_hash)` per row
and a later run refuses if any previously-seen row is absent or altered.
The committed test proves the snapshot half today; the cross-run half is a
Phase B acceptance obligation, like the interleavings. A gate that has never
fired is a comment, so each clause ships with a history that violates exactly
it, plus a clean multi-proposal pass.

**The instrument already exists**, which is unusual and worth stating: the
acceptance corpus is the frozen harness manifests, and the decisive case is
already pinned.

**CITED BY DIGEST, and SHIPPED (round-2 F6).** v6 named the manifests and bound
nothing — so "the acceptance corpus already exists" was unverifiable from the
archive, which is exactly the reviewer's objection. The corpus now travels with
the package (**`corpus/`** — the spec said `acceptance-corpus/` while the
archive said `corpus/`, a name split across two carriers; the archive's name
wins and the spec now uses it): both manifests, both raw result sets, the three
test drivers, **the `harness` package they import** (round-3 F7: all three
drivers failed collection without it — a corpus whose drivers cannot run is
evidence that cannot be checked), the exact source revisions the raw results
identify, the pinned `0031-P3-6-direct-variant-DRAFT.md` companion, and **one
archive-local command that reruns the deterministic corpus** (`corpus/rerun.sh`) —
whose claim is stated exactly (round-4 F6): **source-contained, not
execution-contained.** Every executed source byte comes from the archive,
guard-enforced; the interpreter stack (python ≥ 3.11, pytest ≥ 8, pydantic ≥ 2,
receipt versions pinned in the script) is a documented prerequisite, and
external pytest plugins are disabled. Vendoring wheels was refused because
pydantic-core is a platform-specific binary — a vendored stack is
"self-contained" on the sealer's platform and silently false elsewhere, which
is the same over-claim in better clothes.
The citation and the artifact are one object:

| manifest | version | sha256 (FULL — round-3 F7: an ellipsized digest in a NORMATIVE citation is the location-index defect in digest form; a prefix names a family of possible files, and only the full value binds ONE) |
|---|---|---|
| `corpus/cases/tier45_manifest.json` | v1.1 | `b504904bd79165a33adae29461486a537470a15f2c5be41c4fc927929fe9708c` |
| `corpus/cases/verbs_manifest.json` | v1.0 | `91a9e78eaebad756b7c6c92f993006c216a469bf2604267ee7d49bb4055b4fa4` |

**And what the corpus does NOT establish, stated here rather than left to be
found:** these are the **pre-Phase-A** results. Phase A does not exist, so
nothing shipped executes 0031's own invariants — the runs establish the MEASURED
BASELINE this spec reasons from (P3-3's elevation, the relay floor's
independence, the verbs' marginal power), not the correctness of the design.
The pass criteria below become runnable when Phase A lands. Answering a
verifiability finding with an over-claim would be worse than the gap it
closes.

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
  **The relay floor itself is NOT left unguarded, and this author's first
  statement of the finding implied otherwise.** Checked against the manifest
  rather than assumed: **P2-1** is already a host-side direct-baseline relay
  case — `author=user`, `context=direct`, the same `"my doctor said…"` marker,
  expecting `use_only`/not-assertable — with **P2-2** as its matched control
  (identical but marker-free, expecting `mentionable`). Delete the relay floor
  and P2-1 flips and fails. So the correct scope of this finding is **P3-5 loses
  its own meaning**, not *the floor becomes untested*; the wider reading was an
  overreach and is withdrawn here.

  **The `capability=direct` variant is still owed, on a better footing.** Not
  because the floor would otherwise go unmeasured — P2-1 measures it — but
  because **Phase A creates a NEW path to a mentionable baseline**: the MCP
  surface, which has never had one. P2-1 exercises the floor on the HOST path.
  The floor's behaviour on an MCP write under `capability=direct` is unmeasured,
  and that is precisely the same argument §6a already makes for re-running P1b —
  Phase A raises the stakes on a surface whose bound was previously supplied by
  the absent-context floor. The variant is pinned before the run, per house
  discipline.
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
