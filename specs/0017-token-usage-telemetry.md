# Feature spec: token-usage telemetry over the Metered wrapper

Spec-Status: draft

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v1 — *re-read before editing; quote the version you approve* |
| **Status** | *narrative only — canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (consent semantics + the honest-labels rule are theirs) · workflow-platform unavailable, waived: no consumer-visible API change beyond an optional `introspect()` block — waiver held by dev |
| **External review** | required (full spec — touches `__init__.py`, `introspect.py`); not yet sent |
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
  v1's `introspect()` totals are **process-lifetime, in-memory**, stated as
  such; a persisted variant is a successor decision (§10 Q2).
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
| `EVENT_FIELDS["ingest"]` / `["answer"]` | written: re-add the four token fields | whitelist; anything unlisted is dropped at record | `Collector.record/snapshot`; `tests/test_telemetry_claims.py` (whitelisted ⇒ populated) | yes — populated by this change, which is what the gate demands |
| `FIELD_MIN_VERSION` | written: the four fields at min version **3** | 0015: a field is sent only if recorded under a consent that admits it | `Collector.record` (the binding gate), `_payload` (defense-in-depth) | yes — the 0015 mechanism reused unchanged |
| `SCHEMA_VERSION` | 2 → **3** | the current consent-text version; stamped only by affirmative display flows (0015 I13) | `prompt_consent`, `accept_current_consent`, the payload stamp | yes — one more version through the same machinery |
| `CONSENT_TEXT` | written: token sentence returns, scoped | the consent claim; `test_consent_text_does_not_promise_token_totals` PINS that "token" is absent until fields are whitelisted AND written | `prompt_consent()`, CLI enable | **the pin test flips direction in the same commit** (I5): text mentions tokens iff whitelisted and written — both now true |
| `Metered.totals()` | read: the usage source | host-side accounting only (`metered.py` docstring says nothing writes to telemetry/audit/introspect) | hosts; `tests/test_metered.py` | **changed** — the docstring's "host-side only" paragraph is REWRITTEN by this spec: a `Memory` whose `llm` exposes the `Metered` surface reads per-operation deltas; the wrapper itself still never pushes |
| `Memory.remember()`/`answer()` internals | written: per-operation usage deltas into `_record` | `_record` fans out to telemetry (whitelist-gated) + the host audit sink | both sinks (existing carriers, named per 0015) | yes — two more int fields through the existing dict |
| `introspect()` return | written: an optional `"llm_usage"` block (per-role calls + tokens, process-lifetime) | the transparency surface | host API + CLI `introspect` (NOT an MCP tool — §2c-ii) | yes — additive, absent when unmetered |

Consumers enumerated mechanically — commands in §2c-ii.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| the host's `counter` callable | no counter → **no token fields recorded at all** (chars stay host-side) | non-int / negative / NaN / raising counter | — | a counter returning garbage must not poison the payload | **a per-call delta is recorded iff it is a non-negative `int` (`bool` excluded); anything else — including a raising counter — records NOTHING for that call and never breaks the operation** (`test_garbage_counter_records_nothing_and_never_raises`) |
| the wrapped `complete`'s shape | — | an `llm` with a `totals` attribute that is not `Metered`'s contract (wrong shape, raising) | duck-typed hosts | a hostile `totals()` | **usage is read ONLY when `totals()` returns the documented dict shape; any exception or shape mismatch → no usage recorded, the operation unaffected** (`test_totals_shape_mismatch_is_ignored`) |
| concurrent operations sharing one wrapper | — | — | — | two threads' deltas interleave | **the delta read is documented per-`Memory`-operation; cross-thread attribution error is bounded to MISCOUNTING between roles of concurrent ops, never content, never negative totals** — stated as a §5 regime with its limitation in §8, clamped non-negative (`test_concurrent_ops_never_produce_negative_deltas`) |
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
| any outcome, consent < 3 | nothing accumulates (record-time gating, 0015 I8) |

Counting is class-blind and content-free: token counts carry no
`EvidenceAuthor`/`Disclosure` breakdown (enumerated from `schema.py:37-48`)
and no text. The four §3 questions: **No** to all — no write path, no
provenance, no `needs_confirmation`, no authority movement; I1's byte-identity
check from 0015 extends over metered runs (`test_metering_is_decision_invisible`).

**Write-time or maintain-time?** Neither — observation-time, after commit.

---

## 3b. Authorization and scope — *full specs only*

Analyzed at the information level (the 0015 §3b lesson):

- **What the new numbers reveal:** how many tokens the *host's own model
  calls* consumed, per role, per user. Recipients: (1) the telemetry endpoint
  — weekly per-install sums, only under consent v3; (2) the host audit sink —
  the host's own data; (3) `introspect()` — host API and CLI only.
- **The model caller sees nothing new:** `introspect` is not an MCP tool
  (§2c-ii), and the MCP `remember`/`answer` results gain no usage fields —
  there is nothing to strip because nothing is added there. **No
  supersession-oracle analog exists**: token counts derive from the host's
  own calls, not from prior store state — a per-write token count reveals
  prompt/output SIZE, which the model caller already knows (it produced the
  output). Stated for completeness, enforced by the no-new-MCP-fields test
  (`test_mcp_results_carry_no_usage_fields`).
- **Per-user introspect totals** are visible to whoever can call
  `introspect(user_id)` — the same principal that can already read that
  user's entire memory; usage numbers are strictly less than what it can
  already see.
- **Scope change behaviour:** n/a. **Anything newly visible to a principal
  that couldn't see it before:** no.

---

## 4. Behaviour

**Detection (opt-in, duck-typed, fail-closed):** a `Memory` whose `llm`
exposes the `Metered` surface (`totals()` in the documented shape) reads a
**per-operation delta**: snapshot totals before the operation, subtract
after, validate every delta (non-negative int, bool excluded), and pass the
valid ones into `_record` — `ingest` carries `distill_in_tok`/
`distill_out_tok`; `answer` carries `gate_in_tok`/`gate_out_tok`. Any
exception or shape mismatch anywhere in that read records nothing and never
propagates (telemetry never breaks the host). An unmetered `llm` is a
complete no-op — no probing beyond one `getattr`.

**Consent (the 0015 machinery, one more version):** `SCHEMA_VERSION` 2→3;
`FIELD_MIN_VERSION` gains the four fields at 3; the record-time gate,
epoch/lock/tombstone lifecycle, display-flow-only stamping, and every 0015
invariant apply unchanged. `CONSENT_TEXT` regains a token sentence, scoped
honestly: *"token totals for your own model calls — only when you opt into
metering"*. The `test_consent_text_does_not_promise_token_totals` pin FLIPS
in the same commit to its two-sided form: the text mentions tokens **iff**
the fields are whitelisted and populated (both now true) — the gate keeps
biting in both directions.

**Introspect (step 3):** `introspect(user_id)` gains an optional
`"llm_usage"` block — per-role `{calls, in_tok, out_tok}` accumulated
**in-memory for this process's lifetime**, plus `"scope":
"process-lifetime"` so the boundary is in the payload itself, not only in
docs. Absent entirely when the `llm` is unmetered or no counter was
supplied. Not persisted; `forget_user` untouched (nothing stored).

**`Metered`'s docstring** is rewritten: the "host-side only / nothing writes
to telemetry" paragraph becomes the 0017 contract (the wrapper still never
pushes; the `Memory` pulls deltas when metering is active).

**Interfaces:** the host-API `introspect()` return gains the optional block;
CLI `introspect` prints it when present; **no MCP surface changes**.
**Migration:** none for the memory store; the consent carriers
(`schema_version`, `consent_epoch`) behave per accepted 0015 — v2-consented
installs keep sending the v2 field set until the v3 text is displayed and
accepted.

---

## 5. Regime analysis

- **Consent regimes:** all 0015 regimes re-run green plus: v2-consented
  (token fields stripped at record), v3-consented (sent), the v2→v3
  transition through a live carrier (the I8 test pattern re-instantiated for
  version 3).
- **Metering regimes:** unmetered · metered-no-counter · metered-with-counter
  · garbage counter · raising totals — each a §2c/§6 test.
- **Concurrency regime:** two threads sharing one wrapper — deltas may
  misattribute BETWEEN concurrent operations' roles (documented, §8) but
  never go negative and never leak content (`test_concurrent_ops_never_
  produce_negative_deltas`). This is the regime the tests can reach; the
  per-operation-delta design is single-writer per `Memory` op by
  construction.
- **Cold vs warm:** the 0015 restart rule applies unchanged; the introspect
  block resets with the process (stated in its own payload).

Release class: **stable** — every named regime has a CI-reachable test.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| I1 — metering changes no stored byte and no decision: identical sequences metered vs unmetered produce identical stores and answers | `test_metering_is_decision_invisible` | CI |
| I2 — **no counter → no token telemetry**: character accounting never enters the payload under any field name | `test_no_counter_sends_no_token_fields` | CI |
| I3 — delta validity is closed: non-negative int (bool excluded) per delta; garbage/raising counters and malformed `totals()` record nothing and never raise into the operation | `test_garbage_counter_records_nothing_and_never_raises` + `test_totals_shape_mismatch_is_ignored` | CI |
| I4 — consent v3 gating: v1/v2-consented installs never accumulate the token fields; the v2→v3 live-carrier transition sends only post-acceptance values | `test_v2_consent_strips_token_fields` + `test_v2_to_v3_transition_through_a_live_memory_carrier` | CI |
| I5 — the consent-text pin is two-sided: "token" appears in `CONSENT_TEXT` iff the token fields are whitelisted AND populated | the FLIPPED `test_consent_text_token_mention_matches_the_payload` (replaces the one-sided pin, same file) | CI |
| I6 — whitelisted ⇒ populated (the `2767a35` gate) holds over the four fields | `tests/test_telemetry_claims.py` (existing, starts passing for them) | CI |
| I7 — no MCP surface carries usage: `remember`/`answer` tool results and every MCP tool omit token fields; `introspect` remains non-MCP | `test_mcp_results_carry_no_usage_fields` + the §2c-ii grep pinned as a test | CI |
| I8 — the introspect block is honest about scope: present iff metered-with-counter, carries `"scope": "process-lifetime"`, resets with the process, absent from `forget_user`'s domain (nothing persisted) | `test_introspect_usage_block_scope_and_absence` | CI |
| I9 — content-free: every emitted value is int/float/bool; concurrent deltas clamp non-negative | `test_token_payload_is_content_free` + `test_concurrent_ops_never_produce_negative_deltas` | CI |
| I10 — every 0015 invariant keeps running unmodified (this spec adds a version, not a mechanism) | the existing `test_0015_lifecycle.py` suite green with `SCHEMA_VERSION == 3` | CI |

**Reproducer retention:** review defects become regressions beside these.

---

## 7. Failure modes and reversibility

- **Silent failure:** under-counting — a raising counter or shape mismatch
  records nothing, invisibly. Accepted and directional (we may under-report,
  never fabricate); I3 makes the drop deterministic and tested rather than
  accidental.
- **Silent failure, the worse direction:** character counts leaking under
  token names — structurally closed (I2: the wrapper keeps chars under
  `in_chars`/`out_chars`, which are not whitelisted and gated off by name).
- **Reversibility:** fully — the memory store and the consent carriers are
  untouched beyond 0015's accepted behaviour; disabling metering (unwrap),
  telemetry, or consent each independently stops emission; the introspect
  block vanishes with the process.
- **Partial failure:** the delta read sits inside the existing
  `_record`-adjacent try/except discipline — any failure records nothing for
  that operation and the operation itself is untouched.
- **Attack surface:** none added — no non-user content influences stored
  state, recall, or rendered context; the only new flows are non-negative
  ints to the host's own surfaces and a consent-v3-gated weekly aggregate.

---

## 8. Claims and limits

- **Changelog wording:** "Hosts that wrap their `Complete` with
  `veracium.llm.metered.Metered` and supply a token counter can now opt into
  token-usage telemetry (consent version 3 — shown and accepted before
  anything is sent) and read per-user, per-role usage through
  `introspect()`. Without a counter, nothing token-shaped is ever sent —
  character counts stay in the wrapper, labelled as characters."
- **What this does NOT establish:** token counts are the host's counter's
  opinion, not billing truth (no provider invoice is consulted); introspect
  totals are process-lifetime, not history; concurrent operations sharing
  one wrapper may misattribute deltas between roles (bounded, non-negative,
  content-free); telemetry token sums are not comparable across installs
  (different counters); and this spec does not persist usage — the durable
  per-user variant is §10 Q2's future decision.
- **Measurements:** none cited.

---

## 9. Brief for the external reviewer

- **Least sure of, one:** the **duck-typed detection boundary** — `Memory`
  reads `totals()` from anything exposing the documented shape. Is
  shape-validation (I3) sufficient against a host object that *coincidentally*
  has a `totals()` method, or does the spec need an explicit opt-in marker
  attribute on the wrapper?
- **Least sure of, two:** the **concurrency limitation's honesty** — we
  document between-role misattribution under concurrent ops and clamp
  non-negative. Is "bounded, content-free miscounting" an acceptable stated
  limit, or does it need a per-operation wrapper handle to be sound?
- **Where we may have overstated:** "no supersession-oracle analog exists"
  (§3b) — we argue token counts reveal only sizes the model caller already
  knows; if a composition exists where per-role deltas leak prior-state
  information to any untrusted surface, §3b needs the 0015 treatment.
- **What would change our minds:** if delta-reading proves unreliable under
  the host's real threading patterns, the fallback design is the wrapper
  exposing an explicit per-call event hook instead of totals-deltas — a v2
  with a different §1 trade-off.
- **Reviewer-safe copy:** not needed.

---

## 10. Open questions

1. **Should the `answer` event also carry `compile`-role tokens** (the wiki
   recompile cost), or stay scoped to the four restored fields? Restoration
   scope says the four; the compile role is the actually-expensive one.
   **Decides: research (payload width is a consent claim). Class: blocking.**
2. **Persisted per-user usage** (durable history, `forget_user` integration,
   SCHEMA bump) — wanted? **Decides: Quentin, on demand. Class: deferred.**
3. **Should `selfcheck --push` include usage** when metered? **Decides: dev
   at implementation if research rules it inside the v3 consent's class.
   Class: pre-release.**

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
