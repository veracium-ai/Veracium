# Feature spec: supersession / reinforcement telemetry counters

Spec-Status: draft

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v1 — *re-read before editing; quote the version you approve* |
| **Status** | *narrative only — canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (semantics; the consent question in §10 is theirs) · workflow-platform unavailable, waived: the only consumer-visible change is two additive int keys in `remember()`'s return dict — waiver held by dev |
| **External review** | required (full spec — touches `graph.py`, `ingest.py`, `__init__.py`); not yet sent |
| **Decision + date** | — |
| **Path** | full |

---

## 1. Problem and motivation

`supersessions` and `reinforcements` sat in the telemetry whitelist from its
introduction and were populated by **no call site anywhere** — discovered and
removed in `2767a35` ("telemetry: stop claiming to collect what we never
collected"), with an explicit obligation filed: these are the most
product-relevant counters we could send, because they measure the behaviour
veracium exists for — a changed value handled as change (supersession, history
retained) and a restatement handled as evidence (reinforcement, no currency
laundering). **If we do nothing:** opted-in telemetry can say how often facts
are extracted and quarantined but nothing about whether anyone's data ever
*exercises* the supersession machinery — the one adoption question the
counters were designed to answer — and the filed obligation from `2767a35`
rots.

The removal commit names why this needs a spec rather than a drive-by:
`apply_supersession` knows what it did but returns `None`, so the counts must
be threaded through `graph.py` and `ingest.py`, both guarded trust-surface
files.

**Alternatives rejected:**

- **Count at the store layer from `SupersessionResult`.** The store's result
  carries `invalidated: int`, which **conflates** `superseded` with
  `absorbed_duplicate`; and a committed reinforcement plan is **structurally
  identical** to a plain accumulation plan (`insert_incoming=True`, no
  invalidations, no upserts) — only the planner's branch knows which it was.
  Counting must happen where the classification exists: the planner.
- **A plan-transient marker field on `SupersessionPlan`.** Rejected:
  `SupersessionPlan` feeds the 0014 v2 outcome digest and the snapshot
  verification (`verify_snapshot_against_plan`); adding any field to that
  carrier invites digest/verification drift, for zero benefit when a return
  value from `_build_supersession_plan` suffices. (§6 pins the digest basis
  anyway, so a future field addition fails a check rather than a review.)
- **Emit the new counters immediately to already-consented installs.** The
  operative consent promise is arguably the *class* ("ONLY aggregate
  counters… NEVER your memory"), under which two more counters are covered.
  Rejected as the default: `2767a35`'s lesson is that the consent dialog is
  the worst place for any mismatch with code, in either direction. Default is
  **fail-closed consent versioning** (§4); the class-consistency reading is
  §10's question for research.
- **Also count absorptions and refusals.** Deferred. Scope here is exactly
  the two fields removed in `2767a35`; widening the payload is a new consent
  discussion, not a restoration.

---

## 2. Field contracts touched

No **stored** field is touched — this change persists nothing (§3). The
contracts touched are in-memory/interface carriers:

| field | read / written | its **documented** contract | every other consumer | preserved? |
|---|---|---|---|---|
| `ingest_event()` return dict | written: gains `"supersessions"`, `"reinforcements"` (ints) | "a small summary dict (counts + the episode) for logging/telemetry" (`ingest.py:118-119`) | `__init__.py:155` (sole caller; feeds `_record` and returns to `remember()`'s caller) | yes — additive keys, counts |
| `remember()` return dict | written: same two keys pass through | public API + MCP `remember` tool return (`mcp_server.py:64` returns it to the model caller) | `cli.py:184`, `selfcheck.py:71`, tests | yes — additive; content-free ints, nothing for a model caller to launder |
| `apply_supersession()` return | `None` → `SupersessionCounts` | docstring says nothing about a return today | sole caller `ingest.py:204` (verified §2c-ii) | yes — every existing caller ignores the value |
| `EVENT_FIELDS["ingest"]` | written: re-add the two names | "whitelist of scalar fields per event; anything not listed is silently dropped" | `Collector.record/snapshot` (`telemetry.py:117-140`), `tests/test_telemetry_claims.py` (fails on any whitelisted-but-unpopulated field) | yes — both fields are populated by this change, which is what the test demands |
| `TelemetryConfig.schema_version` | read: gains a second meaning | today: payload format stamp only | `preview()` payload; `load()`/`save()` | **changed** — it becomes the **consented** schema version (§4); the new meaning is documented at the field and enforced by the §6 gate |
| `CONSENT_TEXT` | written: enumeration extended | the consent claim; `test_telemetry_claims.py` pins that it may not over-claim | `prompt_consent()`, telemetry CLI | yes — text and payload move together in this change |

Consumers enumerated mechanically — commands and results in §2c-ii.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| telemetry config file (host disk) | defaults: disabled, nothing sent | `load()` swallows and returns defaults: disabled | extra keys ignored by dataclass merge | a hand-edited file **missing `schema_version`** must not read as current-version consent | **absent/invalid `schema_version` resolves to 1 (least-favourable: pre-this-spec consent), never to the current default** — `load()` gains an explicit floor; `test_absent_schema_version_reads_as_v1` |
| extractor output (drives how many edges reach `apply_supersession`) | 0 triples → both counters 0 | counts are `len()` of planner lists — ints by construction; `Collector.record` coerces and **drops** non-numerics | n/a — counts never carry extractor strings | a hostile event can inflate its own user's counts, nothing else; no content enters the payload | `record()` whitelist + numeric coercion (existing, `telemetry.py:121-131`); `test_counters_are_content_free` asserts payload contains no strings |
| data written by an older version (legacy v1 receipts → replay path) | — | — | — | a replayed operation must not count as fresh work | **replays count zero**: both replay branches return `SupersessionCounts(0, 0, replayed=True)`; `test_replay_counts_zero` covers phase-1 and phase-2 replay |
| store apply result (`PLAN_STALE` loop) | — | — | — | a plan retried N times must count once | counts are computed **only from the attempt whose result is a fresh commit**; `test_plan_stale_retry_counts_once` |
| host audit sink (receives the same fields dict) | — | sink exceptions swallowed (`__init__.py:109-113`, existing) | — | sink is host-chosen and user-scoped; it already receives every ingest count | no new mechanism needed — the sink sees the host's own data for its own user; named in §4 so the carrier is not silent |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | result |
|---|---|---|
| `apply_supersession` has exactly one caller | `grep -rn "apply_supersession(" src/veracium/ \| grep -v "def apply_supersession\|apply_supersession_plan"` | `ingest.py:204` only |
| the only ingest telemetry record site is `remember()` | `grep -rn 'record("ingest"' src/veracium/` | `__init__.py:162` only |
| `telemetry.py` is **not** a guarded file | `grep -c "telemetry" specs/check_spec_reference.py` | `0` |
| the MCP `remember` tool returns the ingest dict to the model caller | `grep -n "return mem.remember" src/veracium/mcp_server.py` | line 64 |
| `correct()` does not route through `apply_supersession` (so corrections do not count here) | `grep -n "apply_supersession" src/veracium/__init__.py` | no hits |
| every config `save()` writes `schema_version` (so absence occurs only via hand-editing) | `grep -n "asdict(self)" src/veracium/telemetry.py` | line 106 (`save()` serialises the full dataclass) |
| reinforcement's committed plan shape is indistinguishable from accumulation (why the planner must classify) | `grep -n "insert_incoming=True" src/veracium/graph.py` | both the reinforcement early-return and the ordinary-branch plan constructor |

---

## 3. Trust-class matrix — REQUIRED, blocking

This change performs **no operation on stored state**: it observes the outcome
of operations `0003`/`0012`/`0014` already specify, after the store has
committed (or replayed, or refused) them. The applicable form is the
state-transition table over **observation outcomes** (unary; the per-class
write behaviour itself is specified and tested in `0003` §4f, `0012` Design 1,
`0014` §4b and is byte-unchanged by this spec — §6 check 1 enforces exactly
that):

| outcome of `apply_supersession` | `supersessions` counts | `reinforcements` counts |
|---|---|---|
| fresh commit, plan had invalidations with reason `superseded` | `+len(reason=='superseded')` | 0 |
| fresh commit, planner took the reinforcement branch | 0 | +1 |
| fresh commit, absorption (`absorbed_duplicate` invalidations) | 0 (absorption is out of scope, §1) | 0 |
| fresh commit, plain accumulation / first fact | 0 | 0 |
| phase-1 replay (receipt matched before planning) | 0 | 0 |
| phase-2 replay (store returned `replayed=True`) | 0 | 0 |
| refusal rows in the committed plan | not counted (out of scope, §1) | — |
| `PLAN_STALE` attempt (superseded by a retry) | 0 for that attempt — only the committing attempt counts | same |
| any exception (integrity error, store failure) | nothing recorded — the exception propagates as today | same |

Counting is **class-blind by design**: a supersession counts identically
whichever `EvidenceAuthor` × `Disclosure` pair (enumerated from
`schema.py:37-48`: `USER`/`THIRD_PARTY`/`SYSTEM` ×
`MENTIONABLE`/`USE_ONLY`/`QUARANTINED`) produced it, because the payload
carries no class breakdown — adding one would let a weekly aggregate say
"this install's third-party mail superseded user facts N times", which is
more than a content-free counter should say. Directionality therefore does
not arise in the payload; it remains fully specified where it matters, in
`0003`'s own matrix.

The four required questions:

- **Can this cause a user-asserted fact to become non-assertable?** No — no
  write path is touched; §6 check 1 asserts store-state byte-identity against
  the pre-change behaviour for the same ingest sequence.
- **Can non-user content gain user-grade authority, confidence, or
  currency?** No — same mechanism.
- **Can it clear `needs_confirmation`?** No — nothing here writes edges;
  `0008`'s only-confirm()-clears invariant is untouched (and its existing
  tests keep running).
- **Does it merge, drop, or overwrite provenance?** No — provenance is
  neither read nor written; counts derive from plan invalidation *reasons*
  and the planner branch, not from provenance fields.

**Write-time or maintain-time?** Neither — observation-time. It grants no
currency, confidence, or flag change anywhere, so the T2 distinction is
satisfied trivially; the §6 byte-identity check is the proof rather than this
sentence.

---

## 3b. Authorization and scope — *full specs only*

- **Cross-boundary?** No new boundary is crossed. The telemetry payload is
  per-install, carries no user ids (`Collector` never sees one —
  `__init__.py:104-106` passes only the fields dict), and the two new fields
  are aggregate ints like the nine existing ingest/recall fields.
- **Who may see it?** (1) The anonymous telemetry endpoint, only when the
  host opted in AND configured an endpoint AND the consented version admits
  the fields (§4). (2) The host's own audit sink, which already receives
  every ingest counter for its own users — no change in who sees what.
  (3) The `remember()` caller (including the MCP model caller) sees two more
  ints about the write it itself just performed.
- **Scope change behaviour?** n/a — no sharing/revocation surface is
  touched.
- **Anything newly visible to a principal who couldn't see it before?** No —
  every recipient above already receives this event's counter dict; the dict
  gains two content-free members.

---

## 4. Behaviour

**`graph.py`** — `_build_supersession_plan` additionally returns whether it
took the reinforcement branch (internal signature:
`(plan, is_reinforcement)`); `apply_supersession` returns a frozen
`SupersessionCounts(superseded: int, reinforced: int, replayed: bool)`
computed **only from a fresh commit**: `superseded` = the committed plan's
invalidations with reason `superseded`; `reinforced` = 1 iff the planner took
the reinforcement branch; both replay branches return zeros with
`replayed=True`. No store call, no plan content, and no persisted byte
changes.

**`ingest.py`** — `ingest_event` sums the per-edge counts and returns them as
`"supersessions"` / `"reinforcements"` in its summary dict.

**`__init__.py`** — `remember()` passes both counts into
`_record("ingest", …)`, which fans out to (a) the telemetry `Collector`
(whitelist-filtered, anonymous) and (b) the host's audit sink (user-scoped,
host-owned) — both named here so neither carrier is silent.

**`telemetry.py`** (not guarded) — `EVENT_FIELDS["ingest"]` re-adds the two
names; the explanatory comment block from `2767a35` is updated to record that
the spec landed rather than deleted. `SCHEMA_VERSION` becomes 2.
`TelemetryConfig.schema_version` is documented as **the version of the
consent text the operator accepted**: `prompt_consent()` and
`set_enabled(True)` stamp the current version; `load()` floors an
absent/invalid value to 1. `preview()` (which `flush_if_due` posts verbatim)
**strips any field whose minimum schema version exceeds the consented one**
(`FIELD_MIN_VERSION = {("ingest","supersessions"): 2,
("ingest","reinforcements"): 2}`) — so an install that consented to the v1
text never sends the new fields until someone re-enables against the v2 text.
`CONSENT_TEXT` extends its enumeration ("…how often facts are extracted,
claims quarantined, values superseded or reinforced, and answers
abstained…").

**Interfaces:** `remember()`'s return dict (public API, CLI `remember`, MCP
tool) gains the two int keys — additive. No CLI, export, or store format
change. **Migration:** none — nothing persisted changes; v1-consented configs
keep working and simply send the v1 field set. Nothing is unrecoverable.

---

## 5. Regime analysis — where does this behave differently?

- **Scale:** counting is O(len(prior_invalidations)) per edge on lists the
  planner already built; no store reads added. No threshold or cap
  interaction (`max_subgraph_edges` etc. are recall-side).
- **The regimes that matter are outcome regimes, and the tests reach each
  one** (§6): fresh commit with supersessions; reinforcement; absorption
  (asserting zero); phase-1 replay; phase-2 replay (persisted-effects AND
  legacy v1-receipt reconstruction); the `PLAN_STALE` retry loop (reaching a
  genuine retry requires the store-level contention fixture from
  `test_0014_receipt_split.py`, reused).
- **Consent regimes:** v1-consented config (fields stripped), v2-consented
  (fields sent), config with absent `schema_version` (floored to 1,
  stripped), fresh consent (stamped 2). All four are cheap unit fixtures.
- **Cold vs warm:** no difference — counters are per-call derived values;
  the weekly aggregation semantics are the existing `Collector`'s.

Release class: **stable** — every named regime has a test in §6.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| I1 — counting changes no stored byte: an identical ingest sequence produces identical edges, receipts, refusals, and ledger rows before/after this change | `test_counting_is_pure_observation` — run the 0012/0014 fixture sequence, dump all tables, compare against the same sequence with telemetry disabled; plus the existing 0012 I1–I6 and 0014 suites staying green | CI |
| I2 — replays count zero (both phases, both replay forms incl. legacy v1 receipts) | `test_replay_counts_zero` | CI |
| I3 — a `PLAN_STALE` retry counts once | `test_plan_stale_retry_counts_once` | CI |
| I4 — `superseded + absorbed == SupersessionResult.invalidated` on every fresh commit (the classification is exhaustive over invalidations) | `test_counts_partition_invalidated` (property-style over the plan fixtures) | CI |
| I5 — reinforcement counts come from the planner branch, not plan shape: a plain accumulation commit counts `(0,0)` even though its plan is shape-identical | `test_accumulation_counts_zero_reinforcements` | CI |
| I6 — the v2 outcome digest basis is unchanged: the pinned 0014 digest vectors still verify, and `SupersessionPlan` gained no field | pinned-vector tests in `test_0014_receipt_split.py` (existing) + `test_supersession_plan_fields_pinned` (asserts the exact field list) | CI |
| I7 — whitelisted ⇒ populated (the `2767a35` gate) | `tests/test_telemetry_claims.py` (existing — starts passing for the re-added fields, keeps failing for any future aspirational field) | CI |
| I8 — consent-version fail-closed: v1-consented and absent-version configs never emit the new fields; `preview()` == what `flush` posts | `test_v1_consent_strips_new_fields`, `test_absent_schema_version_reads_as_v1`, `test_preview_is_what_flush_posts` | CI |
| I9 — content-free: the ingest payload contains only int/float/bool values under every fixture | `test_counters_are_content_free` | CI |
| I10 — consent text and payload move together: `CONSENT_TEXT` mentions supersession/reinforcement iff the fields are whitelisted and populated | extend `test_telemetry_claims.py`'s existing text-pin | CI |

Standing checks that must not regress: injection asserts 0 · cross-user leaks
0 · trust canaries 0 · supersession probes pass · malformed edges 0.

**Reproducer retention:** any defect found in review lands as a regression
test beside these.

---

## 7. Failure modes and reversibility

- **Silent failure:** the counters under-count (a branch returns zeros it
  shouldn't) — invisible in the payload because zero is a legal value. First
  symptom: an install known to exercise supersession reports zeros, possibly
  weeks later. Mitigation is I4 (the partition equality makes a dropped
  supersession count a test failure, not a telemetry mystery) and I5
  (the branch-classification pin).
- **Over-count risk:** replays or retries double-counting — pinned by I2/I3.
- **Reversibility:** fully — nothing is persisted; disabling telemetry (or
  removing the fields from the whitelist) reverts the observable surface.
  The consent-version floor means even a rollback to v1 code leaves nothing
  inconsistent (old code ignores `schema_version` beyond the payload stamp).
- **Partial failure:** `_record` already swallows telemetry and audit-sink
  exceptions (`__init__.py:104-113`); an exception inside `apply_supersession`
  propagates exactly as today, with nothing recorded for the failed call —
  no retry-into-empty-success path exists.
- **New attack surface:** none — no non-user content can influence stored
  state, recall selection, or rendered context through this change; the only
  new data flow is two ints moving outward through carriers that already
  exist, gated by the same whitelist and consent machinery.

---

## 8. Claims and limits

- **Changelog wording:** "Opt-in telemetry can now report how often values
  are superseded and reinforced — the counters the consent dialog's
  'aggregate counters' always intended. Installs that consented before this
  version keep sending exactly the old field set until telemetry is
  re-enabled against the updated consent text."
- **What this does NOT establish:** it does not measure supersession
  *correctness* (the 0003/0012/0014 suites do); it does not make telemetry
  users comparable (installs differ in workload); a zero does not mean the
  machinery is broken (most corpora legitimately never supersede); the
  counters say nothing about which trust classes were involved, by design
  (§3). The consent-version gate covers **veracium's own dialog**; where a
  host obtained end-user consent through its own UI, honouring the widened
  payload against that consent is the host's obligation, not discharged
  here.
- **Measurements:** none cited — no numbers appear in this spec.

---

## 9. Brief for the external reviewer

- **Least sure of, one:** the **consent-versioning boundary** — we gate on
  the version stamped at veracium's own consent prompt, but `set_enabled()`
  is also callable programmatically by hosts who never showed our text.
  Does stamping v2 on any `set_enabled(True)` overclaim what the *end user*
  agreed to?
- **Least sure of, two:** the claim that a **committed reinforcement plan is
  structurally indistinguishable from accumulation** rests on today's plan
  shape (§2c-ii last row). If a future spec adds a distinguishing persisted
  fact, the planner-branch return becomes redundant but not wrong — is the
  redundancy a defect or a margin?
- **Where we may have overstated:** "no new attack surface" (§7) — two ints
  flow to the MCP model caller; we believe count-of-own-write is inert, but
  an adversarial-composition argument we missed would change §3b.
- **What would change our minds:** if the reviewer finds any path where the
  counts differ from the committed store facts (an I4 violation we didn't
  enumerate), the counting moves from the planner into the store layer and
  this spec gets a v2 with a different §1 trade-off.
- **Reviewer-safe copy:** not needed — no competitive-audit detail or
  unpublished findings appear here.

---

## 10. Open questions

1. **Does the class-consistency reading of the existing consent ("ONLY
   aggregate counters") permit sending the new fields to v1-consented
   installs without re-consent?** The spec's default answers no (fail-closed
   versioning, §4); if research rules the class reading sufficient, the
   `FIELD_MIN_VERSION` gate simplifies away. **Decides: research** (consent
   text is a public claim). **By: before acceptance. Class: blocking.**
2. **Should `set_enabled(True)` stamp the current consent version when
   called programmatically (host code, no dialog shown)?** Options: stamp
   always (simple, may overclaim end-user consent) · stamp only via the CLI
   path where the text was displayed (stricter, splits the API). **Decides:
   research proposes, dev implements. By: before acceptance. Class:
   blocking** (it determines the §4 mechanism's shape).
3. **Absorption/refusal counters** — worth a future spec once these two
   fields have shipped and someone wants them? **Decides: dev, on demand.
   Class: deferred.**

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
