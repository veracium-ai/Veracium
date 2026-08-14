# Feature spec: token-usage telemetry over the Metered wrapper

Spec-Status: draft
Spec-Requires: 0015

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v8 — EXTERNAL ROUND 4 (6 blocking + 2 editorial; the false-CI blocker CLOSED; direction endorsed): ALL FOLDED. **R4-1 (D):** §4a claimed §2c carried the registration control-plane rows — it did not (my own claims-vs-content miss) → the rows EXIST now, with the handle-validity predicate (opaque, non-None, from a non-raising call), register-then-raise → FAILED registration with the retained callback INERT, and `close()` always closing the store. **R4-2 (B):** events were uncorrelated with their causing call — a rogue capability could REPLAY a retained callback into another user's same-`(event, role)` operation → the Memory-side single-shot EXPECTATION token armed around each provider invocation; replays and re-entrant emissions drop (no armed/consumed expectation); no trust in the capability required. **R4-3 (B+compliance, reviewer-reproduced — the audit-the-fix's-own-state lesson one level DEEPER than R3-5):** the frame carried raw `user_id` into copied contexts that reset cannot reach → the frame is exactly `(owner, op_token)`, opaque; ALL user-bearing state lives in the enumerable, erasable Memory-owned ACTIVE-OPERATION REGISTRY; copied contexts hold only meaningless tokens (this also discharges R3-2 structurally). **R4-4 (A+C):** forget vs merge was check-then-act → ONE instance lock, four ATOMIC transitions (register / delete+cancel / check+merge / finally-cleanup), ordering exact. **R4-5 (D — the I-table sweep miss, third instance in this spec):** I8 still specified the withdrawn generations and the un-narrowed close rule → rewritten to the actual token state machine, every residual carrier incl. copied contexts, the exact post-close boundary. **R4-6 (C):** `self_check` had no representable frame (no `user_id`) → it pushes NO frame; context-free events reach wrapper totals only; the absence boundary is a named cell. **R4-7/8 (editorial):** the §4d heading and §9 refreshed. *(v7: the module-global routing variable; recursive immutability; pair validation; the control plane — claimed; cancellation tokens; the shared predicate; successful-operation scoping.)* *(v5: the pre-send `contextvars` substitution + emit-boundary clause.)* *(v4:)* — EXTERNAL ROUND 1 (6 bin-(a), bin (b) empty; the consent-v3 reuse and the corrected compile mapping endorsed as directionally sound): ALL FOLDED — and this is a REDESIGN round: the reviewer adopted BOTH of §9's recorded fallbacks as requirements. **F1 (class A+B, overturns v3's §3b):** totals-snapshot deltas reproduced factor-N overcounting AND a cross-user PRIOR-STATE side channel (a concurrent user-B compile delta reveals the size of what `compile.py` built from B's stored facts; v3's single-`Memory` mitigation was FALSE — one instance serves arbitrary `user_id`s incl. MCP) → the design is WITHDRAWN for §4b's per-call events attributed via an operation-context stack (`contextvars.ContextVar` — the v5 primitive) — exact by construction, barrier-tested (I9). **F2 (class B+E):** duck-typed `totals()` shape is not intent → §4a's affirmative capability constant + listener registration; a coincidental `totals()` is never invoked (I11). **F3 (class A+G, reviewer-reproduced against the SHIPPED wrapper):** the counter fired unprotected inside the lock — the operation broke and a partial record survived → §4c's atomic all-or-nothing accounting (both counts validated into locals; either invocation failing discards the pair, emits nothing, returns the provider output; `calls`/chars ride the always-valid block). **F4 (class C):** I2b missed `self_check`'s reach (temporary memories driving distill/gate/compile) and the protocol's DEFAULT `role="compile"` → §4e DECIDES: self-check excluded by design (closes §10 Q3), and I2b is backed by a declarative producer REGISTRY asserted against an AST call-site scan resolving default roles. **F5 (class A+C):** the accumulator had no construction → §4d: `Memory`-instance carrier, lock-guarded, `"instance-lifetime"` (the process-lifetime label was false), and **`forget(user_id)` deletes the entry — compliance erasure covers unpersisted state too**. **F6 (class D):** consent semantics disagreed across carriers → §4f's explicit three-carrier × consent matrix; "sent" scoped to the telemetry endpoint; audit/introspect stated consent-independent-and-local by design. *Miss diagnosed: v3 restated F1's smear honestly but never re-derived WHAT the smeared bytes measure (compile input = prior store state) — the §3b information-not-carrier lesson one level deeper; and the F3 guarantee was written where the code wasn't (claims-vs-code inside the spec's own wrapper).* *(v3 history: internal round 1 — the two-producer mapping, pair-granular I2b, the honest smear restatement.)* |
| **Status** | *narrative only — canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research — round 1 RETURNED 2026-08-13 (3 findings, folded in v3; their preliminary Q1 mapping amended by their own review); re-review requested · workflow-platform unavailable, waived: no consumer-visible API change beyond an optional `introspect()` block — waiver held by dev |
| **External review** | ROUND 4 RETURNED 2026-08-14 (package `0017-v7-20260814T0002Z.tar.gz`): 6 blocking + 2 editorial, folded as v8; round-5 package next |
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
  per-call events with `contextvars`-scoped operation context.
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
| the routing context, registry, and accumulator | NEW state (§4b/§4d): ONE MODULE-GLOBAL `contextvars.ContextVar` holding fully-immutable `(owner, op_token)` frames — NO user-bearing state in any context (R4-3); the Memory-owned ACTIVE-OPERATION REGISTRY (op_token → user/event/buffer/cancelled) + `Memory._llm_usage`, both under ONE instance lock with the §4d atomic transitions; the context-scoped single-shot EXPECTATION token around each provider call (R4-2); listener HANDLES with the R4-1 validity predicate, idempotent removal, `close()` unsubscription | the listener (validated attribution), the terminal merge, `introspect()`, `forget()`, `close()` |
| `introspect()` return | written: an optional `"llm_usage"` block (per-role calls + tokens, `"scope": "instance-lifetime"` in the payload — v3's process-lifetime label was false for instance-local state) | the transparency surface; consent-INDEPENDENT local carrier (§4f) | host API + CLI `introspect` (NOT an MCP tool — §2c-ii); absent when unmetered; empty for a forgotten user |

Consumers enumerated mechanically — commands in §2c-ii.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| the host's `counter` callable | no counter → no token fields ever (chars stay host-side) | non-int / bool / negative / NaN / raising — on EITHER invocation, incl. the second | — | a two-stage counter that succeeds once then raises (the reviewer's F3 reproduction: the operation broke and a partial record survived) | **atomic all-or-nothing accounting (§4c): both counts computed and validated into locals OUTSIDE the lock; any failure discards the whole token pair, mutates no token state, emits no event; the provider output is ALWAYS returned; `calls`/chars ride the always-valid block** — `test_counter_failure_is_atomic_and_never_breaks_the_operation` (both invocation positions) |
| an unrelated object with a coincidental `totals()` method | — | — | duck-typed hosts | a valid-SHAPED `totals()` on a non-Metered object (F2: shape is not intent) | **never probed, never invoked, never routed — opt-in is the affirmative capability constant + listener registration (§4a)**; `test_coincidental_totals_shape_is_never_invoked` |
| **the callback protocol** (an arbitrary callable CAN present the capability string, retain the listener, and invoke it with garbage — R2-6) | non-mapping → dropped | missing/extra keys · non-int/bool/negative counts · counts > 2**53 → dropped | a role outside the producer registry → dropped | malformed data injected DURING a live operation | **listener-side FAIL-CLOSED validation before any state (§4a): drop silently, never attribute, never raise into the operation**; one adversarial cell per malformed form in `test_listener_validates_fail_closed` (stage-5 obligation) |
| **the registration control plane** (external R4-1 — §4a claimed these rows existed; they did not) | capability present, `add_usage_listener` ABSENT → treated unmetered, never probed again | `add_usage_listener` RAISES, or returns an invalid handle (None/non-opaque) → registration is FAILED — the `Memory` treats itself unregistered; a callback the rogue object retained anyway is INERT (no armed expectation, no owned frame — nothing can attribute) | a duplicate or malformed handle passed to `remove_usage_listener` → isolated no-op | `remove_usage_listener` absent or RAISING during `Memory.close()` | **handle validity is a predicate (opaque, non-None, returned by a non-raising call); every failure is isolated; `close()` runs unsubscribe in its own try and ALWAYS closes the store**; the §4a snapshot boundary governs in-flight emissions |
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

### 4a. Opt-in, registration, and the callback protocol (external R1-F2, R2-3, R2-4, R2-6)

Metering detection is an AFFIRMATIVE capability: the `Metered` wrapper
carries `metering_capability = "veracium-metered-v1"` and
`add_usage_listener(fn) -> handle`. `Memory` opts in by REGISTERING iff the
constant matches exactly; a coincidental `totals()` shape is never probed,
invoked, or routed (I11).

**The registration lifecycle is constructed (R2-3):** `add_usage_listener`
returns an opaque HANDLE; **`remove_usage_listener(handle)` exists and is
idempotent; `Memory.close()` unsubscribes its own listener idempotently**
(today `close()` only closes the store — the amendment is part of this
spec's implementation). A `Memory` constructed with the INTERNAL
non-registering parameter (`_register_metering=False`) never subscribes —
the §4e self-check path uses it. Repeated self-checks therefore cannot grow
the wrapper's listener set, and a closed `Memory` stops receiving callbacks
(both named I8/I2b-family checks).

**Emission never holds the wrapper lock (R2-4):** the wrapper commits its
totals and SNAPSHOTS the listener list under the lock, RELEASES it, then
invokes each listener synchronously OUTSIDE the lock with per-listener
exception isolation (one raising listener neither starves later listeners
nor reaches the operation). Concurrent add/remove semantics are snapshot
semantics: a listener added during an emission sees the next event; one
removed during an emission may still receive the in-flight event, never a
later one. A listener that re-enters the wrapper (calls `totals()`,
registers, unregisters) therefore cannot deadlock.

**The registration CONTROL PLANE is itself an untrusted input (external
R3-4):** a matching capability with a missing or raising
`add_usage_listener` → the `Memory` treats the object as UNMETERED (no
registration, no probing retries, one debug-visible fact); a raising
`remove_usage_listener`, or a malformed/duplicate handle → the failure is
ISOLATED and `Memory.close()` STILL closes the store (unsubscribe runs in
its own try; store closure is never lost to a listener failure). **The
closed-`Memory` guarantee is narrowed to what snapshot semantics can
honestly deliver: a closed `Memory` receives no callbacks from emissions
snapshotted AFTER close; an emission already snapshotted in flight may
deliver once** (close does not wait for callback quiescence — the
alternative, a quiescence barrier in `close()`, is rejected as a deadlock
surface). §2c carries the control-plane rows.

**The callback protocol is a validated, untrusted input (R2-6 — a matching
capability string is affirmative intent, not identity; an arbitrary object
can present it and feed the listener garbage):** the event is exactly the
mapping `{"role": str, "in_tok": int, "out_tok": int}`. The listener
validates FAIL-CLOSED before touching any state: a non-mapping, missing or
extra keys, a `(current_frame.event, role)` pair not in the §4e producer
registry (external R3-3 — role-set membership alone let an adversarial
capability object emit `role="gate"` during an `ingest` frame: recognized
globally, invalid for the event; the PAIR is the unit of validity),
non-`int` counts (`bool` excluded), negatives, or counts failing the §4c
SHARED validity predicate are DROPPED silently — nothing attributes,
nothing raises into the operation; every recognized-role × wrong-event
cross-product is a named fail-closed cell. The §2c
matrix carries one adversarial row per malformed form.

### 4b. Attribution — owned frames, buffered aggregation, one terminal merge (external R2-1, R2-2)

The context primitive is **ONE MODULE-GLOBAL `contextvars.ContextVar`**,
shared by every `Memory` in the process and read by every listener
(external R3-1 — the reviewer executed the predicate: with per-instance
variables, the round-2 shared-wrapper trace STILL double-attributes,
because each listener reads its own variable's top frame and each sees a
frame it owns; one shared routing variable accepted the event only in the
correct Memory). It holds an IMMUTABLE frame value, pushed with `set()`
and restored with the returned token in a `finally` (never a mutated
shared list — mutation is not async-safe). **The frame carries an OWNER (R2-1 — the round-2 trace:
two Memories sharing one wrapper, a provider that re-enters the second
Memory mid-call, and a broadcast event double-attributed to both users,
restoring exactly what round 1 removed):**

    frame = (owner: the registering Memory's identity, op_token: opaque)

**The frame carries NO user-bearing state (external R4-3 — reviewer-
reproduced: `copy_context()` copies the frame, and resetting the parent
cannot erase the copies, so a raw `user_id` in the frame survived
`forget()` — the erasure fix's own state violating erasure, one level
deeper than R3-5):** the frame is exactly `(owner, op_token)`, fully and
trivially immutable; `op_token` is an opaque one-operation identifier
meaningless outside this instance. Everything user-bearing — `user_id`,
the event name, the per-role BUFFER — lives in the Memory-owned
**ACTIVE-OPERATION REGISTRY**, keyed by `op_token`: enumerable, erasable,
lock-guarded (§4d). A copied context retains only the meaningless token;
after `forget()` erases the registry entries, no copy anywhere resolves to
a user. (This also discharges R3-2's recursive-immutability demand
structurally: the immutable thing carries nothing mutable, and the
deliberately-mutable buffer is ordinary lock-guarded instance state with
stated ownership.) Adversarial copied-context and recursive-immutability
regressions are named I9/I8 cells.

**Event correlation — the EXPECTATION TOKEN (external R4-2: an event
carrying only `{role, in_tok, out_tok}` can be REPLAYED — a rogue
capability retains Alice's callback and invokes it later while Bob's
same-`(event, role)` frame is active, charging Bob):** the `Memory` arms a
context-scoped, SINGLE-SHOT expectation immediately around each of its own
provider invocations (`expecting = fresh call-id` set before the `llm(...)`
call in the operation's context, cleared in a `finally`); the listener
accepts an event ONLY while the calling context's expectation is armed,
and consumes it (at most one token-pair event per armed call). Delayed
replays arrive with no armed expectation and drop; listener-triggered
re-entrant wrapper calls arrive under a consumed or absent expectation and
drop; a genuine `Metered`'s synchronous emission always lands inside the
window. The boundary is Memory-side and mechanical — it requires no
cooperation from the (untrusted) capability object.

**Aggregation and the single commit (R2-2):** validated events accumulate
into the registry entry's per-role buffer (under the instance lock); at
operation exit the buffer merges EXACTLY ONCE into the operation's
existing terminal `_record` — one audit line per operation, telemetry `n`
incremented once. **A failed operation records NOTHING (decided): the
raise-path discards the entry** — telemetry/audit/introspection are
SUCCESSFUL-OPERATION-scoped (§8, changelog); wrapper totals remain
call-scoped and show real spend including failures.

**The context-entering operation set is EXACT: `remember`, `answer`,
`recall`, `maintain` push frames. `self_check` pushes NO frame (external
R4-6 — it has no `user_id`, and a frame schema requiring one cannot
represent it):** its temporary memories do not register (§4e), its events
arrive context-free and reach only wrapper totals; the absence-boundary
test asserts the routing variable holds no frame during `self_check` and
nothing attributes. This set and the §4e producer registry are
MECHANICALLY COMPARED (I2b).

### 4c. The wrapper's atomic accounting (external R1-F3; emit boundary per §4a)

`Metered.__call__`: the provider is called first and its output is ALWAYS
returned. Both token counts are computed and validated into locals OUTSIDE
the usage lock, the counter wrapped, against **ONE SHARED count-validity
predicate used identically at the wrapper AND the listener (external
R3-6 — v6's split rule let a genuine counter returning `2**53 + 1` commit
to wrapper totals while the listener dropped the same event: a
split-brain): valid ⇔ `type(x) is int` ∧ `0 ≤ x ≤ 2**53`.** Any failure
of the predicate — exception, non-int, bool, negative, or over-limit —
from EITHER invocation discards the whole token pair BEFORE any
token-state mutation or emission; a genuine `Metered` therefore never
emits an event the listener considers malformed (the listener's §4a
revalidation is defense in depth against non-genuine producers, using
the same predicate). A malformed INJECTED event is dropped individually
and never erases previously valid events in the operation buffer (the
round-3 poison ruling). `calls` and the character counts ride the
always-valid block. Only after both counts validate does the wrapper
commit totals and snapshot listeners under its lock, release, and emit per
§4a. **The emit boundary is a contract clause: the event is emitted in the
context that ENTERED `__call__` — at return, on the caller's side — so a
host `Complete` that internally fans out to workers still attributes to
the calling operation's context.**

### 4d. The registry, one atomic lock discipline, and erasure (external R4-3/R4-4; R4-7's heading fixed)

The ACTIVE-OPERATION REGISTRY and the per-user accumulator
(`Memory._llm_usage`) are instance state under **ONE instance lock, and
the four transitions are each ATOMIC under it (external R4-4 — the
check-then-act race: a merge that observed not-cancelled, a `forget()`
that deleted+cancelled between, and the merge recreating the entry):**

1. **operation start:** register the entry `(op_token → user_id, event,
   buffer, cancelled=False)`;
2. **`forget(user_id)`:** in one critical section, delete the user's
   accumulator entry AND mark every registry entry for that user
   cancelled — never two separate acquisitions;
3. **terminal merge:** in one critical section, check the entry's
   cancelled flag AND (iff clear) merge the buffer into the accumulator —
   the check and the write are never separated;
4. **operation exit (`finally`):** remove the registry entry.

Ordering is thereby exact: a `forget` acquiring the lock before the merge
wins (the merge sees cancelled and discards); a merge holding the lock
completes and the subsequent `forget` deletes what it merged. After
`forget()` + quiescence NO per-user residue exists in ANY carrier — the
accumulator, the registry, and (per §4b) every copied context, which
holds only opaque tokens. The accumulator remains
`"scope": "instance-lifetime"` in its payload; two instances independent;
restart empty; growth bounded by served users.

### 4e. Self-check accounting — excluded, and now constructible (external R2-3)

`self_check`'s temporary memories are constructed through the explicit
non-registering path (`_register_metering=False` — §4a): they never
subscribe, so nothing attributes, the listener set does not grow across
repeated runs, and the wrapper's host-side totals still see the diagnostic
calls (honest — they cost money). The consent text's activity scope stays
exact. **The producer registry (R1-F4, simplified per the round-2 §9
ruling):** a declarative `(role, event, callsite)` registry for the four
attributed pairs plus the named `selfcheck` exclusion, asserted against an
AST scan of every in-tree `Complete` invocation — and **every in-tree
production invocation MUST pass an explicit `role=`; the AST check REJECTS
omissions** (general static default-resolution is abandoned as open-ended —
the public wrapper keeps its default for host compatibility only).

### 4f. The FOUR-column carrier matrix (external R1-F6, R2-7)

| carrier | unmetered | metered, NO counter | metered + counter, consent <3 | metered + counter, consent v3 |
|---|---|---|---|---|
| telemetry payload (leaves the machine) | no token fields | no token fields (no token events exist) | **no token fields** (record-time `FIELD_MIN_VERSION` gate, 0015 I8) | the eight fields |
| host audit sink (local) | none | none — chars stay in the wrapper, never event-shaped | token fields present — local, consent-independent | same |
| `introspect()` accumulator (local, instance-lifetime) | absent | absent | present — local, consent-independent | same |

Metered-without-counter emits NO token events anywhere (the §3/§5/§8 rule,
now a matrix column rather than a contradiction of one);
`test_carrier_consent_matrix` walks all twelve cells.

### 4g. Consent and interfaces

`SCHEMA_VERSION` 2→3; `FIELD_MIN_VERSION` gains all EIGHT fields at 3; the
0015 machinery applies unchanged (`Spec-Requires: 0015` — the design
mechanically depends on its persisted consent version, record-time gate,
adoption transitions, and carrier semantics). `introspect(user_id)` gains
the optional `"llm_usage"` block per §4d. The `Metered` docstring is
rewritten to the §4a/§4c contract. No MCP surface changes; no store schema
change; no migration.

## 5. Regime analysis

- **Consent regimes:** all 0015 regimes re-run green plus: v2-consented
  (token fields stripped at telemetry record), v3-consented (sent), the
  v2→v3 transition through a live carrier — and the §4f carrier matrix's
  twelve §4f cells walked (`test_carrier_consent_matrix`, a stage-5 obligation).
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
- **Lifecycle regimes (I8):** two `Memory` instances — independent;
  `forget(user_id)` — the atomic delete+cancel; the merge-vs-forget barrier
  race; copied contexts hold only opaque tokens; restart empty; the
  post-close snapshot boundary.

Release class: **stable on acceptance** — every named regime has a NAMED check; the checks marked stage-5 obligations do NOT yet exist (external round 2's package blocker: v5 claimed them as CI — the packaged suite validates the existing product, not this proposed redesign; implementation makes them real, and acceptance is what authorizes it).

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| I1 — metering changes no stored byte and no decision: identical sequences metered vs unmetered produce identical stores and answers | `test_metering_is_decision_invisible` | **stage-5 obligation — does NOT exist yet** |
| I2 — **no counter → no token telemetry**: character accounting never enters the payload under any field name (all eight fields, v3) | `test_no_counter_sends_no_token_fields` | **stage-5 obligation — does NOT exist yet** |
| I2b — the payload is COMPLETE over the (role, event) PAIRS, registry-backed (§4e; the round-2 §9 ruling) | `test_token_payload_covers_every_role_event_pair` — the declarative registry (four pairs + the `selfcheck` exclusion) asserted against an AST scan of every in-tree `Complete` invocation; **every production invocation must pass explicit `role=` — the scan REJECTS omissions** (default-resolution abandoned); the registry and the §4b context-entering set MECHANICALLY COMPARED; **plus the thread-fanout gate: the scan rejects any thread/executor dispatch inside a context-entering operation path until it propagates context via `copy_context().run(...)` or an explicit token** | **stage-5 obligation — does NOT exist yet** |
| I3 — the wrapper's accounting is ATOMIC, non-breaking, and lock-safe (§4c + §4a; external R2-4) | `test_counter_failure_is_atomic_and_never_breaks_the_operation` (both invocation positions) + **the deadlock cell: a listener that calls `totals()`, re-enters, or unregisters during emission completes without deadlock (emission outside the lock; per-listener exception isolation)** | **stage-5 obligation — does NOT exist yet** |
| I4 — the §4f carrier matrix holds | `test_v2_consent_strips_token_fields` + `test_v2_to_v3_transition_through_a_live_memory_carrier` + `test_carrier_consent_matrix` (all TWELVE §4f cells) | **stage-5 obligation — none of the three exists yet** |
| I5 — the consent-text pin is two-sided: "token" appears in `CONSENT_TEXT` iff the token fields are whitelisted AND populated | the FLIPPED `test_consent_text_token_mention_matches_the_payload` (replaces the one-sided pin, same file) | **stage-5 obligation — the flip does not exist yet; the current pin asserts the OPPOSITE and stays green until implementation** |
| I6 — whitelisted ⇒ populated (the `2767a35` gate) holds over all eight fields | `tests/test_telemetry_claims.py` EXISTS, but its current assertions REQUIRE the token fields to remain absent — the future condition (passing FOR them) is a **stage-5 obligation**; today it is the guard that keeps this spec unimplemented until accepted |
| I7 — no MCP surface carries usage: `remember`/`answer` tool results and every MCP tool omit token fields; `introspect` remains non-MCP | `test_mcp_results_carry_no_usage_fields` + the §2c-ii grep pinned as a test | **stage-5 obligation — does NOT exist yet** |
| I11 — opt-in is affirmative (§4a, external F2) | `test_coincidental_totals_shape_is_never_invoked` — an unrelated `Complete` with a valid-shaped `totals()` and no capability constant: never probed, never invoked, nothing routed; registration occurs iff the constant matches exactly | **stage-5 obligation — does NOT exist yet** |
| I8 — erasure and lifecycle hold over the ACTUAL state machine (§4b/§4d; rewritten by external R4-5 after v7's row still described the withdrawn generation design) | `test_usage_accumulator_lifecycle` — the four atomic transitions under one lock; the R4-4 barrier race (merge-vs-forget interleaving CANNOT recreate an erased entry); after `forget()` + quiescence EVERY carrier is inspected empty: accumulator, registry, cancel marks — and a COPIED CONTEXT retains only opaque tokens that resolve to nothing (R4-3's reproduction as the named cell); instance-lifetime label; two instances independent; restart empty; `self_check` pushes no frame and attributes nothing (R4-6's absence boundary); **the post-close boundary exactly as §4a states it: no callbacks from emissions snapshotted after close; one in-flight snapshotted emission may deliver** | **stage-5 obligation — does NOT exist yet** |
| I9 — attribution is EXACT (§4b) | `test_attribution_is_exact_under_concurrency` — barrier-controlled: two users' overlapping operations; nested `answer→recall`; concurrent `recall.compile` vs `maintain.compile`; the shared-wrapper re-entry trace under the module-global routing variable; **the REPLAY cell (R4-2): a retained callback invoked outside any armed expectation — and during another user's same-`(event, role)` operation — attributes NOTHING**; a listener-triggered re-entrant call drops (consumed expectation); a context-free event reaches only wrapper totals | **stage-5 obligation — does NOT exist yet** |
| I10 — every 0015 invariant keeps running unmodified (this spec adds a version, not a mechanism) | the existing `test_0015_lifecycle.py` suite EXISTS and is green today with `SCHEMA_VERSION == 2`; green-under-3 is the future condition — a **stage-5 obligation** |

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
  block is instance-lifetime state and vanishes with its instance (§4d).
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
  per-user, per-role usage of SUCCESSFUL Veracium operations through
  `introspect()` (local, instance-lifetime) and local audit records —
  actual spend including failed operations stays visible in the wrapper's
  own `totals()` — and, separately, only under consent version 3 (shown
  and accepted before anything LEAVES THE MACHINE), token-usage
  telemetry. Without a counter, nothing token-shaped exists anywhere —
  character counts stay in the wrapper, labelled as characters.
- **What this does NOT establish:** token counts are the host's counter's
  opinion, not billing truth; **every attributed number is SUCCESSFUL-
  OPERATION usage, not total model spend (external R3-7): a provider call
  inside an operation that subsequently fails contributes NOTHING to
  telemetry, audit, or introspection — hosts wanting actual spend
  including failures read the wrapper's own `totals()`, which is
  call-scoped and sees everything**; introspect totals are
  INSTANCE-lifetime, not history; self-check's diagnostic calls are
  excluded from attribution by design (§4e); the audit/introspect
  carriers are local and consent-independent (§4f); **telemetry
  aggregation rides accepted 0015's collector, which accumulates numeric
  fields as floats — individual events are exact under the §4c predicate
  (≤ 2**53), but a weekly AGGREGATE that itself exceeds 2**53 loses
  integer exactness in the payload (external R3-6; bounded, stated —
  integer-preserving accumulation would amend accepted 0015 and is
  deliberately not proposed)**; and this spec does not persist usage —
  the durable per-user variant is §10 Q2's future decision. The v3
  concurrency-smear limitation is GONE, not restated: attribution is
  exact by construction over successful operations (§4b/I9).
- **Measurements:** none cited.

---

## 9. Brief for the external reviewer

What v8 is least sure of (the resolved owner/capability questions are
gone — external R4-8): (1) the EXPECTATION TOKEN as the correlation
boundary (§4b) — single-shot, context-scoped, armed around each
Memory-initiated provider call; is at-most-one-event-per-armed-call the
right cardinality for a provider that legitimately retries internally, or
does a genuine wrapper retry need a re-armable window (the failure
direction as specified: the retry's second emission drops — undercounting,
never misattribution)? (2) the registry as the sole user-bearing carrier —
§4d's four atomic transitions are the complete write set to our reading;
the adversarial question is whether any OTHER path can write user-keyed
usage state outside the lock. **What would change our minds:** if the
expectation-token boundary proves too coarse for real providers, the
fallback is wrapper-issued per-call tokens validated against a
Memory-side issued-set — heavier, and it re-introduces trust in the
capability object, which is why it is not the primary design.

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
