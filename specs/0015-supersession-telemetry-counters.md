# Feature spec: supersession / reinforcement telemetry counters

Spec-Status: draft

| | |
|---|---|
| **Author / session** | dev |
| **Version** | v10 — *re-read before editing; quote the version you approve*. v9→v10: EXTERNAL ROUND 7 (4 bin-(a), all in the consent lifecycle) + **the PROCESS R3 CONSOLIDATION, armed last round and triggered**: rounds 3–7 layered the lifecycle until two of dev's own fixes contradicted each other (R7-1: the terminal matrix returns True on post-send lock failure while the older lock paragraph and I17 said False/"nothing sent") — §4's lifecycle paragraphs are REPLACED by one consolidated contract (persisted state · ONE portable lock · transitions · adoption · the flush algorithm with the under-lock STATUS read R7-2 requires · the endorsed authorization claim). R7-3: the lock is decided IN the spec, not deferred — an atomic O_CREAT|O_EXCL lockfile, one code path on every platform (the CI regime that runs IS the regime that ships; former §10 Q4 CLOSED), stale-break at 10 s as the documented portability trade, TelemetryLockError for explicit transitions. R7-4: the last "non-negative" carrier → positive int, zero invalid, everywhere. I17 rewritten to the split failure classes. Standing closures unchanged |
| **Status** | *narrative only — canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research — reviewed 2026-08-11, returned one amendment (folded in v2) · workflow-platform unavailable, waived: the only consumer-visible change is two additive int keys in the host-API `remember()` return — waiver held by dev |
| **External review** | required (full spec). R1: 3 → v4. R2: 5 + blocker → v5. R3: 4 → v6. R4: 3 → v7. R5: 3 → v8. R6: 3 → v9. R7 (v9): 4 bin-(a), no blocker → v10 = the round-8 resubmission, carrying the PROCESS-R3 lifecycle consolidation |
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
- **Return the counts in the MCP tool result (with the oracle disclosed).**
  Rejected (internal review): a per-write count is a supersession oracle over
  prior store state (§3b), the model caller is the one principal that cannot
  otherwise derive it, and the feature loses nothing by omission — telemetry
  aggregates are computed host-side before the MCP layer returns anything.

---

## 2. Field contracts touched

No **memory-store** field is touched — no edge, episode, graph row, or store
format changes (§3). The consent design persists TWO things (R2-5 + R4-2)
in `telemetry.json`: `schema_version` (accepted consent) and `consent_epoch`
(the transition counter) — disabling telemetry erases neither. The other
contracts are in-memory/interface carriers:

| field | read / written | its **documented** contract | every other consumer | preserved? |
|---|---|---|---|---|
| `ingest_event()` return dict | written: gains `"supersessions"`, `"reinforcements"` (ints) — **at BOTH constructor sites: the normal return AND the unparseable early return (`ingest.py:158-173`), int zero there (F3)** | "a small summary dict (counts + the episode) for logging/telemetry" (`ingest.py:118-119`) | `__init__.py:155` (sole caller; feeds `_record` and returns to `remember()`'s caller) | yes — additive keys, counts |
| `remember()` return dict | written: same two keys pass through on the **host-API path only** | public API return; the MCP `remember` tool (`mcp_server.py:64`) **strips both keys** before returning to the model caller — a per-write count is a supersession oracle (§3b), and the model must not see it | `cli.py:184-189` consumes the dict but prints its own fixed summary ("remembered: N facts, M quarantined") — **CLI OUTPUT IS UNCHANGED by this spec (R2-3)**; `selfcheck.py:71`; tests | yes — additive for the host-API caller only; CLI text and the untrusted MCP view both unchanged (§6 I11) |
| `apply_supersession()` return | `None` → `SupersessionCounts` | docstring says nothing about a return today | sole caller `ingest.py:204` (verified §2c-ii) | yes — every existing caller ignores the value |
| `EVENT_FIELDS["ingest"]` | written: re-add the two names | "whitelist of scalar fields per event; anything not listed is silently dropped" | `Collector.record/snapshot` (`telemetry.py:117-140`), `tests/test_telemetry_claims.py` (fails on any whitelisted-but-unpopulated field) | yes — both fields are populated by this change, which is what the test demands |
| **`TelemetryConfig.consent_epoch` (NEW, R4-2)** | persisted; bumped by every real consent transition under the lock | none today — new field | `adopt_consent` (mismatch → discard; invalidity seen at adoption NORMALIZES under lock before adopting), the pre-send recheck, `load()` (absent/invalid → normalized under lock to a fresh persisted NONZERO epoch before any collector exists), the v1 loader (unknown key → whole-config disabled defaults on rollback) | new contract, fully stated in §4; I16/I17 |
| `TelemetryConfig.schema_version` | read+**persisted** (R2-5): gains a second meaning, written to `telemetry.json` on affirmative acceptance | today: payload format stamp only | `preview()` payload; `load()`/`save()`; `Collector` (holds it; `adopt_consent`) | **changed** — it becomes the **consented** schema version (§4), persisted as the cross-restart consent carrier; disable does NOT erase it; enforced by I8/I13/I16 |
| `CONSENT_TEXT` | written: enumeration extended | the consent claim; `test_telemetry_claims.py` pins that it may not over-claim | `prompt_consent()`, telemetry CLI | yes — text and payload move together in this change |

Consumers enumerated mechanically — commands and results in §2c-ii.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| telemetry config file (host disk) | defaults: disabled, nothing sent | `load()` swallows and returns defaults: disabled | **an UNKNOWN key discards the WHOLE config to disabled defaults** — reproduced (R2-4): the dataclass constructor raises on unexpected kwargs and `load()` falls back; fail-closed (an enabled config with a typo key goes disabled, losing nothing but sending nothing) — DOCUMENTED as the chosen behaviour, not key-filtering | a hand-edited file **missing or invalid `schema_version`** must not read as current-version consent | **`schema_version` valid iff a positive `int` (`bool` excluded) ≤ `SCHEMA_VERSION`, else 1; `consent_epoch` valid iff a positive `int` (`bool` excluded) — absent/invalid is NORMALIZED UNDER LOCK to a fresh persisted nonzero epoch BEFORE any collector exists (R5-2: 0 is not a sentinel — a legacy enabled config would otherwise construct a live epoch-0 collector and hand-edits could ABA at 0); invalid seen at adoption → unconditional discard** — parametrized `test_invalid_schema_version_reads_as_v1`, `test_legacy_enabled_config_epoch_is_normalized_before_collection`, `test_absent_or_invalid_epoch_aba_discards` (I16) + `test_unknown_config_key_fails_closed_whole_config` |
| the consent response (stdin at the prompt) (R2-4) | empty answer → not affirmative → version 1 | unknown text ("maybe", garbage) → not affirmative → 1 | mixed-case affirmative ("Y", "YES", "Yes") → affirmative per the frozen accept-set {y, yes} case-insensitive → stamp current | EOF / interrupt / non-interactive → never affirmative → 1 | **only the frozen affirmative set stamps** — I13's parametrization covers every listed response class |
| extractor output (drives how many edges reach `apply_supersession`) | 0 triples → both counters 0 | counts are `len()` of planner lists — ints by construction; `Collector.record` coerces and **drops** non-numerics | n/a — counts never carry extractor strings | (a) a hostile event can inflate its own user's counts, nothing else; no content enters the payload. (b) **the supersession oracle** (research, internal review): a hostile event that also controls what the model reports could read a non-zero per-write count as "my injected claim conflicted with existing memory" — prior-state information | (a) `record()` whitelist + numeric coercion (existing, `telemetry.py:121-131`); `test_counters_are_content_free`. (b) **the MCP tool result carries neither key** — §6 I11 |
| data written by an older version (legacy v1 receipts → replay path) | — | — | — | a replayed operation must not count as fresh work | **replays count zero**: both replay branches return `SupersessionCounts(0, 0, replayed=True)`; `test_replay_counts_zero` covers phase-1 and phase-2 replay |
| store apply result (`PLAN_STALE` loop) | — | — | — | a plan retried N times must count once | counts are computed **only from the attempt whose result is a fresh commit**; `test_plan_stale_retry_counts_once` |
| host audit sink (receives the same fields dict) | — | sink exceptions swallowed (`__init__.py:109-113`, existing) | — | sink is host-chosen and user-scoped; it already receives every ingest count | no new mechanism needed — the sink sees the host's own data for its own user; named in §4 so the carrier is not silent |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | result |
|---|---|---|
| `apply_supersession` has exactly one caller | `grep -rn "apply_supersession(" src/veracium/ \| grep -v "def apply_supersession\|apply_supersession_plan"` | `ingest.py:204` only |
| the only ingest telemetry record site is `remember()` | `grep -rn 'record("ingest"' src/veracium/` | `__init__.py:162` only |
| `telemetry.py` is **not** a guarded file | `grep -c "telemetry" specs/check_spec_reference.py` | `0` |
| the MCP `remember` tool returns the ingest dict to the model caller **today** (the reach that makes I11 necessary — v2 strips the two keys there) | `grep -n "return mem.remember" src/veracium/mcp_server.py` | line 64 |
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

*v1 of this section answered "no new visibility" by asking who receives the
**dict** — the carrier — when the section's question is about **information**.
Research's internal review corrected the conclusion; the analysis below is the
v2 replacement, and its enforcement is I11.*

- **The per-write counts are a supersession oracle.** A non-zero
  `supersessions` on a single write tells the caller that the store held a
  conflicting active value for that (subject, relation) **before** the write;
  a non-zero `reinforcements` tells it a matching value already existed. That
  is **prior-state information**, not own-write information. For the
  **untrusted MCP model caller** under indirect injection this is exactly the
  paper-2 leak class: inject "bank = EvilBank", observe `supersessions: 1` in
  the tool result, learn that a bank fact existed in the user's memory —
  without any recall ever disclosing it.
- **Closure, at zero feature cost:** the MCP `remember` tool **omits both
  keys** from its tool result. The telemetry aggregate (weekly, per-install,
  class-blind) and the host-API return are unaffected — the feature exists
  for the aggregate, which the model never sees.
- **The kept MCP fields are supersession-invariant** (research verified this
  rather than leaving §9's completeness question open): the tool result's
  remaining count fields are `facts` and `quarantined`
  (`ingest.py:205-209`) — `facts` is the *extraction* count, incremented per
  non-quarantined edge **before** `apply_supersession` runs, so a fact that
  supersedes counts exactly like a fact that accumulates; `quarantined`
  reflects the incoming edge's own disclosure class, independent of any
  prior. Neither co-varies with the counters. I11's check asserts this
  co-invariance, not just key absence, so a future field addition re-asks
  the question mechanically.
- **Who may see the counts:** (1) the anonymous telemetry endpoint — only
  when opted in, an endpoint is configured, AND the consented version admits
  the fields (§4); (2) the host's audit sink — host-owned, user-scoped, and
  the host can already derive every count from its own store access; (3) the
  host-API caller — a trusted principal with full store access, for whom
  the counts reveal nothing it could not query (the CLI prints its fixed
  summary and does not surface them — R2-3/R3-3). **The MCP model caller
  is the one recipient that could NOT previously derive them, and it is the
  one that does not receive them.**
- **Scope change behaviour?** n/a — no sharing/revocation surface is
  touched.
- **Anything newly visible to a principal who couldn't see it before?**
  After I11: no. Without I11 the answer was yes — which is why I11 blocks.

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

**`mcp_server.py`** — the `remember` tool strips `"supersessions"` and
`"reinforcements"` from the dict before returning it to the model caller
(§3b: the per-write count is a supersession oracle; the model is the one
recipient that could not previously derive it). The host-API return keeps
both keys; the CLI consumes the dict but prints its fixed summary, unchanged
(R2-3/R3-3).

**`telemetry.py`** (not guarded) — `EVENT_FIELDS["ingest"]` re-adds the two
names; the explanatory comment block from `2767a35` is updated to record that
the spec landed rather than deleted. `SCHEMA_VERSION` becomes 2.
`TelemetryConfig.schema_version` is documented as **the version of the
consent text that was DISPLAYED and accepted** (research's Q2 ruling: the
consent version belongs to the display event, not the enable event). So:
**only the consent-display flow stamps it** — `prompt_consent()` and the CLI
enable path that prints `CONSENT_TEXT` stamp the current version;
**`set_enabled()` never stamps or bumps `schema_version`** — it toggles
`enabled` and leaves the recorded consent version exactly as it was, so a
programmatic re-enable by host code that displayed nothing keeps the install
at its previously-consented version. `load()` floors an absent/invalid value
to 1, and **`TelemetryConfig`'s dataclass default for `schema_version` is 1**
— the default is a stamping carrier (F2), and only an affirmative acceptance
may write the current version. **The gate binds at RECORD time (F1):** the
`Collector` holds the consented version it was constructed under, and
`record()` drops any field whose `FIELD_MIN_VERSION`
(`{("ingest","supersessions"): 2, ("ingest","reinforcements"): 2}`) exceeds
it — so a gated field NEVER ACCUMULATES under a consent that does not admit
it, and accepting v2 mid-process cannot retroactively expose pre-acceptance
values (the accumulated aggregate simply never contained them; post-
acceptance records, made after the process reloads its config into a
collector holding v2, include them). `preview()` applies the same strip as
defense-in-depth, but the record-time gate is the binding one: **a field is
sent only if it was recorded under a consent that admitted it.**

**The stamping transition table (F2) — TOTAL over the consent surface; only
the affirmative cell stamps the current version:**

| event | outcome | `enabled` | `schema_version` stamped | `consent_epoch` |
|---|---|---|---|---|
| fresh + interactive prompt | user answers yes | True | **current (2)** — the ONLY stamp-current cell besides CLI enable | **+1** (one bump: enable+stamp is ONE transition) |
| fresh + interactive prompt | user answers no | False | **1** — text was displayed, nothing was accepted | +1 (a fresh config is itself a persisted transition) |
| fresh + interactive prompt | EOF / interrupt | False | **1** | +1 |
| fresh + non-interactive | (no display) | False | **1** | +1 |
| CLI explicit enable (prints the text, affirmative) | accepted | True | **current (2)** | **+1** (one bump) |
| existing config + programmatic `set_enabled(True/False)` | — | toggled | **unchanged** (I12) | **+1 iff `enabled` actually changed; idempotent re-set bumps nothing** |
| no file + programmatic `set_enabled(True)` | (nothing displayed) | True | **1** — the fresh-programmatic cell F2 named; the floored default is what makes it safe | +1 |
| **existing config (any version) + `prompt_consent()`** | idempotent return — **no display, no prompt** | unchanged | **unchanged** — the reachable no-op row R3-4 named; an existing v1 install is NOT upgraded by a later prompt call (upgrade happens only through an explicit re-display flow) | **unchanged** (no transition, no bump) |

### The consent lifecycle — CONSOLIDATED (v10, PROCESS R3: past three rounds, rewrite)

*Rounds 3–7 each patched this construction and round 7 found two of the
patches contradicting each other (R7-1) — the exact failure R3 predicts.
This section replaces every prior lifecycle paragraph as ONE contract;
where older wording elsewhere disagrees, THIS section governs, and the
withdrawn-phrase registry guards the retired forms.*

**1. Persisted consent state.** `telemetry.json` carries `enabled`,
`schema_version` (the DISPLAYED-AND-ACCEPTED consent version; default 1),
and `consent_epoch` — **a positive `int` (`bool` excluded; zero is INVALID —
R7-4)** counting consent transitions. Absent/invalid `schema_version` reads
as 1. Absent/invalid `consent_epoch` is **normalized under the lock to a
fresh persisted positive epoch before any collector is constructed**; no
live collector ever holds an unnormalized or zero epoch. Deleting the file
is the consent-erasure mechanism and is never undone by telemetry code.

**2. The lock — ONE portable primitive (R7-3, decided HERE, not deferred).**
An **atomic lockfile**: `os.open(telemetry.json.lock, O_CREAT|O_EXCL)` —
atomic on POSIX and Windows alike, pure stdlib, one code path on every
platform (so the CI regime that runs IS the regime that ships; no
platform-conditional tests, and §10's former Q4 is CLOSED as decided).
Acquisition: nonblocking attempts every 50 ms up to a 2 s deadline. A crash
leaves the lockfile; a holder-crash is recovered by breaking locks older
than 10 s (mtime), the documented trade for portability (flock's
OS-auto-release is given up; telemetry tolerates the rare double-entry this
allows because every guarded write is a whole-file temp+rename). **Failure
splits by operation class:** `record()` and flush fail closed and SILENT —
telemetry never breaks the host; **explicit consent transitions
(`set_enabled`, `prompt_consent`, the CLI flows) RAISE `TelemetryLockError`
on deadline** — a user's consent choice must never silently fail to persist.

**3. Transitions.** Every consent transition is a locked read-modify-write:
acquire → reload → apply → **bump `consent_epoch` iff the persisted
(enabled, schema_version) pair actually changed** (idempotent calls bump
nothing; enable+stamp in the affirmative display flow is ONE transition) →
temp+rename → release. Racing transitions serialize and mint distinct
epochs.

**4. Collectors and adoption.** `load_collector_if_enabled()` constructs a
collector holding the (normalized) epoch of the config it read. At the
entry of `flush_if_due()` and `preview()`, `adopt_consent(config)` compares
epochs: **any difference — including the ABA disable→re-enable case —
DISCARDS pending aggregates before adopting** (an aggregate cannot prove
which increments predate a revocation; the blunt discard is the endorsed
fail-closed choice). Invalidity first seen at adoption normalizes under the
lock, then discards. `reset()` clears aggregates only and preserves the
adopted epoch. `record()` drops fields above the adopted consent version
(record-time gating — a field is sent only if recorded under a consent that
admitted it).

**5. The flush algorithm, start to finish.**
(a) not due / no endpoint / disabled → return False (nothing sent).
(b) acquire the lock; failure → return False (nothing sent).
(c) **under-lock read with STATUS (R7-2):** `_read_config_status()` returns
`(status ∈ {valid, absent, malformed}, config)` — the executable
construction the terminal matrix needs; `absent` and `malformed` are
distinguished from a valid default-valued file by the read, not inferred.
(d) absent/malformed/epoch-mismatch/disabled → discard-or-adopt per rule 4,
release, return False.
(e) valid + epoch match → the payload is AUTHORIZED; release the lock; POST.
(f) **post-POST, TOTAL (the terminal matrix):** reacquire the lock and
re-read with status; then —

| state after the POST | returns | collector | `last_sent` | file |
|---|---|---|---|---|
| valid, consent unchanged | True | reset | updated | untouched otherwise |
| valid, consent changed | True | reset | updated on the CURRENT file; consent preserved | untouched otherwise |
| absent (deleted during POST) | True | reset | not written | **NEVER recreated** |
| malformed | True | reset | not written | untouched (never rewritten) |
| lock or write failure | True | reset | not written — interval drift, never consent damage; the reset collector means an early re-send carries only new increments | untouched |

**`True` means a send happened; `False` means nothing was sent — the
pre-authorization and post-send failure classes never share an outcome
(R7-1).**

**6. The authorization claim (endorsed wording).** A POST is authorized by
its final locked recheck; an authorized POST may begin or complete after a
later revocation lands. Revocation is honored at every authorization
boundary, and no data recorded after a revocation is ever sent — not "no
packet ever crosses a revocation".


**The absent-collector state (R3-2): RESTART is the activation boundary.**
A process that started disabled has no collector (`load_collector_if_enabled
→ None`), and `flush_telemetry()`/`telemetry_preview()` return without
loading config when `self.telemetry is None` — a later acceptance therefore
takes effect at the next process start, never mid-process. Ruled and stated
(here, §5, §8, changelog) rather than patched: the alternative — a live
None→enabled transition — would need every `_record` site to re-check
config, and the fail-closed cost of the restart rule is under-collection
only. The disabled-start→affirmative-v2→record→flush regime asserts nothing
is collected or sent before restart (I8).

**`reset()` (R2-2):** clears aggregates only and PRESERVES the adopted
consent version — it must not re-run the constructor. The two-period rule:
record → flush (POST + reset) → record → flush sends the new fields in BOTH
periods exactly once each (I15).

**CLI output (R2-3):** UNCHANGED. `cli.py` prints its fixed summary and does
not gain the counters; the header waiver stands as written (host-API return
only). `CONSENT_TEXT` extends its enumeration ("…how often facts are
extracted, claims quarantined, values superseded or reinforced, and answers
abstained…").

**Interfaces:** the host-API `remember()` return dict gains the two int keys
— additive; **CLI output is UNCHANGED** (its fixed summary, R2-3) and **the
MCP `remember` tool result does NOT carry them** (§3b, I11). No export or
memory-store format change. **Migration:** none for the memory store;
`telemetry.json` gains `consent_epoch` (absent/invalid normalized under
lock to a fresh nonzero value at first load) and its
`schema_version` remains the persisted consent carrier (R2-5) — both survive
disable and are erased only by deleting the file. Nothing in the memory
store is unrecoverable or touched.

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
- **Consent regimes are a state MACHINE, not a list of states (F1's
  lesson):** the static cells (v1-consented stripped · v2-consented sent ·
  absent-version floored to 1 · fresh affirmative stamped 2 · programmatic
  enable on v1 stays v1) PLUS the transitions — **the same running collector
  across a v1→v2 acceptance** (pre-acceptance records must never surface,
  which record-time gating makes structural), and **every non-acceptance
  display outcome** (no / EOF / interrupt / non-interactive / fresh
  programmatic enable — each ends at version 1, per the §4 table). All are
  cheap unit fixtures.
- **Cold vs warm (R4-3): there IS a difference, and it is the restart
  rule** — a warm `Memory` that started disabled keeps `telemetry=None` for
  its lifetime; a restarted process constructs a collector under the new
  consent. Delayed activation is disclosed in §8.

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
| I8 — consent-version fail-closed **at RECORD time (F1)**, with the adoption lifecycle REAL (R2-1): `adopt_consent` is called at the named reload sites; the v1→v2 transition test runs **through a long-lived `Memory` carrier** (construct v1 → record → accept v2 via the display flow → the carrier's next flush adopts → record → flush sends only post-acceptance values); downgrade adoption discards gated aggregates; **the two R3 carrier regressions are NAMED on this surface (R4-3): `test_disabled_period_records_are_never_sent` (enabled→disabled→record→re-enabled→flush through a live `Memory`) and `test_disabled_start_activates_only_at_restart` (disabled-start→accept→record→flush sends nothing before restart)** | `test_v1_to_v2_transition_through_a_live_memory_carrier`, `test_disabled_period_records_are_never_sent`, `test_disabled_start_activates_only_at_restart`, `test_downgrade_adoption_discards_gated_fields`, `test_gated_fields_never_accumulate_pre_consent`, `test_v1_consent_strips_new_fields`, `test_preview_is_what_flush_posts` | CI |
| I9 — content-free: the ingest payload contains only int/float/bool values under every fixture | `test_counters_are_content_free` | CI |
| I10 — consent text and payload move together: `CONSENT_TEXT` mentions supersession/reinforcement iff the fields are whitelisted and populated | extend `test_telemetry_claims.py`'s existing text-pin | CI |
| I11 — **the oracle is closed**: the MCP `remember` tool result contains neither `"supersessions"` nor `"reinforcements"` under every outcome (fresh supersession, reinforcement, accumulation, replay); the kept fields (`facts`, `quarantined`) are **byte-identical across a superseding, reinforcing, and accumulating write of the same shape** (co-invariance, not just key absence); AND the permission side: the host-API `remember()` return contains both keys | `test_mcp_result_carries_no_supersession_oracle` (incl. the co-invariance assertion) + `test_host_api_return_carries_counts` | CI |
| I12 — `set_enabled` never stamps: toggling enabled (either direction, any number of times, with or without an endpoint change) leaves `schema_version` byte-identical; only the display flow stamps | `test_set_enabled_never_stamps_consent_version` | CI |
| I13 — **only AFFIRMATIVE consent stamps (F2)**: every non-acceptance path — answer no, EOF, interrupt, non-interactive, fresh programmatic `set_enabled(True)` — ends at `schema_version=1`; the dataclass default is 1; the §4 transition table is exercised cell by cell | `test_only_affirmative_consent_stamps_current` (parametrized over every non-acceptance path) + `test_config_default_schema_version_is_1` | CI |
| I14 — **both keys on EVERY successful terminal return of `ingest_event` (F3)**, including the unparseable early return, as int zeros; the host result, audit/telemetry recording, and the MCP strip all behave on that branch | `test_unparseable_return_carries_zero_counts` (asserts the host dict, the recorded event, and the MCP result on the parse-failure branch) | CI |
| I15 — **`reset()` preserves consent (R2-2)**: reset clears aggregates only; the two-period sequence (record → flush+reset → record → flush) carries the new fields in BOTH periods exactly once each, and reset after a defaulted or argument-bearing construction neither downgrades the version nor raises | `test_reset_preserves_adopted_consent_two_periods` | CI |
| I16 — **config validity is a closed predicate (R2-4 + R4-2 + R6-2)**: `schema_version` positive int (bool excluded) ≤ current else 1; **`consent_epoch` positive int (bool excluded); absent/invalid NORMALIZES UNDER LOCK to a fresh persisted nonzero epoch before any collector exists; adoption-time invalidity normalizes-then-discards; no live collector ever holds 0**; an unknown config KEY fails closed to whole-config disabled defaults | parametrized `test_invalid_schema_version_reads_as_v1` + `test_invalid_consent_epoch_normalizes_nonzero` + `test_adoption_time_invalid_epoch_normalizes_and_discards` + `test_unknown_config_key_fails_closed_whole_config` | CI |
| I17 — **the lifecycle's concurrency contract (consolidated §4)**: racing transitions mint DISTINCT epochs; a pre-authorization lock failure returns False with nothing sent; a POST-send lock/write failure returns True with `last_sent` unwritten (the two failure classes NEVER share an outcome — R7-1); a stalled POST resuming after a disable leaves the disable durable; a config deleted during POST is never recreated; a malformed config is never rewritten; `_read_config_status` distinguishes valid/absent/malformed (R7-2) | `test_racing_transitions_mint_distinct_epochs` + `test_preauth_lock_failure_returns_false_nothing_sent` + `test_postsend_lock_failure_returns_true_last_sent_unwritten` + `test_blocked_poster_disable_survives_post_resume` + `test_delete_during_post_never_recreates` + `test_malformed_config_never_rewritten` + `test_read_config_status_three_states` | CI |

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
- **Reversibility:** the memory store is untouched. **TWO values persist in
  `telemetry.json` (R2-5 + R4-2): `schema_version` and `consent_epoch`** —
  disabling stops all sending but erases neither; a host that wants the
  consent record gone deletes the config file. **Rollback to v1 code (probed, R4-2): the v1 loader hits `consent_epoch`
  as an unknown key and fails closed to whole-config disabled defaults** —
  telemetry silently OFF until re-consent under the old build;
  under-collection, never misreading.
- **Partial failure:** `_record` already swallows telemetry and audit-sink
  exceptions (`__init__.py:104-113`); an exception inside `apply_supersession`
  propagates exactly as today, with nothing recorded for the failed call —
  no retry-into-empty-success path exists.
- **New attack surface:** one was created by v1 of this spec and is closed
  in v2 — *stated rather than glossed, because v1's "none" was the internal
  review's returned finding.* The per-write counts are a supersession oracle
  over prior store state (§3b); had they reached the MCP tool result, an
  indirect-injection attacker could have used the model to read back "did my
  injected claim conflict with existing memory". Closure: the MCP result
  omits both keys (I11). What remains is two ints flowing to principals that
  can already derive them (the host-API caller) and a class-blind weekly
  aggregate — no non-user content can influence stored state, recall
  selection, or rendered context through any of it. **Timing boundary,
  stated so it is explicit rather than silent:** supersession does extra
  store work, so tool-call *latency* co-varies with the closed signal; the
  MCP result surfaces no timing to the model, so this is out of scope —
  unless a host independently exposes tool-call latency to its model, which
  is that host's boundary to defend, not this spec's.

---

## 8. Claims and limits

- **Changelog wording:** "Opt-in telemetry can now report how often values
  are superseded and reinforced — the counters the consent dialog's
  'aggregate counters' always intended. Installs that consented before this
  version keep sending exactly the old field set until telemetry is
  re-enabled against the updated consent text. A process that started with telemetry disabled begins collecting at its next process start after consent, not mid-run."

- **What this does NOT establish:** it does not measure supersession
  *correctness* (the 0003/0012/0014 suites do); it does not make telemetry
  users comparable (installs differ in workload); a zero does not mean the
  machinery is broken (most corpora legitimately never supersede); the
  counters say nothing about which trust classes were involved, by design
  (§3). The consent-version gate covers **veracium's own dialog**; where a
  host obtained end-user consent through its own UI, honouring the widened
  payload against that consent is the host's obligation, not discharged
  here. **And the scoping the oracle closure needs (two signals, one
  defect):** I11 closes the **new write-result oracle** — the direct,
  per-write, magnitude signal v1 would have introduced. It does not and
  cannot remove the **inherent** property that recall reflects
  post-supersession state (a model can always ingest, then recall, and
  observe its claim won or lost) — that signal predates this spec, is the
  memory working as designed, and is not closable without breaking recall.
  A review that finds the residual recall signal has found v0's designed
  behaviour, not an incomplete fix.
- **Delayed activation (R3-2/R4-3), disclosed:** a process that started
  with telemetry disabled does not begin collecting when consent is granted
  mid-run — activation happens at the next process start. The changelog
  carries this sentence.
- **Measurements:** none cited — no numbers appear in this spec.

---

## 9. Brief for the external reviewer

- ~~The error-surface question~~ — **CLOSED by external round 1**: the
  reviewer's enumeration found no additional prior-fact oracle in the present
  MCP error surface (author/date/extractor errors are request-dependent;
  refusal commits keep the same result shape; receipt-integrity errors need
  an op-id collision normal MCP writes cannot select; `PLAN_STALE` exhaustion
  exposes concurrency, not the prior value — and those paths predate this
  spec). Recorded here so round 2 does not re-litigate it.
- **Least sure of, one:** the **epoch discard rule's bluntness** — any
  consent transition discards ALL pending aggregates, including fields the
  old and new consent both admit. That is deliberately fail-closed (an
  aggregate cannot be split by when its increments happened), but it
  under-reports around every consent change; if you see a sound way to keep
  provably-always-admitted fields, we would take it — and if not, say the
  bluntness is right.
- **Least sure of, two:** the claim that a **committed reinforcement plan is
  structurally indistinguishable from accumulation** rests on today's plan
  shape (§2c-ii last row). If a future spec adds a distinguishing persisted
  fact, the planner-branch return becomes redundant but not wrong — is the
  redundancy a defect or a margin?
- **Where we may have overstated:** the **display-event consent rule** (Q2
  ruling) assumes the CLI enable path is the only programmatic surface that
  *shows* the text; if a host embeds `CONSENT_TEXT` in its own UI and then
  calls `set_enabled(True)`, that end user genuinely consented to v2 and we
  still strip the fields — fail-closed, but strictly under-collecting
  relative to real consent. We accept that; say so if you think the
  asymmetry hides a defect.
- **What would change our minds:** if the reviewer finds any path where the
  counts differ from the committed store facts (an I4 violation we didn't
  enumerate), the counting moves from the planner into the store layer and
  this spec gets a successor version with a different §1 trade-off.
- **Reviewer-safe copy:** not needed — no competitive-audit detail or
  unpublished findings appear here.

---

## 10. Open questions

1. ~~Class-consistency consent reading~~ — **RESOLVED 2026-08-11 (research,
   `proposals/0015-internal-review.md`): the gate stays.** Consent is to what
   was **displayed**, not to an abstract category (`2767a35` is directly on
   point); "aggregate counters" is an open-ended grant with no natural
   boundary; and the downside is asymmetric (small recoverable friction vs a
   falsified public consent claim). The `FIELD_MIN_VERSION` gate is
   load-bearing, not provisional.
2. ~~`set_enabled(True)` stamping~~ — **RESOLVED 2026-08-11 (research): both
   v1 options were wrong the same way — they tied the consent version to the
   ENABLE event when it belongs to the DISPLAY event.** `set_enabled` never
   stamps or bumps `schema_version`; only the consent-display flow
   (`prompt_consent()` / the CLI path that prints the text) stamps. One
   behaviour, no API split, nothing stamps v2 unless v2 was shown. §4
   carries the mechanism; I12 enforces it.
3. ~~Platform scope of the lock~~ — **CLOSED in v10 (R7-3): the O_CREAT|O_EXCL
   atomic lockfile is one code path on every platform, so no platform regime
   split exists and nothing was deferred to implementation.**
4. **Absorption/refusal counters** — worth a future spec once these two
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
