# Feature spec: maintenance never raises confidence — the decay bounds (0002's N4, carried)

Spec-Status: accepted

*<!-- canonical machine-readable state; the header table below carries the narrative. Only `accepted` authorises implementation. -->*

| | |
|---|---|
| **Author / session** | research (veracium-research-d5), the candidate's author → dev, adopted at rest and re-read from the file: v2 2026-10-10 from `0048-decay-never-raises-confidence-CANDIDATE.md` (sha16 f7336e49d33d1494); v3 2026-10-11 from `0048-decay-never-raises-confidence-CANDIDATE.md` (sha16 e3053ec1828ec62f) |
| **Version** | **v4.2 — 2026-11-03: round 3 returned the IMPLEMENTATION for amendment (R3-01, R3-02 medium; R3-03 low); the round-2 design acceptance stands. This version changes only the text that describes the mechanism, so it matches the round-4 implementation: §4A, an integer is compared exactly before any float conversion (R3-03); §4C, the helper validates and returns ONE captured serialisation (R3-01), and one write method, guarded by a closed grammar, makes every edges json write (R3-02); §4D's writes go through that method; the cost line names the body it measured; N4b, N4f and the §6 mutant rows carry the reviewer's forms; a round-3 closure table. No change to the accepted design surface.** **Prior: v4.1 — 2026-11-02: N4i's retiring case keeps the wiki (the shipped meaning), and §2c-ii's rows are history once §4 lands.** Dev, implementing §4, found N4i's last sentence ("its journal row and the wiki drop") contradicting accepted 0004 W3: `decayed` is a wiki-RETAINING reason (`schema.WIKI_RETAINING_REASONS`; `DISPOSITIONED_REASONS["decayed"] == "retain"`), and R2-02's rule is the shipped meaning. The contract harness models no wiki, so only the text changes. No design change. **Prior: v4 — 2026-10-12: ACCEPTED (design), external round 2, with the verdict's two obligations folded.** The verdict accepted v3.3 on the frozen surface N4 (confidence half), N4b, N4b′, N4b-assign, N4c within its scope, N4d, N4d-prefix, N4e, N4f, N4g and N4h, under §4 A–D and §7–§8. **R2-01** (medium): the contract harness's writer gate passed `executemany` and an alias of `execute` while storing confidence 1.8; research found two more forms (`getattr`, a cursor). N4f's gate now fails closed by the connection's receiver, and nine forms are mutants of one §6 row. **R2-02** (medium): the model counted every decay and stored the decayed value below the floor, where the shipped `expire()` does neither; diffed over thirteen branches, seven differed, all from those two mechanisms. §2 and §4D now state the shipped meaning (the accepted "no meaning changes" contract; adopting the model's would be the owner's explicit behaviour change), and **N4i** holds it with a fixed table and three mutants. Editorial: §9's R1-02 row counts four D mutants; §5's fixed point is at the floor. No design change. Prior: **v3.3 — 2026-10-12: §4D's "equivalent form" removed (H-01, found by round 2's contract harness).** v3.2 permitted a write conditional on the whole row as read, where zero rows meant no write, not counted. When that write loses a race, a transition still due on the committed row is dropped, which matches no serial order of the overlapping operations, contrary to §4D's own statement and to N4h's serial control. Modelled, N4h's `decay` case leaves B's 0.225 where the serial control gives 0.1125 (`specs/evidence/0048/contract_harness_0048.py`). The in-transaction read is now the only form. One §6 mutant row is added, and the round-1 closure's archive row names the harness. No other change. Prior: **v3.2 — 2026-10-11: §6 N4c narrowed to what its instruments catch.** v3.1's (iii) said "A new writer without an entry fails the test" of an AST census that, planted with unvalidated-write forms it was not written for, missed every one (research's round-2 stage 2, `S2-01`; dev's campaign found more against the widened census). (iii) is now two instruments that do not share a scope, the census and a token tripwire compared with a hand-classified snapshot, and the residual both miss is named. One §6 mutant row added. No other change. Prior: **v3.1 — 2026-10-11: Q6 resolved, "Q6 - edges only"** (the owner, 2026-10-11T20:04:32Z, first-hand in the dev session, relayed by dev; coordination ledger `9cdd856`), on research's and dev's joint recommendation. C stays edge-only; storage bounds for every other `Provenance` carrier, starting with the episode path, are a named follow-up (§8, §10). No other change. Prior: **v3 — 2026-10-11: round 1 returned v2 for amendment (R1-01..R1-04 and the finite-decay note; R1-05 was a baseline fixture, fixed in the tree at `6c0eab6`).** Each finding was reproduced against the shipped code at `4ea1ce5` by dev before this fold, with honest controls. **(R1-01)** one shared validator for BOTH numeric fields, run at `expire()`'s ENTRY on every config, independent of any edge's confidence, its result captured once (§4A–B). **(R1-02)** the expiry transition is decided from the CURRENT row inside one write transaction (new §4D). Research found the class wider than the verdict's decay case: the same stale read-decide-write reverts a user's `confirm()` and lapses a fact just confirmed, through the CONFIRM and LAPSE behaviours of the **shipped** expiry table (§2c-ii row 11). 🔴 **Scope: §4D covers all three behaviours, on the owner's ruling "All 3" (2026-10-11T19:10:51Z, first-hand in the dev session, relayed by dev; coordination ledger `2b930e2`; §10 Q5).** **(R1-03)** one unit of refusal: configuration refusal at entry, before any edge; later ordinary failures keep the stated per-edge prefix behaviour (§4B, §7, N4d). **(R1-04)** the persistence guarantee is scoped to EDGES; §2c-ii row 8 is a generated AST census (five confidence writers, not four); consolidation's confidence is in range by its inputs, stated as a dependency (§4C). **(The finite-decay note.)** §5 promises non-increase only; finite-time invalidation is real-arithmetic intuition, not a runtime guarantee. **Q4 resolved** as the reviewer answered, with dev's co-decision (§10). §2c-ii's prose rows are now scripts (`specs/evidence/0048/`, landing with this version). Prior: **v2 — 2026-10-10.** v2 folded the owner's answer to Q1, "Yes, guard the store" (2026-10-10, first-hand in the dev session, relayed by dev): part C and N4f are IN, unconditional. v1: research 2c134739, never adopted. A standalone carrier for one invariant of `specs/0002-maintenance-provenance-invariant.md` (Spec-Status `deferred`), on the owner's decision of 2026-10-10 (relayed by dev, given first-hand in the dev session): **"B"**, a small standalone spec, so the fix reaches `lifecycle.py` (guarded) through review rather than through an exception. No Spec-Exception fits: the hostile value is the host's own configuration, not an attacker's, so `security-hotfix` does not apply. |
| **Status** | *see `Spec-Status:` at the top — canonical.* |
| **Internal reviewers** | research (author) · dev |
| **External review** | required: the change touches two guarded files, `src/veracium/lifecycle.py` and `src/veracium/store/sqlite.py`. **Round 1** (package `f147f044…` @ `4ea1ce5`, v2): RETURNED for amendment, 2026-10-10 (R1-01..R1-04; R1-05 a baseline fixture), folded at v3. **Round 2** (package `c8ca80f4…` @ `c1c9ecf`, v3.3): DESIGN ACCEPTED, 2026-10-12, with two implementation and evidence obligations (R2-01, R2-02), folded at v4 |
| **Decision + date** | **ACCEPTED — DESIGN 2026-10-12** (external round 2, pin `c1c9ecf`; Spec-Status flipped by dev, the acceptor, at the v4 fold; the verdict banked as `0048-round2-verdict-verbatim.md`). Implementation follows; its review is the next round |
| **Path** | full |

---

## 1. Problem and motivation

`specs/0002` states, as N4, that **no maintenance operation raises `confidence`**, and lists five tests that would
enforce it (N4b, N4b′, N4c, N4d, and the N4 property test). **None of the five exists** (§2c-ii, row 6). 0002 is
deferred, so the invariant has been a sentence for ten weeks. It is false today in two ways.

**First, the decay factor is unchecked.**

- `MemoryConfig` (`src/veracium/config.py`) is a plain `@dataclass`. `decay_factor` and `confidence_floor` are
  unvalidated: `2.0`, `-1.0`, `nan` and `inf` are each accepted at construction, and assignment after construction is
  accepted too (§2c-ii, rows 1–2).
- `expire()` (`src/veracium/lifecycle.py:72–73`) writes the decayed confidence with
  `e.provenance.model_copy(update={"confidence": e.provenance.confidence * config.decay_factor})`. pydantic's
  `model_copy(update=…)` **skips validation**, so `Provenance.confidence`'s declared bound (`Field(ge=0.0, le=1.0)`,
  `src/veracium/schema.py`) does not hold on this path. `expire()` takes `config` duck-typed: any object with the
  attributes it reads is accepted.
- **Range validation of the result is not enough (round 1, R1-01).** A result in [0, 1] does not show `f ≤ 1` or
  `result ≤ c`: confidence 0.3 under factor 2.0 is a valid 0.6. The factor itself must be validated.

**Second, `expire()` decides on a read taken outside its write (round 1, R1-02, and its class).** `expire()` lists the
user's edges, decides each edge's behaviour from that listing, and writes the copy it read back with `add_edge`. Any
write committed to the same edge in between is overwritten or ignored. Measured with two real connections
(§2c-ii row 11):

- **DECAY** (mapped by a host): the reviewer's schedule. Two runs commit 0.45 then 0.225; a third, which read 0.9
  before them, commits its stale 0.45. Maintenance raised the committed confidence.
- **CONFIRM** (the **shipped** table: SLOW, DURABLE): a user's `confirm()` commits `needs_confirmation = False`,
  confidence 0.9 and today's `observed_at`; the overlapping maintenance run writes back the pre-confirmation copy. The
  confirmation's audit row survives; the edge says it was never confirmed.
- **LAPSE** (the **shipped** table: TRANSIENT, EPHEMERAL): the overlapping run invalidates a fact the user confirmed
  a moment earlier, deciding from its stale `observed_at`.

The race needs a host that runs `maintain()` while another operation writes the same user's edge. `maintain()` is
public API ("call on a schedule") and an MCP tool; no shipped code schedules it, and how often hosts overlap it with
user operations is not measured. The store's lock is per instance and held per statement group, so it does not span
the read and the write either.

**What happens if we do nothing about the factor.** Two facts decide the severity, and both were measured
(§2c-ii, rows 3–5):

1. **With the shipped expiry table the decay branch is unreachable.** No `Volatility` maps to `ExpiryBehavior.DECAY`
   in `schema.DEFAULT_EXPIRY` (0 of 5), and no file in `src/`, `tests/`, `examples/`, `docs/`, `README.md` or
   `CHANGELOG.md` maps one. The branch runs only for a host that edits that exported, mutable module dict.
2. **When a host does reach it, the result is worse than a raised number.** With `DEFAULT_EXPIRY[SLOW] = DECAY` and
   `decay_factor=2.0`, `expire()` writes confidence `1.8` (0.9 × 2.0). The store accepts the write, but every later
   read of that user's edges raises `ValidationError`. With `decay_factor=nan` the value is stored as `NULL` and the
   reads raise the same way. **One maintenance run poisons the user's whole edge listing.**

So **a default store never reaches the decay branch**, but it does reach the stale write through CONFIRM and LAPSE.
The cost of the fix is small, and it turns a recurring invariant ("configuration may narrow, never widen", 0001; 0002
L727–731) into an enforced one on the two numeric knobs that can widen it.

**Alternatives rejected.**
- **Remove `ExpiryBehavior.DECAY`.** It is unreachable by default, but `ExpiryBehavior` and `DEFAULT_EXPIRY` are
  exported (`schema.__all__`), so a host that maps DECAY today would break. Rejected for this spec; kept as §10 Q3.
- **Clamp instead of refuse** (`min(1.0, c·f)`). A clamp turns a host's misconfiguration into a silent behaviour
  (factor 2.0 would mean "never decays"), and NaN has no clamp. Refusal is visible at host startup.
- **Validate the config only.** Leaves the duck-typed `config` path and the unvalidated copy (above).
- **Make `MemoryConfig` frozen.** Fixes assignment, but changes a public dataclass's API for every field; hosts may
  legitimately mutate other fields. Rejected in favour of validating the two fields on assignment (§10 Q4, resolved).
- **A monotonic guard in `add_edge`** (refuse any write that raises confidence). Rejected, as round 1 advised: other
  operations raise confidence legitimately (`confirm()`), so the guard would be wrong for them, and it would not catch
  the CONFIRM and LAPSE cases at all.
- **A write conditional on the fields the transition reads** (confidence and activity as read). Rejected by
  measurement: a `confirm()` on an edge already at 0.95 changes neither, and the stale write still reverts its
  `observed_at` and `needs_confirmation` (§2c-ii row 11, case `confirm95`).

---

## 2. Field contracts touched

| field | read / written | its documented contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `MemoryConfig.decay_factor` | read by `expire()` | "confidence multiplier when a DECAY fact expires" (`config.py`) | `lifecycle.py` only | yes: it narrows the accepted values to the ones the comment already implies (a multiplier that decays) |
| `MemoryConfig.confidence_floor` | read by `expire()` | "below this, a decayed fact is invalidated" (`config.py`) | `lifecycle.py` only | yes: values outside [0, 1] could never be a floor of a value in [0, 1] |
| `Provenance.confidence` | written by `expire()`'s decay | `Field(default=0.9, ge=0.0, le=1.0)` (`schema.py`) | 8 files in `src/` (`why`, `lifecycle`, `dryrun`, `store/revocation`, `store/revocation_sweep`, `store/sqlite`, `contribution`, `graph`) | yes: the change makes the declared bound hold on a path where it did not |
| `Edge.needs_confirmation`, `Provenance.observed_at`, the edge's activity | written by `expire()` (CONFIRM sets the flag; LAPSE and the floor invalidate); written by `confirm()` and others | 0008 (`confirm()` is the only path that clears the flag); 0012 (each edge ages against its own `observed_at`) | `confirm_edge`, recall, `doctor`, the wiki | yes, and newly: an expiry write can no longer restore a value another operation replaced (§4D) |
| `expire()`'s return (`lapsed`, `decayed`, `flagged_for_confirmation`) | read by `maintain()` and its audit event | the shipped meaning (R2-02): `lapsed` counts LAPSE invalidations; `decayed` counts **decay-triggered invalidations only**, an edge whose decayed confidence falls strictly below the floor, **not** a retained decay; `flagged_for_confirmation` counts flags newly set | 0021's `maintain` event mapping | yes: no key is added or removed, and no count changes meaning (N4i). An edge that is no longer due when its transition runs is not counted, which is what a serial run after the other operation reports |

Consumers enumerated by `grep -rcE '\.confidence\b|"confidence"' src/veracium --include=*.py | grep -v ':0$'` and
`grep -rn 'decay_factor\|confidence_floor' src/veracium`. **No meaning changes**, so no documentation states an old
meaning; the CHANGELOG gains a "who should take this" note (§8).

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| host configuration: `MemoryConfig(decay_factor=…, confidence_floor=…)` | n/a (defaults apply) | non-number, `bool`, `nan`, `±inf`: **refused** at construction | — | `> 1` or `< 0`: **refused** at construction; boundaries `0.0` and `1.0` **accepted** | **N4b**, **N4b′** |
| host configuration: assignment after construction (`c.decay_factor = 2.0`) | — | as above: **refused**, and the field keeps its old value | — | as above: **refused**, old value kept | **N4b-assign** |
| host configuration: any `config` passed to `expire()`, a `MemoryConfig` or a duck-typed object | — | either numeric field a non-number, `bool` or non-finite: **refused at `expire()`'s entry**, before any edge is read; nothing is stored, even when no edge is eligible | — | either field outside [0, 1]: **refused at entry**, whatever any edge's confidence is | **N4d**, **N4g** |
| host configuration: `schema.DEFAULT_EXPIRY` edited to map a class to DECAY | — | — | a non-`ExpiryBehavior` value: out of scope (unchanged behaviour, §8) | DECAY mapped: the decay path runs, under N4b–N4h | **N4**, **N4d** |
| the schedule: another operation commits to the same edge between `expire()`'s listing and its write (`confirm()`, a redaction, another `expire()`, ingest) | — | — | — | any interleaving: the transition decides from the row as committed when it runs (§4D) | **N4h** |
| data written by an older version: an edge whose stored confidence is `> 1` or `NULL` (only possible for a host that mapped DECAY with a factor `> 1` or `nan` before this fix) | — | the read path already **refuses** (`ValidationError`); unchanged by this spec | — | — | **none in this spec: §10 Q2 (repair)** — named, not hidden |

The last row has no invariant **in this spec**, and that is stated rather than filled: repairing rows already
written is a separate decision (§10 Q2). This spec prevents new ones.

### 2c-ii. Assertions about reach — REQUIRED

**(v4.1) Rows 5, 11 and 12 record the code at this pin, as history.** With §4 implemented their scripts print the fixed behaviour (each script's docstring states both outputs), and `tests/test_0048_evidence.py` asserts the fixed form case by case; row 8's census is held live by N4c. All commands run at veracium `6c0eab6` (its `src/` equals round 1's `4ea1ce5` except `asof/resolve.py`) on CPython
3.14.7 / SQLite 3.45.1, from a git-archive copy (`PYTHONPATH=src`). Rows 1–4, 6, 9 and 10 were first run at `0f93840`
and re-run at `6c0eab6` with the same results. The scripts are in `specs/evidence/0048/`; each records its output
beside it.

| # | assertion | command that establishes it | result |
|---|---|---|---|
| 1 | `MemoryConfig` accepts out-of-range and non-finite bounds at construction | `python -c "from veracium.config import MemoryConfig as M; [M(decay_factor=v) for v in (2.0, float('nan'), -1.0, float('inf'))]; [M(confidence_floor=v) for v in (2.0, -0.5, float('nan'))]"` | no exception (all 7 accepted) |
| 2 | assignment after construction is accepted | `python -c "from veracium.config import MemoryConfig as M; c=M(); c.decay_factor=2.0; print(c.decay_factor)"` | `2.0` |
| 3 | the shipped expiry table maps no class to DECAY | `python -c "from veracium.schema import DEFAULT_EXPIRY as D, ExpiryBehavior as B; print(sum(v==B.DECAY for v in D.values()), len(D))"` | `0 5` |
| 4 | nothing shipped maps DECAY or edits the table | `git grep -nE 'DEFAULT_EXPIRY\|ExpiryBehavior\.DECAY' -- src tests examples docs README.md CHANGELOG.md` | only the definition, `schema.__all__`, and `lifecycle.py:31,65,68` (the import and the two branch reads) |
| 5 | with DECAY mapped, factor `2.0` and `nan` are written and the user's reads then fail; `0.5` reads back | `python specs/evidence/0048/reach_rows.py . 5` | factor 2.0: `expire` returns normally, the read raises `provenance.confidence: Input should be less than or equal to 1`; nan: `… Input should be a valid number`; 0.5: read ok, confidence 0.45 |
| 6 | none of 0002's five named N4 tests exists | `for t in test_no_maintenance_op_raises_confidence test_config_bounds_are_validated test_boundary_configs_are_still_valid test_declared_bounds_hold_under_in_place_mutation test_decay_through_expire_cannot_exceed_the_bound; do git grep -c "def $t" -- tests; done` | 0 hits for each (the sixth, `test_no_maintenance_op_widens_disclosure`, exists) |
| 7 | the only bounded field in `schema.py`'s pydantic models is `Provenance.confidence`; `Provenance` is frozen; `validate_assignment` is off | `python specs/evidence/0048/reach_rows.py . 7` | `Provenance.confidence ['Ge(ge=0.0)', 'Le(le=1.0)'] frozen=True validate_assignment=False`; `1 bounded field(s)` |
| 8 | **five** `model_copy(update=…)` sites in `src/` write `confidence`, and only the decay site multiplies by a host value; seven SQL statements write the edges table's `json` | `python specs/evidence/0048/census_0048.py .` (an AST walk: the key may sit on any line of the call) | `lifecycle.py:72` (× `decay_factor`); `store/sqlite.py:704` (confirm: `max(c, 0.9)`); `graph.py:514` (`max(incoming, prior)`); `store/sqlite.py:894` (0022's recompute: a stored value); **`store/sqlite.py:2454`** (consolidation output: the minimum of its inputs, key at L2472). One site replaces the whole `provenance` (`scope_read.py:406`), with keys `disclosure` and `derived_from` only. Edge `json` writers at L640, 722, 794, 850, 898, 2089, 2884. `UNRESOLVED: 0`. *v2's row said four: it used a line grep, and the consolidation site's key is 18 lines below its call (R1-04).* |
| 9 | no call site in `src/`, `tests/` or `examples/` sets either bound | `git grep -nE 'decay_factor\s*=\|confidence_floor\s*=' -- src tests examples` | no hits (the declarations in `config.py` read `decay_factor: float = 0.5`, which the pattern does not match; any keyword use `decay_factor=…` would) |
| 10 | the spec 0002 text reviewed at its seventh external review already carried N4's confidence clause and N4b–N4d | `git log --before=2026-08-02T12:53:00Z -1 -- specs/0002-maintenance-provenance-invariant.md` → `36374ae`; `git show 36374ae:specs/0002-… \| grep -cE '^\| \*\*N4[bcd]'` | `36374ae`; N4 row with "or raises `confidence`"; 4 rows. *Scope of this claim: the v7 verdict says "Invariant approved a seventh time", about 0002's headline invariant ("may never widen [trust]"); that the reviewer approved each N4 row is not claimed.* |
| 11 | `expire()` decides on a read outside its write, in all three behaviours; with two real connections, an overlapping operation's committed state is lost | `python specs/evidence/0048/probe_expire_lost_update.py <scratch-dir>` (A pauses deterministically after its read; B commits; A resumes) | `LOST-UPDATE` in all four cases: `confirm` (B's 0.9 / today / unflagged reverted to 0.6 / 2024 / flagged), `confirm95` (confidence and activity unchanged by B, still reverted), `lapse` (a just-confirmed fact invalidated), `decay` (0.225 → stale 0.45). Serial control in the same script (B, then A, no overlap): B's state kept, A applies nothing |
| 12 | the round-1 reproductions hold against the shipped code: factor 2.0 at confidence 0.3 persists 0.6; floor 2.0 invalidates a valid decay; a NaN floor and a Boolean factor complete; a non-number factor raises after an earlier edge in the loop was durably lapsed; `5e-324 × 0.9 == 5e-324` | `python specs/evidence/0048/pin_repro.py .` (dev's, with honest controls) | each case as stated, at `4ea1ce5` and `6c0eab6` |

Row 8's four non-decay `confidence` writers stay in range **because their inputs do**: each takes a maximum or a
minimum of validated values, or a stored value. That is a dependency, not a guarantee. For **edges**, part C (§4)
closes it at the store's write boundary. For the consolidation output, which is an **episode**, it stays a stated
dependency (§4C, §8, §10 Q6).

---

## 3. Trust-class matrix — REQUIRED, blocking

`expire()`'s decay is **unary** (one edge at a time) and **maintain-time**, so this is a state-transition table.
Classes enumerated from the enums at `6c0eab6`: `EvidenceAuthor` = user, third_party, system, assistant;
`Disclosure` = mentionable, use_only, quarantined.

| edge's `author_of_evidence` | mentionable | use_only | quarantined |
|---|---|---|---|
| user | c → c·f, f ∈ [0, 1]; disclosure, author unchanged | same | same |
| third_party | same | same | same |
| system | same | same | same |
| assistant | same | same | same |

Every cell is the same rule, because decay does not read the class: **confidence can only fall or stay
(f = 1.0)**, and below `confidence_floor` the edge is invalidated (narrowing). After this change no cell can raise
confidence or write one outside [0, 1], **and c is the confidence committed when the transition runs, not the one
listed earlier**.

§4D changes **when** each behaviour decides, not **what** it does: LAPSE still invalidates, CONFIRM still sets the
flag, and DECAY keeps the shipped result, its count and its below-floor stored state included (R2-02, N4i).
None of them reads the class.

- Can it make a **user-asserted fact non-assertable**? Yes, by design: a DECAY fact below the floor is invalidated
  ("decayed"), and a LAPSE fact is invalidated. **After §4D, never on the strength of a state another operation has
  already replaced** (today: the LAPSE case of §2c-ii row 11).
- Can **non-user content gain user-grade authority, confidence or currency**? Today, yes: confidence above 1.0 for any
  class. **After: no.** That is the change.
- Can it **clear `needs_confirmation`**? No. **Can it re-set a flag a user's `confirm()` just cleared?** Today, yes
  (§2c-ii row 11). After §4D: only if the edge is due again by its current `observed_at`.
- Does it **merge, drop or overwrite provenance**? A retained decay replaces the stamp with a copy differing only in
  `confidence`, built from the current row; every other field is the current row's. Below the floor no new stamp
  is written: the current row is retired with its stored confidence unchanged (R2-02).

**Write-time or maintain-time?** Maintain-time: no new evidence arrives, so the only permitted direction is down.

## 3b. Authorization and scope — *full specs only*

n/a — `expire(store, user_id, …)` reads and writes one user's edges; nothing crosses a user, tenant or scope boundary,
and no principal sees anything new. The one cross-cutting effect today (a poisoned row makes **that user's** reads
raise) is removed by the change.

---

## 4. Behaviour

**A. One validator for the two decay bounds** (`src/veracium/config.py`, not guarded). A single function validates a
`(decay_factor, confidence_floor)` pair: each must be a real number (`int` or `float`, **not** `bool`, refused
explicitly), finite, with `0.0 ≤ x ≤ 1.0`; integers and both inclusive endpoints are accepted. **An integer is compared
exactly, before any conversion to float** (v4.2, R3-03), so `10**400` is outside the interval and raises the same
`ValueError`, never an `OverflowError` from a finiteness check. A violation raises
`ValueError` naming the field and the value. **The same function** serves `MemoryConfig` construction, assignment
(a `__setattr__` check on these two fields only, which validates **before** setting, so a refusal keeps the old
value; §10 Q4) and `expire()`'s entry (B). Defaults (0.5, 0.3) are unchanged.

**B. `expire()` validates its policy once, at entry** (`src/veracium/lifecycle.py`, guarded). Before reading any edge,
`expire()` reads `decay_factor`, `confidence_floor` and `volatility_lifetime_days` from `config` **once**, validates the
pair with A's function, and uses those captured values for the whole run. This holds for every `config` object,
`MemoryConfig` or duck-typed, and **does not depend on any edge's confidence or on whether any edge is eligible**: a
malformed configuration refuses on an empty store. Configuration refusal therefore happens before anything is written
(R1-03's unit). The decayed stamp is still built so that pydantic validates it (`Provenance.model_validate`, not
`model_copy(update=…)`), as defence in depth; with a validated policy it never fires.

**C. The store refuses to persist an EDGE that violates a declared bound** (the owner's answer to Q1). One helper
serialises an edge for storage **from one observation** (v4.2, R3-01): it serialises the edge once, re-validates
**those captured bytes** (`Edge.model_validate_json(captured)`; accepting an existing instance is not revalidation,
since a nested model can be built unvalidated), and returns exactly the bytes it validated. Validating one observation
of a mutable edge and storing another was the defect: a provenance replaced between the two was committed unvalidated.
**One write method** (v4.2, R3-02) makes every SQL write of the edges table's `json` column in
`src/veracium/store/sqlite.py` (the seven of §2c-ii row 8, and §4D's). It calls the helper once, binds the captured bytes
at the `json` position, and journals the same bytes, at once or, for the redaction, through a single-use deferred
journal that must be emitted before its scope closes, inside the write transaction. No writer holds the json string,
so no binding of it can be changed. A gate refuses every edges write that does not go through that method, by a
**closed grammar, refusal over inventory**:
- the write method and its deferred journal are frozen by digest, and only the write method calls the journal writer;
- the helper's and the method's names are bound once and never shadowed, by any binding form, attribute assignment,
  subclass or dynamic rebinding;
- the json-writing SQL is a closed set of literals used only by the write method, each classified by SQLite's own
  authorizer, so `WITH … UPDATE edges` and `UPDATE main.edges` are edges writes;
- every non-literal SQL site is on a closed allow-list, with any dynamic table's domain frozen;
- a test-time authorizer refuses an edges insert, or an edges `json` update, prepared outside the write method.

The gate still **fails closed by the connection's receiver**
(R2-01): every reference to the store's connection is a form it resolves, a direct call whose SQL and bound values
it reads, or one the binding inventory lists as a non-write with its reason; any other reference fails, whatever
the method is called. **A refusal raises before the SQL statement runs**, so
nothing is written; inside a transaction the existing rollback applies. With A and B in place, C never fires on a
valid configuration; it is the defence for every path that computes a bounded value for an edge, present or future.

**C's scope is edges.** The consolidation output (`store/sqlite.py:2454`, an **episode**'s provenance) takes the
minimum confidence of its inputs. Its inputs are episodes read through `Episode` validation, so the minimum is in
[0, 1] **because its inputs are**: a stated input dependency, bound by
`tests/test_lifecycle.py::test_consolidation_output_is_no_stronger_than_its_weakest_input`. An episode written by
another path with an out-of-range confidence is accepted by `add_episode` today and fails at its next listing
(round 1 observed it); that adjacent path is outside this spec on the owner's ruling, and is the named follow-up
(§8, §10 Q6).

**D. The expiry transition is decided from the current row, inside one write transaction** (`store/sqlite.py`,
guarded; R1-02). `expire()` lists the user's due candidates as today, then applies each through **one store
transition per edge**, which inside `_write_txn` (`BEGIN IMMEDIATE`):

1. reads the edge's row by `(id, user_id)`; **absent, inactive or attested-redacted → no write, not counted** (the
   0041 skip moves inside the transaction, so a redaction committed after the listing is seen);
2. decides from **that** row: due-ness from its current `volatility` and `observed_at` against the captured
   lifetimes and `now`; the behaviour from `DEFAULT_EXPIRY` for its current volatility; **not due → no write, not
   counted**;
3. applies the behaviour to that row: **LAPSE** invalidates it; **CONFIRM** sets `needs_confirmation` if it is not
   already set; **DECAY** computes `c·f` from the row's **current** confidence; **strictly below** the captured floor
   it invalidates that row **with its stored confidence unchanged** and counts it in `decayed`; otherwise it writes
   the decayed edge, which is **not** counted. That is the shipped meaning (R2-02, N4i); a decay exactly at the
   floor is retained;
4. writes through C's write method and the same in-transaction bodies the existing writes use, so 0029's journal, 0041's
   attestation refusal and the wiki invalidation apply unchanged.

The result equals the result of some serial order of the overlapping operations: an operation that committed first
is seen; one that commits later sees the transition's result. Nothing is retried. **The in-transaction read is the
only form. Not permitted:**
- a write conditional on the row as read, in place of that read (`… WHERE id=? AND user_id=? AND json=?`, zero
  rows → no write). When it loses a race, a transition still due on the committed row is dropped and not counted,
  which matches no serial order (H-01: on N4h's `decay` case B commits 0.225 and the dropped transition leaves it,
  where the serial control gives 0.1125);
- a write conditional on the fields the decision reads (§1, rejected by `confirm95`);
- a predicate binding the read model re-serialised: rows written by earlier releases need not match today's
  serialiser, and every one of them would be skipped;
- any whole-row write-back of a copy read outside the transaction.

**Scope (the owner's ruling, §10 Q5):** D covers all three behaviours, CONFIRM, LAPSE and DECAY.

**Interfaces:** `MemoryConfig` construction and assignment can now raise `ValueError` for the two fields; `expire()`
and `maintain()` can raise it at entry for a duck-typed config. No CLI, MCP or export-format change; `expire()`'s
return keys and their meaning are unchanged (§2, N4i). **Rendering:** none.

**Migration:** none for stores written under the shipped expiry table (§2c-ii row 3: they cannot contain a decayed
out-of-range value). For a host that mapped DECAY with a factor > 1 or NaN **before** this fix, rows already written
remain unreadable; that is §10 Q2, unchanged by A–D.

---

## 5. Regime analysis — where does this behave differently?

- **Repeated maintenance runs compound**: c·fⁿ, non-increasing for f ∈ [0, 1]. **That is the guarantee.** In real
  arithmetic the floor is reached in finitely many runs whenever f < 1 and the floor is > 0, but **this is not a
  runtime guarantee**: floating-point products can reach a fixed point at or above the floor (`5e-324 × 0.9 == 5e-324`,
  at a floor of `5e-324`, round 1's finite-decay note), so an edge can stay active indefinitely. No progress rule is specified; eventual
  invalidation is not promised. Tested by running `expire()` repeatedly (N4).
- **The boundaries**: f = 1.0 never decays; f = 0.0 drives confidence to 0 in one run (invalidated if floor > 0);
  floor = 0.0 never invalidates by decay; floor = 1.0 invalidates every decayed fact below 1.0. All four are tested
  (N4b′, N4).
- **Concurrency** (new; R1-02): `maintain()` overlapping another write to the same edge, in the same process (the
  store's lock is per instance and held per statement group) or across connections. Before D, the overlap loses the
  other write in all three behaviours (§2c-ii row 11). After D, each transition is serialised with the other writes by
  SQLite's writer lock, and decides from what they committed (N4h). Two `maintain()` runs overlapping each other
  compose the same way: the later transition decays the earlier one's result.
- **Legacy serialisations**: a row written by an earlier release, whose `json` differs from today's serialiser in key
  order or float form, is processed like any other (N4h's control).
- **Cost of C**: one re-validation per edge write. Measured as a microbenchmark only, of v4.1's body
  `Edge.model_validate(e.model_dump())`: ≈ 20 µs per edge against ≈ 11 µs for `model_dump_json()` alone (CPython 3.14.7, c6a.2xlarge, `timeit`, best of 5 ×
  20,000; 2026-10-10). v4.2's body (`model_dump_json()`, then `Edge.model_validate_json` of those bytes) is **not
  measured**. **Not a workload measurement**: no ingest or maintenance run was timed. **Cost of D**: one
  `BEGIN IMMEDIATE` transaction per due edge instead of one per written edge; not measured.
- **Scale** does not enter: the rule is per edge, and the tests use small constructed stores, which reach every
  regime above. **Cold vs warm**: none (no cache).

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| **N4** (confidence half) no maintenance operation raises `confidence` | `test_no_maintenance_op_raises_confidence` — property-based over a random sequence of `expire()` runs on edges of every volatility, with DECAY mapped for the test, under valid configs: every edge's confidence after ≤ before, and in [0, 1]. **Consolidation, the other maintenance operation that writes confidence,** is bound by the existing `tests/test_lifecycle.py::test_consolidation_output_is_no_stronger_than_its_weakest_input` | CI |
| **N4b** `MemoryConfig` rejects both bounds outside [0, 1], NaN and ±inf, and `bool` | `test_config_bounds_are_validated` — both fields × {>1, <0, nan, +inf, −inf, True, "0.5", the nearest floats beyond each bound, ±10**400 (v4.2, R3-03)}, at construction, assignment and `expire()` entry, must raise `ValueError` naming the field | CI |
| **N4b′** the exact boundaries remain accepted | `test_boundary_configs_are_still_valid` — 0.0, 1.0, `0` and `1` on both fields, construct and assign. *A regression test: the cheapest wrong fix is an exclusive bound.* | CI |
| **N4b-assign** the bounds hold on assignment | `test_config_bounds_hold_on_assignment` — every rejected value of N4b, assigned after construction, raises, and the field keeps its old value | CI |
| **N4c** (restated from 0002, scoped to edges) no write path stores an **edge** outside a declared bound; every `confidence` writer the census sees is declared, and every other occurrence of an unvalidated write's tokens is classified | `test_declared_bounds_hold_on_every_write_path` — **enumerated from the models**, not hand-listed: for every pydantic field in `veracium.schema` carrying `Ge`/`Le`/`Gt`/`Lt`, (i) construction past the bound raises, (ii) assignment raises (frozen model or `validate_assignment`), and (iii) **the AST census of `specs/evidence/0048/census_0048.py`** (every `model_copy(update=…)` writing a bounded field, every whole-`provenance` replacement, and nothing UNRESOLVED) **equals a declared table with each site's reason** ("validated", or "in range by its inputs: <inputs>"), and (iv) **the token tripwire of `specs/evidence/0048/tripwire_0048.py`** (every non-comment token an unvalidated write of `confidence`, or a write of the edges table, must contain) **equals its hand-classified snapshot `specs/evidence/0048/tripwire_0048_classified.tsv`** as a multiset (`tests/test_0048_evidence.py::test_every_tripwire_hit_on_this_tree_is_classified`). A new writer **of a form the census sees** (listed, or refused as UNRESOLVED) without an entry fails (iii); a new writer of **any other form carrying a trigger token** fails (iv) until it is classified. **Residual, named:** a write carrying no trigger token, that is, a field name built from parts and reached through no trigger name (ctypes, a C extension), a SQL write verb built from parts, or SQL read from outside `src/veracium/*.py`; a planted control of it is silent in both instruments (`tests/test_0048_evidence.py::test_tripwire_0048_fires_on_every_planted_attack`). *Neither inventory is a universal persistence guarantee; C is the guarantee, and only for edges* | CI |
| **N4d** configuration refusal is one unit: nothing is written | `test_decay_config_refusal_writes_nothing` — a **mixed-volatility ordered fixture** (an expired TRANSIENT edge listed before an expired SLOW edge, SLOW mapped to DECAY) under a duck-typed config whose factor is each of {2.0, −1.0, nan, True, "0.5"} and, separately, whose floor is each of {2.0, −0.5, nan}: `expire()` raises `ValueError`, and a **complete store snapshot** (every table, the counters and 0029's journal included) is byte-identical to before; the same on an **empty** store | CI |
| **N4d-prefix** a later ordinary failure keeps the stated prefix behaviour | `test_a_later_failure_keeps_the_processed_prefix` — a valid config, an injected store failure on the second due edge: the first edge's transition is committed, the second's is not, and the error propagates | CI |
| **N4e** a valid config never makes B raise | `test_valid_decay_never_raises` — every factor/floor pair on a grid including both boundaries, over confidences {0, 0.3, 0.9, 1.0}: `expire()` completes and every stored row reads back | CI |
| **N4f** no edge write bypasses the validating serialiser, and the serialiser refuses an out-of-bound edge | `test_every_edge_write_goes_through_the_validating_serialiser` — AST over `src/veracium/store/sqlite.py`: every write of the edges table's `json` column is made by the one write method, which binds and journals the helper's single captured bytes, §4C's closed grammar refuses every other form, and **every reference to the store's connection is one the gate resolves** (a direct call whose SQL and bound values it reads, or a non-write listed in the binding inventory with its reason); any other reference fails: an alias, `executemany`, a cursor, `getattr`, the unbound method, the connection passed as an argument, the instance `__dict__`, a second connection (R2-01); `test_the_store_refuses_an_out_of_bound_edge` — an edge whose provenance carries confidence 1.8, **its nested `Provenance` built with `model_construct`** as a buggy path would, is refused by `add_edge`, and the table is unchanged; **`test_the_store_binds_the_bytes_it_validated`** (v4.2, R3-01) — the reviewer's schedule: validation succeeds, a second thread replaces the edge's provenance with confidence 1.8, the writer commits, and the stored row and every read carry 0.8 | CI |
| **N4g** the factor is validated independently of the current confidence | `test_factor_is_validated_whatever_the_confidence` — confidences {0.0, 0.3, 0.9} × factors {2.0, the nearest float above 1.0, −1.0, nan, True}: each refuses at entry. **`0.3 × 2.0 → 0.6` is the retained regression** that a range-only implementation must fail; `0.9 × 2.0` alone cannot distinguish them | CI |
| **N4i** DECAY keeps the shipped result (R2-02) | `test_decay_keeps_the_shipped_result` — SLOW mapped to DECAY, one due edge per case, against this table of the shipped `expire()` (`decayed`, active, stored confidence, flag): retained 0.9 × 0.5, floor 0.3 → 0, active, 0.45; **below the floor** 0.9 × 0.5, floor 0.5 → 1, retired, **0.9**; **exactly at the floor** 0.6 × 0.5, floor 0.3 → 0, active, 0.3; factor 1.0 → 0, active, 0.9; factor 0, floor 0 → 0, active, 0.0; factor 0, floor 0.3 → 1, retired, 0.9; an already-flagged edge, retained → 0, active, 0.45, still flagged. The returned counts and the stored edge equal the table. The table was read from the shipped `expire()` at `c1c9ecf` (the contract harness checks it against the tree it runs on). Also assert the side effects of the retiring case: its journal row (`invalidated`, reason `decayed`) and that the wiki is **kept**, as 0004 W3 keeps it for `decayed` (v4.1; v4 said "and the wiki drop", against the shipped meaning) | CI |
| **N4h** the expiry transition decides from the row committed when it runs | `test_expiry_is_decided_from_the_current_row` — two real connections, A paused deterministically after its listing, B committing, A resuming, for the four cases of §2c-ii row 11 (`confirm`, `confirm95`, `lapse`, `decay`): **B's committed state is kept** and A applies only what is due on it; the **serial control** (B, then A) gives the same committed state; and a **legacy-bytes control**: a row stored with valid, non-canonical `json` (keys reordered) is processed, not skipped | CI |

**Planned mechanism mutants** (the closure-mutant rule of 2026-10-10 applies). Each must be killed by the cells named,
with the honest controls passing:

| mutant | reintroduces | killed by |
|---|---|---|
| construction check removed | N4b | `test_config_bounds_are_validated` |
| assignment check removed | N4b-assign | `test_config_bounds_hold_on_assignment` |
| assignment sets before validating | N4b-assign (old value lost) | `test_config_bounds_hold_on_assignment` |
| exclusive bound (`0 < x < 1`) | N4b′ | `test_boundary_configs_are_still_valid` |
| NaN-blind comparison (`x < 0 or x > 1`) | N4b (nan) | `test_config_bounds_are_validated` |
| `bool` accepted (no explicit refusal) | N4b | `test_config_bounds_are_validated` |
| the entry validation removed, B and C intact | N4g | `test_factor_is_validated_whatever_the_confidence` (`0.3 × 2.0`) |
| the floor left unvalidated at entry | N4d | `test_decay_config_refusal_writes_nothing` (floor 2.0) |
| the entry validation moved back inside the DECAY branch | N4d (unit) | `test_decay_config_refusal_writes_nothing` (the TRANSIENT edge is lapsed first) |
| decay write back to unvalidated `model_copy`, entry check also removed | N4d | `test_decay_config_refusal_writes_nothing` |
| a copy site writing `confidence` removed from the declared table | N4c | `test_declared_bounds_hold_on_every_write_path` |
| a writer of a form the census does not see, its trigger tokens left unclassified | N4c (iv) | `test_every_tripwire_hit_on_this_tree_is_classified` |
| the store helper serialises without validating | N4f | `test_the_store_refuses_an_out_of_bound_edge` |
| the helper accepts an instance without revalidating nested data | N4f | `test_the_store_refuses_an_out_of_bound_edge` |
| **(v4.2, R3-01)** the helper validates one observation and returns another (v4.1's two-observation body); validates the capture and returns a fresh dump; returns the capture unvalidated | N4f | `test_the_store_binds_the_bytes_it_validated` |
| **for each of the declared edge writers:** that writer bypasses the write method | N4f | `test_every_edge_write_goes_through_the_validating_serialiser` |
| **for each connection form the gate does not resolve:** a writer reaches the connection that way | N4f (R2-01: `executemany`; an alias of `execute`; `getattr`; a cursor; SQL held in a variable; parameters held in a variable; the unbound `Connection.execute`; a second connection; the instance `__dict__`) | `test_every_edge_write_goes_through_the_validating_serialiser` |
| a writer calls the helper, or the journal writer, itself | N4f | `test_every_edge_write_goes_through_the_validating_serialiser` |
| **(v4.2, R3-02) for each form the round-3 reviewer found:** an edge dump bound outside the write method by annotated rebinding, a loop target, unpacking, a named expression, or with the helper shadowed by a lambda; `WITH … UPDATE edges`; `UPDATE main.edges` | N4f | `test_every_edge_write_goes_through_the_validating_serialiser` |
| **(v4.2) the write method's own forms:** an edit to the write method or its deferred journal; a second helper call in it; a journal of other bytes; the deferred journal not emitted, emitted twice or after its scope, or swallowing an exception; a non-constant or second `defer`; a name shadowed by an instance or class attribute, a subclass or a same-named function; an f-string or `executescript` edges write; a non-literal SQL site unlisted; a dynamic table's domain gaining `edges` | N4f | `test_every_edge_write_goes_through_the_validating_serialiser` and the deferred journal's cells |
| **(v4.2, R3-03)** the bound check converts an integer to float before comparing it | N4b | `test_config_bounds_are_validated` (±10**400) |
| the transition decides from the listing (read outside the transaction) | N4h | `test_expiry_is_decided_from_the_current_row` (all four cases) |
| a write conditional on (confidence, active) as read | N4h | `test_expiry_is_decided_from_the_current_row` (`confirm95`) |
| a conditional write binding the read model re-serialised | N4h | `test_expiry_is_decided_from_the_current_row` (legacy-bytes control) |
| a conditional write on the row as read in place of the in-transaction read | N4h | `test_expiry_is_decided_from_the_current_row` (`decay`) |
| a retained decay counted as `decayed` | N4i (R2-02) | `test_decay_keeps_the_shipped_result` (`retained`) |
| below the floor, the decayed confidence stored | N4i (R2-02) | `test_decay_keeps_the_shipped_result` (`below the floor`) |
| the floor comparison inclusive (`<=`) | N4i | `test_decay_keeps_the_shipped_result` (`exactly at the floor`) |

**Reproducer retention:** §2c-ii row 5's run becomes the honest control of N4d (DECAY mapped, factor 0.5 → 0.45, read
succeeds); row 11's serial control is N4h's.

---

## 7. Failure modes and reversibility

- **Silent failure today**: a host maps DECAY with factor > 1; nothing is visible until the next read of that user's
  edges raises, possibly days later. And on the shipped table, a `maintain()` that overlaps a user's `confirm()` can
  revert it with no error anywhere. **After**: a bad `MemoryConfig` raises at host startup; a bad duck-typed config
  raises at `expire()`'s entry; an overlapping operation's committed state is kept.
- **Reversible?** A–C are refusals and write nothing. D changes which state a transition reads, not what it writes. A
  host that relied on `decay_factor > 1` (to raise confidence) loses that behaviour, which N4 forbids.
- **Unit of refusal (R1-03).** **Configuration refusal is whole-run:** it happens at entry, before any edge is read,
  so nothing is written (N4d). **A later ordinary failure** (a store error, a lock refusal, a validation failure C
  raises on a path A and B did not cover) **keeps the per-edge prefix behaviour**: each transition is atomic, the
  transitions committed before the failure stay committed, the failing one is rolled back, and the error propagates
  (N4d-prefix). `expire()` is not made one transaction across edges; that is unchanged and stated.
- **Existing tests that store an out-of-bound edge on purpose** would now be refused by C; the implementation finds
  them by running the suite, and each is either a test of the old defect (rewritten to expect the refusal) or a bug.
- **Attack surface**: none new. The change removes one way for a configuration value to influence stored state
  outside its declared range, and one way for maintenance to undo a user's act.

---

## 8. Claims and limits

**What we will say** (CHANGELOG): *"`MemoryConfig` now rejects `decay_factor` and `confidence_floor` outside
[0, 1] (and NaN/±inf/booleans), at construction and on assignment; `expire()` validates both at entry, for any config.
Expiry now decides each fact's transition from its current stored state, so a `maintain()` that overlaps a
`confirm()` no longer reverts it. **Who should take this:** hosts that run `maintain()` alongside user operations,
set either bound, or map a volatility class to `ExpiryBehavior.DECAY`. With the shipped expiry table the decay path is
not reached."*

**What this does NOT establish:**
- that confidence values are calibrated or meaningful; only that maintenance keeps them in range and never raises them;
- that a decayed fact is eventually invalidated (§5: float fixed points);
- any bound on **episode** provenance at storage (C covers edges; the consolidation output is in range by its inputs,
  §4C). **Named follow-up, on the owner's ruling (§10 Q6):** storage bounds for every `Provenance` carrier, starting
  with the episode path's `json`-writing SQL statements in `store/sqlite.py` (ten at `6c0eab6`, by two independent
  AST walks of its string constants);
- anything about the **disclosure** half of N4 (its test exists and is unchanged);
- validation of any other `MemoryConfig` field;
- that `expire()` is one transaction across edges (§7);
- that values already stored out of range are repaired (C refuses new ones; §10 Q2);
- that `DEFAULT_EXPIRY` edits are a supported configuration surface.

---

## 9. Brief for the external reviewer

- **Least sure of:** (1) D's scope includes CONFIRM and LAPSE on the owner's ruling (§10 Q5): they are not this
  spec's confidence invariant, but they are the same transition and the shipped-reachable part of R1-02's class; tell
  us if that belongs elsewhere; (2) whether
  C's gate recognises every edge write form (it now refuses an unrecognised form rather than skipping it);
  (3) whether N4h's deterministic two-connection schedule covers the interleavings that matter (it pauses between
  listing and write; a pause inside the transaction cannot be reached, since `BEGIN IMMEDIATE` excludes other
  writers).
- **Where we may have overstated:** §2c-ii row 10 scopes 0002's v7 approval to its headline invariant on purpose.
- **What would change our minds:** evidence that hosts map DECAY in practice (then Q2's repair becomes blocking), or
  that the duck-typed `config` is a documented extension point (then B is the primary control, not defence in depth).
- **Reviewer-safe copy:** nothing generalised.

### Review closure — round 1

| finding | v3 |
|---|---|
| **R1-01** validating the product does not validate the factor | §4A–B: one validator, both fields, at entry, independent of confidence, captured once; N4g with `0.3 × 2.0`; mutant "entry validation removed, B and C intact". Reproduced at `4ea1ce5` (§2c-ii row 12) |
| **R1-02** a concurrent decay can overwrite a lower committed confidence | §4D: decided from the current row inside one write transaction; §5 concurrency; N4h with two connections, a serial control and a legacy-bytes control; four mutants (three at v3, the fourth added at v3.3 by H-01). **Wider than reported:** the shipped CONFIRM and LAPSE behaviours lose a `confirm()` the same way (§2c-ii row 11); in scope on the owner's ruling (§10 Q5). The redaction skip moves inside the transaction. No monotonic guard in `add_edge` |
| **R1-03** refusal and partial failure disagree | §4B, §7, N4d, N4d-prefix: configuration refusal at entry (whole-run, store byte-identical, empty store included); later failures keep the per-edge prefix |
| **R1-04** the bounded-write claim exceeds C's edge-only boundary | C scoped to edges (§4C, §8); five writers by an AST census that also lists whole-`provenance` replacements (§2c-ii row 8); consolidation in range by its inputs, bound by the existing test; per-writer bypass and ignored-return mutants; nested revalidation (N4f); episodes stay outside C on the owner's ruling, a named follow-up (§10 Q6) |
| **R1-05** (baseline fixture, not 0048) | fixed in the tree at `6c0eab6`, separately from this spec |
| the finite-decay note (the verdict's low-severity note on §5) | §5: non-increase promised; finite time stated as real-arithmetic intuition; `5e-324` fixed point named |
| Q4 | resolved: the narrow `__setattr__`, as answered (§10) |
| archive notes | §2c-ii's prose rows are scripts with recorded outputs; the generated inventories ship; the runnable contract harness of §4, a model with every §6 mechanism mutant outside N4c run against it, ships as `specs/evidence/0048/contract_harness_0048.py`; the capture's offline command, skip inventory and interpreter preflight are the package's (dev) |

### Review closure — round 2 (v4; the verdict ACCEPTED the design of v3.3)

| finding | v4 |
|---|---|
| **R2-01** (medium; implementation and evidence obligation) the model's writer gate passes `executemany` and a bound `execute` alias | §4C and N4f: the gate fails closed by the connection's receiver; nine forms (the reviewer's two, `getattr` and a cursor found by research, and five more of the class) are mutants of one §6 row. Over the model, `specs/evidence/0048/contract_harness_0048.py` kills all nine. At implementation the same rule runs over the store's connection, with the binding inventory naming each non-write form it resolves |
| **R2-02** (medium; compatibility obligation) the model's decay count and below-floor stored state differ from the shipped baseline | §2, §3 and §4D state the shipped meaning; N4i holds it with a fixed table of seven cases (the reviewer's two and five more from research's two-arm diff over thirteen branches, which found no third mechanism) and three mutants. The harness's model now keeps that meaning, and N4i checks its table against the tree's own `expire()` |
| editorial: §9's R1-02 row said three mutants | four, with when each was added |
| editorial: §5's fixed point is at the floor | "at or above the floor" |
| owed at implementation (the verdict, not reopened) | the actual N4 results; the per-writer mutant matrix and binding inventory over the real store, D's new writer included; current-row traces with journal, count and cache effects; the no-op and current-volatility branches; the store interface's declaration of the transition and an explicit contract for other backends; the baseline reproduction tests that assert today's defects, inverted or replaced |


### Review closure — round 3 (v4.2; the IMPLEMENTATION returned for amendment, the design acceptance stands)

| finding | v4.2 |
|---|---|
| **R3-01** (medium; data integrity) the helper validates one observation of a mutable edge and serialises another | §4C: one captured serialisation, validated and returned; N4f's regression with the reviewer's schedule; the two-observation body is a named mutant |
| **R3-02** (medium; implementation and evidence obligation) N4f accepts an edge dump rebound by forms the gate does not see, a shadowed helper, and two SQL forms | §4C: one write method, no writer holds the bytes, a closed grammar refused over inventory, SQL classified by SQLite's authorizer, a test-time authorizer as a complement; the reviewer's seven forms and the method's own are executable gate mutants (§6) |
| **R3-03** (low) `10**400` raises `OverflowError` instead of the specified `ValueError` | §4A: an integer compared exactly first; N4b's ±10**400 cells at construction, assignment and entry |
| closed in round 3, not reopened | R2-01's two concrete forms; R2-02; the design acceptance of round 2 |

---

## 10. Open questions

| # | question | who decides | by when | class |
|---|---|---|---|---|
| **Q1** | Include **C**? **RESOLVED 2026-10-10: "Yes, guard the store"** (the owner, first-hand in the dev session, relayed by dev). C and N4f are in. | owner | — | resolved |
| **Q2** | **Repair** for rows already written out of range by a host that mapped DECAY: a doctor check plus a repair verb, or a documented manual fix? No shipped configuration can have written them (§2c-ii row 3); round 1 found no evidence of affected deployed stores and agreed it may stay a pre-release decision. | owner + dev | before the release carrying this | pre-release |
| **Q3** | Should DECAY stay reachable only by editing a module dict, become a `MemoryConfig` field, or be removed? | owner | — | deferred |
| **Q4** | Assignment validation: `__setattr__` on the two fields or a frozen/validated config type? **RESOLVED 2026-10-11:** the round-1 reviewer approved the narrow `__setattr__`; dev's co-decision agrees (coordination ledger `2c194fb`), with these conditions, now §4A: validate before setting so a refusal keeps the old value; refuse booleans explicitly; keep integers and both inclusive endpoints; one validator for construction, assignment and `expire()`'s entry. | dev + external reviewer | — | resolved |
| **Q5** | **Scope of §4D:** all three expiry behaviours, or DECAY only? **RESOLVED 2026-10-11T19:10:51Z: "All 3"** (the owner, first-hand in the dev session, relayed by dev; coordination ledger `2b930e2`), on research's and dev's joint recommendation: CONFIRM and LAPSE are on the shipped table and lose a user's `confirm()` today (§2c-ii row 11). | owner | — | resolved |
| **Q6** | Should C extend to **episode** writes (every `Provenance` carrier protected at storage), or stay edge-only with the consolidation dependency stated? Round 1: either, if named and tested. **RESOLVED 2026-10-11T20:04:32Z: "Q6 - edges only"** (the owner, first-hand in the dev session, relayed by dev; coordination ledger `9cdd856`), on research's and dev's joint recommendation: no shipped producer writes an episode out of range (§4C), and the episode path would more than double C's writer census. Every `Provenance` carrier at storage is a named follow-up (§8). | owner | — | resolved |

---

## Reviewer checklist

- [ ] §3 has no unanswered cells (decay is unary: a state-transition table, every class enumerated from the enums)
- [ ] Prohibitions AND permissions tested: N4b (refusals) and N4b′/N4e (boundaries and valid grids accepted)
- [ ] Every default fails closed: a bad bound refuses at construction; any bad config refuses at `expire()`'s entry
- [ ] §2c has a row per uncontrolled input, the schedule included; the one without an invariant here (older rows) is named and sent to Q2
- [ ] §2c-ii: every reach claim carries its command and result, and the prose rows are scripts
- [ ] §2 consumers enumerated by grep
- [ ] Every §6 invariant has a check, and each planned mutant names the cell that must kill it
- [ ] §5 regimes are reached by constructed stores, concurrency by two real connections
- [ ] §3b: n/a with reason
- [ ] §8 states what this does not establish
- [ ] §10 questions each carry a class
