# Feature spec: token-usage telemetry over the Metered wrapper

Spec-Status: draft

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v4 — EXTERNAL ROUND 1 (6 bin-(a), bin (b) empty; the consent-v3 reuse and the corrected compile mapping endorsed as directionally sound): ALL FOLDED — and this is a REDESIGN round: the reviewer adopted BOTH of §9's recorded fallbacks as requirements. **F1 (class A+B, overturns v3's §3b):** totals-snapshot deltas reproduced factor-N overcounting AND a cross-user PRIOR-STATE side channel (a concurrent user-B compile delta reveals the size of what `compile.py` built from B's stored facts; v3's single-`Memory` mitigation was FALSE — one instance serves arbitrary `user_id`s incl. MCP) → the design is WITHDRAWN for §4b's per-call events attributed via a thread-local operation-context stack — exact by construction, barrier-tested (I9). **F2 (class B+E):** duck-typed `totals()` shape is not intent → §4a's affirmative capability constant + listener registration; a coincidental `totals()` is never invoked (I11). **F3 (class A+G, reviewer-reproduced against the SHIPPED wrapper):** the counter fired unprotected inside the lock — the operation broke and a partial record survived → §4c's atomic all-or-nothing accounting (both counts validated into locals; either invocation failing discards the pair, emits nothing, returns the provider output; `calls`/chars ride the always-valid block). **F4 (class C):** I2b missed `self_check`'s reach (temporary memories driving distill/gate/compile) and the protocol's DEFAULT `role="compile"` → §4e DECIDES: self-check excluded by design (closes §10 Q3), and I2b is backed by a declarative producer REGISTRY asserted against an AST call-site scan resolving default roles. **F5 (class A+C):** the accumulator had no construction → §4d: `Memory`-instance carrier, lock-guarded, `"instance-lifetime"` (the process-lifetime label was false), and **`forget(user_id)` deletes the entry — compliance erasure covers unpersisted state too**. **F6 (class D):** consent semantics disagreed across carriers → §4f's explicit three-carrier × consent matrix; "sent" scoped to the telemetry endpoint; audit/introspect stated consent-independent-and-local by design. *Miss diagnosed: v3 restated F1's smear honestly but never re-derived WHAT the smeared bytes measure (compile input = prior store state) — the §3b information-not-carrier lesson one level deeper; and the F3 guarantee was written where the code wasn't (claims-vs-code inside the spec's own wrapper).* *(v3 history: internal round 1 — the two-producer mapping, pair-granular I2b, the honest smear restatement.)* |
| **Status** | *narrative only — canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research — round 1 RETURNED 2026-08-13 (3 findings, folded in v3; their preliminary Q1 mapping amended by their own review); re-review requested · workflow-platform unavailable, waived: no consumer-visible API change beyond an optional `introspect()` block — waiver held by dev |
| **External review** | ROUND 1 RETURNED 2026-08-13 (package `0017-v3-20260813T1157Z.tar.gz`): 6 bin-(a), folded as v4 (the attribution redesign); round-2 package next |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

`2767a35` removed four token fields (`ingest.distill_in_tok`,
`ingest.distill_out_tok`, `answer.gate_in_tok`, `answer.gate_out_tok`) that
were whitelisted and populated **nowhere**, and cut "token totals" from the
consent text — because `Complete` returns a bare string and veracium never
owns credentials or model choice, so usage is invisible to the library **by
design**. That commit named the only honest re-entry path: *"Re-add only with
the planned `veracium.llm.metered` opt-in wrapper that makes it visible."*
The wrapper shipped (`f5ce03f`): `Metered` wraps any `Complete`, counts
per-role calls, and counts **tokens iff the host supplies a counter** —
otherwise characters, honestly labelled, never fabricated tokens. Steps 2–3
of the token-accounting plan were deferred to this spec: (2) usage into the
existing telemetry/audit sinks; (3) per-user totals through `introspect()` —
our answer to Hindsight's per-bank `/llm-requests/stats`, the one Workstream-C
finding filed against us. **Do nothing:** the wrapper's numbers stay locked in
one process-local object; opted-in telemetry still cannot answer the basic
cost question; the Workstream-C follow-up rots the way `2767a35`'s obligation
nearly did.

**Alternatives rejected:**

- **Send character counts under the token field names when no counter is
  supplied.** Rejected outright — a number labelled as tokens that is not
  tokens is the exact claims-vs-code defect `2767a35` existed to stop. **No
  counter → no token telemetry.** Character counts stay host-side in the
  wrapper.
- **Persist per-user usage in the store** (durable historical totals).
  Deferred, not chosen: it needs a SCHEMA bump and a retention/erasure story
  (usage becomes stored personal-adjacent data subject to `forget_user`).
  v1's `introspect()` totals are **instance-lifetime, in-memory** (§4d),
  stated as such in the payload itself; a persisted variant is a successor
  decision (§10 Q2).
- **Totals-snapshot deltas as the attribution mechanism (the v1–v3 design).**
  WITHDRAWN at external round 1 (F1): global-snapshot subtraction over
  concurrent operations both overcounts by up to a factor of N and creates a
  cross-user prior-state side channel (a concurrent compile delta reveals
  the size of what another user's stored memory built) — replaced by §4b's
  per-call events with thread-local operation context.
- **Duck-typed `totals()`-shape detection as opt-in.** WITHDRAWN at external
  round 1 (F2): shape proves data, not intent — replaced by §4a's
  affirmative capability + listener registration.
- **Auto-wrap the host's callable so usage is always visible.** Rejected:
  veracium never owns the LLM relationship; metering is the host's explicit
  opt-in, exactly as `Metered`'s docstring promises.
- **Emit the counts to already-consented v2 installs.** Rejected — the 0015
  consent rule is now machinery, not precedent: new fields ride a **new
  consent version (3)**, gated at record time, stamped only by affirmative
  display flows.

---

## 2. Field contracts touched

No memory-store field is touched — no edge, episode, or store format changes
(§3). The consent design's two persisted values (`schema_version`,
`consent_epoch`) behave exactly as accepted 0015 defines; this spec only
raises the current consent version.

| field | read / written | its **documented** contract | every other consumer | preserved? |
|---|---|---|---|---|
| `EVENT_FIELDS["ingest"]` / `["answer"]` / `["recall"]` / `["maintain"]` | written: the four `2767a35` fields return AND the compile pairs join at BOTH compile producers — `recall.compile_in_tok`/`compile_out_tok` (the wiki compile, `compile.py:239`) and `maintain.compile_in_tok`/`compile_out_tok` (the consolidation compile, `lifecycle.py:128` — v3, internal F1; a "token usage" label that omits the most expensive producer misleads by omission) | whitelist; anything unlisted is dropped at record | `Collector.record/snapshot`; `tests/test_telemetry_claims.py` (whitelisted ⇒ populated) | yes — populated by this change, which is what the gate demands |
| `FIELD_MIN_VERSION` | written: all EIGHT fields at min version **3** | 0015: a field is sent only if recorded under a consent that admits it | `Collector.record` (the binding gate), `_payload` (defense-in-depth) | yes — the 0015 mechanism reused unchanged |
| `SCHEMA_VERSION` | 2 → **3** | the current consent-text version; stamped only by affirmative display flows (0015 I13) | `prompt_consent`, `accept_current_consent`, the payload stamp | yes — one more version through the same machinery |
| `CONSENT_TEXT` | written: token sentence returns, scoped | the consent claim; `test_consent_text_does_not_promise_token_totals` PINS that "token" is absent until fields are whitelisted AND written | `prompt_consent()`, CLI enable | **the pin test flips direction in the same commit** (I5): text mentions tokens iff whitelisted and written — both now true |
| `Metered` — the capability + listener interface | `metering_capability = "veracium-metered-v1"` + `add_usage_listener(fn)`; per-call events `{role, in_tok, out_tok}` emitted synchronously on the calling thread AFTER both counts validate (§4a/§4c); `totals()` stays the host's own view and is no longer read by `Memory` | `Memory` (registers the listener); hosts; `tests/test_metered.py` — the shipped docstring's "nothing writes to telemetry" paragraph is REWRITTEN to this contract |
| `Memory` operation context + per-user accumulator | NEW instance state (§4b/§4d): the thread-local `(event, user_id)` context stack pushed/popped by every public operation; `Memory._llm_usage` keyed by `user_id`, lock-guarded, INSTANCE-lifetime, deleted by `forget(user_id)` | the listener (writes), `introspect()` (reads), `forget()` (erases), `_record` (the attributed fields fan out to telemetry-gated + audit carriers) |
| `introspect()` return | written: an optional `"llm_usage"` block (per-role calls + tokens, `"scope": "instance-lifetime"` in the payload — v3's process-lifetime label was false for instance-local state) | the transparency surface; consent-INDEPENDENT local carrier (§4f) | host API + CLI `introspect` (NOT an MCP tool — §2c-ii); absent when unmetered; empty for a forgotten user |

Consumers enumerated mechanically — commands in §2c-ii.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| the host's `counter` callable | no counter → no token fields ever (chars stay host-side) | non-int / bool / negative / NaN / raising — on EITHER invocation, incl. the second | — | a two-stage counter that succeeds once then raises (the reviewer's F3 reproduction: the operation broke and a partial record survived) | **atomic all-or-nothing accounting (§4c): both counts computed and validated into locals OUTSIDE the lock; any failure discards the whole token pair, mutates no token state, emits no event; the provider output is ALWAYS returned; `calls`/chars ride the always-valid block** — `test_counter_failure_is_atomic_and_never_breaks_the_operation` (both invocation positions) |
| an unrelated object with a coincidental `totals()` method | — | — | duck-typed hosts | a valid-SHAPED `totals()` on a non-Metered object (F2: shape is not intent) | **never probed, never invoked, never routed — opt-in is the affirmative capability constant + listener registration (§4a)**; `test_coincidental_totals_shape_is_never_invoked` |
| concurrent operations sharing one wrapper | — | — | — | N overlapping operations, different users, nested calls (F1's reproductions: factor-N overcounting; cross-user prior-state absorption) | **EXACT attribution by construction (§4b): per-call events on the calling thread, attributed to that thread's innermost operation context — no snapshot window exists to overlap**; I9's barrier-controlled cells (cross-user, nested `answer→recall`, concurrent `recall.compile` vs `maintain.compile`) |
| the consent config | — | — | — | — | **unchanged 0015 machinery** — v1/v2-consented installs never send the token fields (min version 3); every 0015 I8/I13/I16/I17 test keeps running |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | result |
|---|---|---|
| the four fields were exactly ingest.distill_* + answer.gate_* | `git show 2767a35 -- src/veracium/telemetry.py \| grep "^-.*tok"` | the two removed lines, four fields |
| `introspect` is NOT an MCP tool | `grep -n "@server.tool" -A 1 src/veracium/mcp_server.py \| grep -i introspect` | no hits (exit 1) |
| the consent-text token pin exists and currently forbids | `grep -n "token" tests/test_telemetry_claims.py` | `test_consent_text_does_not_promise_token_totals` |
| `Metered.totals()` is the only usage surface and pushes nowhere | `grep -rn "totals\|telemetry\|audit" src/veracium/llm/metered.py \| grep -v '"""'` | totals() only; no sink imports |
| the MCP `remember`/`answer` results carry no usage today (nothing to strip) | `grep -n "_tok\|usage" src/veracium/mcp_server.py` | no hits (exit 1; the bare "tok" grep hits `token_budget`, which is a recall input, not usage) |
| `_record` is the single fan-out to both sinks | `grep -n 'def _record' src/veracium/__init__.py` | line 102 |

---

## 3. Trust-class matrix — REQUIRED, blocking

This change performs **no operation on stored state** — it observes the
wrapper's usage counters after operations that are themselves fully specified
elsewhere. State-transition form over observation outcomes:

| operation outcome | token fields recorded |
|---|---|
| metered llm + counter, operation succeeds | the per-call deltas (non-negative ints) for the roles the operation used |
| metered llm, **no counter** | nothing — characters are not tokens and are never sent |
| unmetered llm (plain `Complete`) | nothing — usage is invisible by design, unchanged |
| operation raises | nothing recorded for that operation (the existing exception path is untouched) |
| any outcome, consent < 3 | the TELEMETRY collector accumulates nothing (record-time gating, 0015 I8); the local audit/introspect carriers are consent-independent by design — the §4f matrix is the total statement (external F6) |

Counting is class-blind and content-free: token counts carry no
`EvidenceAuthor`/`Disclosure` breakdown (enumerated from `schema.py:37-48`)
and no text. The four §3 questions: **No** to all — no write path, no
provenance, no `needs_confirmation`, no authority movement; I1's byte-identity
check from 0015 extends over metered runs (`test_metering_is_decision_invisible`).

**Write-time or maintain-time?** Neither — observation-time, after commit.

---

## 3b. Authorization and scope — *full specs only*

Analyzed at the information level (the 0015 §3b lesson), rewritten at
external round 1 (F1 overturned v3's analysis):

- **The withdrawn design's side channel, named plainly:** totals-snapshot
  deltas let user A's numbers absorb a concurrent user-B compile delta, and
  `compile.py` builds its measured input from B's stored facts and episodes —
  so the delta's size revealed prior-state information about another user.
  v3's "no supersession-oracle analog" and "single-Memory deployments avoid
  it" claims were both false (one `Memory` serves arbitrary `user_id`s, MCP
  included). **§4b closes the channel by construction:** attribution follows
  the calling thread's own operation context; no cross-user absorption path
  exists, and I9's barrier tests prove exact attribution rather than
  bounding a smear.
- **What the numbers reveal, per carrier (§4f):** the telemetry endpoint
  receives weekly per-install sums only under consent v3; the host audit
  sink and `introspect()` are the host's own LOCAL surfaces,
  consent-independent by design — consent governs what leaves the machine.
- **The model caller sees nothing:** `introspect` is not an MCP tool
  (§2c-ii); MCP results gain no usage fields
  (`test_mcp_results_carry_no_usage_fields`).
- **Erasure:** `forget(user_id)` deletes the user's accumulator entry (§4d)
  — after erasure `introspect(user_id)` reveals no usage record (external
  F5: persistence is irrelevant to the compliance promise).

## 4. Behaviour

### 4a. Opt-in — an affirmative capability, never a shape (external F2)

Metering detection is an AFFIRMATIVE, UNIQUE capability, not duck-typed
shape-probing (v3's `totals()`-shape detection is WITHDRAWN — a coincidental
`totals()` method on an unrelated `Complete` proves data shape, not host
intent, and would have been probed and routed): the `Metered` wrapper carries
`metering_capability = "veracium-metered-v1"` (a class-level string constant
no unrelated object plausibly carries) AND the registration method
`add_usage_listener(fn)`. `Memory` opts in by REGISTERING a listener — an
explicit interaction that cannot happen by coincidence — iff the capability
constant matches exactly. An object with a `totals()` method but no matching
capability is NEVER probed, NEVER invoked, NEVER routed
(`test_coincidental_totals_shape_is_never_invoked`).

### 4b. Attribution — per-call events on the operation's own thread (external F1)

**The totals-snapshot delta design (v1–v3) is WITHDRAWN in full.** The
reviewer reproduced both of its failures: factor-N overcounting under N
overlapping operations (two concurrent ops each observed the global delta),
and a CROSS-USER PRIOR-STATE side channel — a concurrent user-B compile delta
absorbed into user A's numbers reveals the size of what `compile.py` built
from B's stored facts and episodes. "Content-free" was not prior-state-free,
and v3's single-`Memory` mitigation claim was FALSE (one `Memory` serves
arbitrary `user_id`s, including over MCP).

The replacement is EXACT SCOPED ATTRIBUTION: the wrapper emits a per-call
usage event `{role, in_tok, out_tok}` SYNCHRONOUSLY on the thread making the
call, to each registered listener. `Memory` maintains a THREAD-LOCAL
operation-context stack — each public operation (`remember`/`answer`/
`recall`/`maintain`/…) pushes `(event, user_id)` on entry and pops on exit —
and the listener attributes the event to the TOP of the calling thread's
stack (nested operations: the innermost context wins, e.g. `answer → recall`
attributes the compile to the recall context it ran under, and the §2
event-field map routes it). A usage event arriving with NO context on its
thread (no public operation in progress) is attributed to nothing —
counted only in the wrapper's own host-side totals. Consequences, each a
named test (I9): two users' concurrent operations attribute EXACTLY (barrier-
controlled); nested `answer → recall` attributes once, to the inner context;
concurrent `recall.compile` vs `maintain.compile` never cross; no factor-N
inflation exists by construction; and NO cross-user absorption is possible —
the side channel is closed by construction, not bounded.

### 4c. The wrapper's atomic accounting (external F3)

`Metered.__call__` is re-specified (an amendment to the shipped wrapper,
landing with this spec's implementation): the provider is called first and
its output is ALWAYS returned — a counter failure never breaks the operation.
Both token counts are computed and validated INTO LOCALS, outside the usage
lock, with the counter wrapped: any exception, non-int, bool, or negative
from EITHER invocation (first or second) discards the WHOLE token pair — the
call mutates NO token state and emits NO usage event (all-or-nothing: a
partially-counted call cannot be honestly attributed; v3's "records nothing"
promise was placed AFTER the failure point, reviewer-reproduced with a
two-stage counter that broke the operation AND retained a partial record).
`calls` and the character counts (which cannot fail) are accounted in the
wrapper's always-valid block and are unaffected. Only after both counts
validate does the wrapper, under its lock, mutate totals and emit the event.

### 4d. The per-user accumulator — carrier, lifetime, erasure (external F5)

The introspection accumulator is constructed exactly: it lives ON THE
`Memory` INSTANCE (`Memory._llm_usage`, a dict keyed by `user_id` of
per-role `{calls, in_tok, out_tok}`), updated atomically under an
instance-level lock by the registered listener, and labeled
**`"scope": "instance-lifetime"`** in its own payload (v3's
"process-lifetime" was false for instance-local state; two `Memory`
instances have independent accumulators, stated). Growth is bounded by the
distinct `user_id`s the instance serves. **`forget(user_id)` DELETES the
user's accumulator entry in the same call** — compliance erasure covers
every per-user record this library holds, persisted or not; after
`forget()`, `introspect(user_id)` shows no usage (I8's erasure cell).
Restart/new instance ⇒ empty accumulators (the scope label says so).

### 4e. Self-check accounting — DECIDED: excluded, and stated (external F4; closes §10 Q3)

`Memory.self_check` runs synthetic probes through TEMPORARY throwaway
memories sharing the host's `llm`. Its distill/gate/compile calls are
DIAGNOSTIC, not user memory operations: they are EXCLUDED from per-user
attribution and from the telemetry payload BY DESIGN — the temporary
memories register no listener, and the outer `self_check` pushes a
`selfcheck` context that the §2 event-field map carries no token fields for,
so nothing attributes. The wrapper's own host-side totals still grow
(honest: the calls happened and cost money; the host sees them in
`totals()`). The consent text's scope ("your own model calls during
extraction, answering, and memory maintenance") therefore remains exact:
self-check usage never enters the payload. **I2b's completeness claim is
correspondingly scoped and mechanically backed (F4's second half): a
declarative PRODUCER REGISTRY** — `(role, event, callsite)` rows for the
four attributed pairs plus the named `selfcheck` exclusion — **asserted
against an AST-based scan of every `Complete`-invoking call site in
`src/veracium/`, resolving DEFAULT role values** (the literal `role="…"`
grep missed the protocol's `role="compile"` default — reviewer-caught), so
a new call site, a new role, or a default-role call breaks the test until
the registry decision is remade.

### 4f. The three-carrier consent matrix (external F6)

Consent semantics, stated once for ALL carriers — telemetry consent governs
what LEAVES the machine; the host's own local surfaces are independent of it
BY DESIGN, and every claim is scoped accordingly (the changelog and consent
text say "sent" about the telemetry endpoint only):

| carrier | unmetered | metered, consent <3 | metered, consent v3 |
|---|---|---|---|
| telemetry payload (leaves the machine, weekly) | no token fields | **no token fields** (record-time `FIELD_MIN_VERSION` gate, 0015 I8) | the eight fields |
| host audit sink (`_record` fan-out — the host's own local data) | no token fields (nothing measured) | token fields PRESENT — local, consent-independent, the host's own numbers | same |
| `introspect()` accumulator (local, instance-lifetime) | absent | PRESENT — local, consent-independent | same |

"Nothing accumulates" in the §3 matrix is corrected to its true scope: the
TELEMETRY collector accumulates nothing below v3; the local carriers are
consent-independent and say so (`test_carrier_consent_matrix` walks every
cell).

### 4g. Consent and interfaces (unchanged from v3 where not amended above)

`SCHEMA_VERSION` 2→3; `FIELD_MIN_VERSION` gains all EIGHT fields at 3; the
0015 machinery applies unchanged; the consent text enumerates the three
activities mapped onto the four pairs (§2). `introspect(user_id)` gains the
optional `"llm_usage"` block per §4d. The `Metered` docstring is rewritten
to the 4a/4c contract. No MCP surface changes. No store schema change; no
migration.

## 5. Regime analysis

- **Consent regimes:** all 0015 regimes re-run green plus: v2-consented
  (token fields stripped at telemetry record), v3-consented (sent), the
  v2→v3 transition through a live carrier — and the §4f carrier matrix's
  nine cells walked (`test_carrier_consent_matrix`).
- **Metering regimes:** unmetered · capability-present-but-unregistered
  (impossible by construction — registration IS detection) ·
  coincidental-`totals()` object (never invoked) · metered-no-counter
  (chars host-side, no events) · metered-with-counter · counter failing on
  first invocation · on second invocation (both atomic, operation
  unbroken).
- **Attribution regimes (I9, barrier-controlled):** two users concurrent —
  exact; nested `answer → recall` — inner context, once; concurrent
  `recall.compile` vs `maintain.compile` — never cross; a usage event with
  no operation context on its thread — wrapper totals only; `self_check` —
  excluded by design (§4e).
- **Lifecycle regimes (I8):** two `Memory` instances — independent
  accumulators; `forget(user_id)` — entry deleted, introspect empty;
  restart/new instance — empty (the scope label says instance-lifetime).

Release class: **stable** — every named regime has a CI-reachable test.

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| I1 — metering changes no stored byte and no decision: identical sequences metered vs unmetered produce identical stores and answers | `test_metering_is_decision_invisible` | CI |
| I2 — **no counter → no token telemetry**: character accounting never enters the payload under any field name (all eight fields, v3) | `test_no_counter_sends_no_token_fields` | CI |
| I2b — **the payload is COMPLETE over the (role, event) PAIRS, backed by the producer REGISTRY (v4, external F4)** | `test_token_payload_covers_every_role_event_pair` — the declarative registry (four attributed pairs + the named `selfcheck` exclusion) asserted against an AST scan of every `Complete`-invoking call site in `src/veracium/`, DEFAULT role values resolved; a new call site, role, or default-role call breaks it until the registry decision is remade | CI |
| I3 — the wrapper's accounting is ATOMIC and non-breaking (§4c, external F3) | `test_counter_failure_is_atomic_and_never_breaks_the_operation` — a counter raising/returning garbage on the FIRST or the SECOND invocation: the operation completes with the provider output, NO token state mutates, NO event emits, `calls`/chars unaffected | CI |
| I4 — the §4f carrier matrix holds (external F6) | `test_v2_consent_strips_token_fields` + `test_v2_to_v3_transition_through_a_live_memory_carrier` + `test_carrier_consent_matrix` (all nine cells: telemetry gated at record time; audit and introspect consent-independent and local) | CI |
| I5 — the consent-text pin is two-sided: "token" appears in `CONSENT_TEXT` iff the token fields are whitelisted AND populated | the FLIPPED `test_consent_text_token_mention_matches_the_payload` (replaces the one-sided pin, same file) | CI |
| I6 — whitelisted ⇒ populated (the `2767a35` gate) holds over all eight fields — the returning four and the four compile fields (v3) | `tests/test_telemetry_claims.py` (existing, starts passing for them) | CI |
| I7 — no MCP surface carries usage: `remember`/`answer` tool results and every MCP tool omit token fields; `introspect` remains non-MCP | `test_mcp_results_carry_no_usage_fields` + the §2c-ii grep pinned as a test | CI |
| I11 — opt-in is affirmative (§4a, external F2) | `test_coincidental_totals_shape_is_never_invoked` — an unrelated `Complete` with a valid-shaped `totals()` and no capability constant: never probed, never invoked, nothing routed; registration occurs iff the constant matches exactly | CI |
| I8 — the accumulator's lifecycle is constructed (§4d, external F5) | `test_usage_accumulator_lifecycle` — instance-lifetime label in the payload; lock-guarded concurrent updates; two instances independent; restart empty; **`forget(user_id)` deletes the entry and post-erasure `introspect` shows no usage**; absent entirely when unmetered | CI |
| I9 — attribution is EXACT (§4b, external F1) | `test_attribution_is_exact_under_concurrency` — barrier-controlled: two users' overlapping operations each attribute exactly their own calls (no factor-N, no absorption); nested `answer→recall` attributes once to the inner context; concurrent `recall.compile` vs `maintain.compile` never cross; a context-free event reaches only wrapper totals. Plus content-free: every emitted value is a non-negative int | CI |
| I10 — every 0015 invariant keeps running unmodified (this spec adds a version, not a mechanism) | the existing `test_0015_lifecycle.py` suite green with `SCHEMA_VERSION == 3` | CI |

**Reproducer retention:** review defects become regressions beside these.

---

## 7. Failure modes and reversibility

- **Silent failure:** under-counting — a failing counter drops that call's
  whole token pair, invisibly. Accepted and directional (we may
  under-report, never fabricate, never retain a PARTIAL record — external
  F3's reproduction is the named regression); I3 makes the drop
  deterministic, atomic, and tested.
- **Silent failure, the worse direction:** character counts leaking under
  token names — structurally closed (I2: the wrapper keeps chars under
  `in_chars`/`out_chars`, which are not whitelisted and gated off by name).
- **Reversibility:** fully — the memory store and the consent carriers are
  untouched beyond 0015's accepted behaviour; disabling metering (unwrap),
  telemetry, or consent each independently stops emission; the introspect
  block vanishes with the process.
- **Partial failure:** the listener is invoked synchronously but WRAPPED —
  a raising listener (or accumulator failure) records nothing for that call
  and never propagates into the operation; the wrapper's own accounting
  already committed atomically before the event was emitted.
- **Attack surface:** none added — no non-user content influences stored
  state, recall, or rendered context; the only new flows are non-negative
  ints to the host's own surfaces and a consent-v3-gated weekly aggregate.

---

## 8. Claims and limits

- **Changelog wording:** "Hosts that wrap their `Complete` with
  `veracium.llm.metered.Metered` and supply a token counter get exact
  per-user, per-role usage through `introspect()` (local,
  instance-lifetime), local audit records, and — separately, only under
  consent version 3, shown and accepted before anything LEAVES THE MACHINE
  — token-usage telemetry. Without a counter, nothing token-shaped exists
  anywhere — character counts stay in the wrapper, labelled as
  characters." (The sent-scoping is external F6's carrier split.)
- **What this does NOT establish:** token counts are the host's counter's
  opinion, not billing truth (no provider invoice is consulted); introspect
  totals are INSTANCE-lifetime, not history (two instances, two ledgers; a
  restart is a reset — the payload's scope label says so); self-check's
  diagnostic calls are excluded from attribution by design (§4e — the
  wrapper's host-side totals still see them); the audit/introspect carriers
  are local and consent-independent (§4f — consent governs the telemetry
  endpoint); and this spec does not persist usage — the durable per-user
  variant is §10 Q2's future decision. The v3 concurrency-smear limitation
  is GONE, not restated: attribution is exact by construction (§4b/I9).
- **Measurements:** none cited.

---

## 9. Brief for the external reviewer

Round 1 adopted BOTH of the previous §9's least-sure fallbacks as
requirements (the scoped per-call interface; the affirmative capability) —
they are now the §4a/§4b design. What v4 is least sure of: (1) the
THREAD-LOCAL context stack as the attribution scope — it is exact for the
codebase's synchronous call structure; if a future operation dispatches
llm calls to worker threads, the context would not follow, and the event
would fall to wrapper-totals-only (visible, not misattributed — but state
whether that failure direction is acceptable); (2) the AST-based default-
role resolution in I2b's registry check — is static resolution of default
parameters robust enough, or should the wrapper refuse a missing explicit
`role` outright? **What would change our minds:** if barrier tests show
the context stack leaking across any real async/thread boundary in the
shipped codebase, the fallback design is passing an explicit operation
token through the call chain — invasive but airtight.

## 10. Open questions

1. ~~Payload width~~ — **RULED (research: preliminary 2026-08-11; CONFIRMED
   IN PRINCIPLE and MAPPING-AMENDED by their internal round 1, 2026-08-13):
   COMPLETE, not restoration-scoped — and complete means every (role,
   event) PAIR, not every role.** The compile role has two producers, so
   the payload is `recall.compile_*` AND `maintain.compile_*` (v3, internal
   F1); research's own preliminary "joins as recall.compile_*" assumed a
   single producer and is amended by their review. | resolved |
2. **Persisted per-user usage** (durable history, `forget_user` integration,
   SCHEMA bump) — wanted? **Decides: Quentin, on demand. Class: deferred.**
3. ~~Should `selfcheck --push` include usage when metered?~~ **DECIDED at
   external round 1 (F4, §4e): self-check usage is EXCLUDED from per-user
   attribution and the telemetry payload by design (diagnostic calls
   through temporary memories, not user memory operations); the wrapper's
   host-side totals still see it. The consent text's activity scope stays
   exact.** | resolved |

---

## Reviewer checklist

- [ ] §3 has no unanswered cells, and is **directional** where the operation is
- [ ] §3's classes were read from the enums, not copied from the template
- [ ] Prohibitions AND the corresponding **permissions** are both tested
- [ ] Every default fails **closed**
- [ ] §2c has a row per uncontrolled input, and **no empty invariant cell**
- [ ] §2c-ii: every reach claim carries **the command**
- [ ] §2 consumers were enumerated by grep, not recall
- [ ] Every §6 invariant has a check that actually runs
- [ ] §5 regimes are reachable by tests, or the change is experimental
- [ ] §3b: no principal can see anything they could not see before
- [ ] §6 and §8 are filled in
- [ ] §10 questions each carry a class
- [ ] §8 states what this does *not* establish
- [ ] I have said where I think the **author's conclusion is wrong**
- [ ] I re-read the current version before reviewing
- [ ] §9 brief is written, and external review has been sent
