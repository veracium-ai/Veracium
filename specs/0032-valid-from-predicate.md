# Feature spec: the valid-time predicate at the present

Spec-Status: draft

| | |
|---|---|
| **Version** | **v1** — drafted 2026-09-04 by dev on Quentin's ruling of the same day (**option (a)**: "a short owner-accepted `valid_from`-predicate spec"), the ruling that resolves the second leg of specs/0031 §5's ordering precondition. The mechanism this spec pins is ALREADY SHIPPED at `d83775d` (the S2 commit, CI 33870294444 test lanes green; the process gate's red and its closure at `34a16b0`/`76a205b` are disclosed in that line's history) — this document exists so that the precondition's letter ("that spec exists, is accepted, and lands") is satisfied by a specification, not by an inference from a changelog. Research co-checks against 0030 §2c/V-NORM-TOTAL, 0028 §4a, 0030 §3/§4e and 0031 §5 before the acceptance word (done 2026-09-04; its edits are in this text). |
| **Author / session** | dev (veracium-69); mechanism, cells and CHANGELOG entry by dev; the ruling and the acceptance Quentin's; research's harness Tier-7/S2 receipt at `d83775d` is the acceptance instrument (both directions observed live) |
| **Scope** | one predicate, two records, the present only: `Edge.valid_now`, `Episode.valid_now`, folded into `Edge.assertable` / `Episode.assertable`. No change to the as-of path (0028/0030), to ingest's skew refusal (`MAX_FUTURE_SKEW`), or to the gate's routing (0023 §4a-iv) |
| **Acceptance** | owner-accepted, no external round — specs/0031 round-1 F6 requires that the spec "exist, be accepted, and land" and does not demand an external round for it; the owner's option-(a) ruling of 2026-09-04 fixes that path; see `## Review closure` |

## 1. Problem and motivation

**This is the specification that specs/0031 §5's ordering precondition
awaits** — the one its round-1 finding F6 required to "exist, be accepted,
and land" before Phase A. Its acceptance discharges that leg; nothing else
does, and no reader should have to reconstruct that from version cells.

Until `d83775d`, `Edge.assertable` was `active and not quarantined and not
use_only` — it consulted **no time predicate**. A fact whose `valid_from`
had not yet arrived was therefore assertable *now*: recalled into the
GROUNDED block, compiled into the wiki, stated as true a day before it
became true. specs/0030 §4e measured this live (harness Tier-7 / S2,
2026-08-31): an MCP `remember` with a `date` inside `MAX_FUTURE_SKEW`
(one day) wrote an edge with `valid_from` 2026-09-01 that was assertable
on 2026-08-31. Ingest refuses dates *beyond* the skew; inside it the
window was open, and reaching it needed only a `date` argument on the
MCP `remember` tool.

**What happens if we do nothing:** specs/0031 Phase A (`capability=direct`)
lets MCP writes reach `MENTIONABLE` without the host-side floor that today
keeps this a host-only anomaly — so an agent could assert, today, a fact
that becomes true tomorrow. That is why the owner sequenced this predicate
AFTER the joint arc and BEFORE Phase A (0031 §5), and why the reviewer of
0031 credited that qualifier as necessary.

**Alternatives rejected.** (i) *Refuse future dates at ingest entirely* —
rejected: a fact known today to become true tomorrow (a start date, a
move) is legitimate memory; the defect is asserting it early, not storing
it. (ii) *Route the check through the as-of classifier* (`assertable_as_of`
with `T = now`) — rejected: 0030's as-of path is accepted design and not
yet shipped (`grep -rn assertable_as_of src/` → 0 hits), and 0030
V-CURRENT-UNCHANGED deliberately leaves the current path alone; the
present needs one conjunct on the property every consumer already reads.
(iii) *Change `active`* — rejected: the future-`invalidated_at` cell is
the 0019 question 0030 leaves open; this spec touches only the lower
bound.

---

## 2. Field contracts touched

Consumers enumerated by command, not recalled (`grep -rn "\.assertable" src/veracium/`
→ **22 call sites**, 2026-09-04):

| field | read / written | its **documented** contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `Edge.valid_from` (`schema.py:443`) | READ | "when the fact became true" — the first-known, immutable valid-time lower bound (0028 §2, 0030 §2) | recall, combining, graph clustering (`graph.py:695-908`), export, `confirm` readback (`__init__.py:1463`) | YES — read-only; the predicate reads it, never writes it |
| `Edge.invalidated_at` / `active` | READ (unchanged) | active ⇔ `invalidated_at is None` | every consumer of `active` | YES — untouched; the interval's upper bound stays with `active` (0019's cell) |
| `Edge.assertable` (`schema.py:528`) | property, ONE conjunct added | "safe to state as fact" | `__init__.py` (recall ×6, contested set, confirm), `gate.py` (partition), `scope_read.py` (views), `compile.py`, `selfcheck.py` (×2), `graph.py` (×2), `proactive.py` (×3), `store/sqlite.py:166` — the 22 sites | YES — the contract gains the clause its words always implied: a fact is not safe to state before it is true |
| `Episode.date` (`schema.py:565`, ISO date string) | READ | "ISO date the event occurred (may differ from wall clock)" | gate rendering, proactive, selfcheck | YES — read-only |
| `Episode.assertable` (`schema.py:617`) | property, ONE conjunct added | 0023 §4a-iv's shared predicate for text consumers | `gate.py:137-139`, `compile.py:146`, `selfcheck.py`, `proactive.py:210` | YES — same clause; **LIFECYCLE MUST NOT CALL THIS** stays true (0023 §7a) |
| `schema.utcnow` | READ | the UTC-aware clock | the `valid_from` default factory | YES — the predicate reads the same clock the default writes |

**New:** `schema.as_utc(dt)` — normalizes any datetime to UTC-aware before
comparison (naive taken as UTC, aware converted). Two obligations meet here
and they have different owners: the **normalize-before-compare** obligation
is 0030's (its §2c untrusted-inputs row: naive/aware mismatch → normalise to
UTC-aware BEFORE compare; V-NORM-TOTAL, round-2 F7). The **naive-value-
denotes-UTC** interpretation is NOT 0030's — 0030 nowhere decides what a
naive value means. It is the store's convention, pinned HERE by the shipped
`as_utc` and normative for any future `as_utc_required` implementation on
the as-of path: an as-of implementation that read a naive `valid_from`
under a different rule (typed refuse, local time) would break
V-AGREE-AS-OF while both specs still read as consistent.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| `valid_from` written by an older version (naive datetime; 0030 round-2 F7's class) | n/a (required field, default `utcnow`) | naive → `as_utc` takes it as UTC, compares; never raises | — | a stored value cannot make the predicate fail OPEN: any value not `≤ now` is not assertable | V-NORM (`test_naive_valid_from_is_normalized_not_crashed`, `test_aware_non_utc_valid_from_compares_in_utc`) |
| `valid_from` supplied through MCP `remember(date=...)` | absent → `utcnow` (true now) | non-ISO → ingest refuses (`ingest.py:83` class) | — | a future date beyond `MAX_FUTURE_SKEW` → ingest REFUSES (unchanged); inside the skew → STORED, NOT assertable until it arrives | V-LOWER-BOUND (`test_edge_valid_now_is_the_half_open_lower_bound`) + ingest's existing skew test |
| `Episode.date` (ISO date string, possibly with a time part) | required | a date after today → not assertable; the date part decides (`date[:10]`) | — | a future-dated episode is FENCED, never asserted (0023 §4a-iv) | V-EPISODE (`test_episode_valid_now_by_iso_date`) |
| the wall clock (`utcnow`) | — | — | — | a clock set backwards makes a true fact temporarily non-assertable (fails CLOSED, never open) | stated in §7; V-CLOSED-DEFAULT |

### 2c-ii. Assertions about reach — REQUIRED

| assertion | command that establishes it | result (2026-09-04) |
|---|---|---|
| the predicate is defined on both records and used only by their `assertable` | `grep -rn "valid_now" src/veracium/` | 6 hits: two definitions (`schema.py:510`, `:636`), two uses (`:536`, `:633`), two docstrings |
| every consumer of `assertable` inherits the clause | `grep -rn "\.assertable" src/veracium/ \| grep -vc "def assertable"` | 22 |
| the window is agent-reachable through the MCP surface | `grep -n "@server.tool" src/veracium/mcp_server.py`; `grep -n "def remember(" src/veracium/mcp_server.py` | 5 tools; `remember(... date: Optional[str] = None ...)` at `mcp_server.py:152` |
| ingest refuses only BEYOND the skew | `grep -n "MAX_FUTURE_SKEW" src/veracium/ingest.py` | `= timedelta(days=1)` (:35); `if dt > utcnow() + MAX_FUTURE_SKEW` (:83) |
| the as-of path is NOT in shipped code (so this spec cannot delegate to it) | `grep -rn "assertable_as_of\|facts_valid_at" src/veracium/ \| wc -l` | 0 |
| `as_utc` has exactly one caller today | `grep -rn "as_utc" src/veracium/` | definition `schema.py:28`; caller `:525` |
| the cells run | `$PY -m pytest tests/test_s2_valid_from_predicate.py -q -p no:randomly` | 16 passed |

---

## 3. Trust-class matrix — REQUIRED, blocking

The predicate is **unary and class-blind**: it reads `valid_from` (edges)
or `date` (episodes) and the clock, never author or disclosure. Classes
read from the enums today (`EvidenceAuthor`: user, third_party, system,
assistant; `Disclosure`: mentionable, use_only, quarantined) — the matrix
is a state-transition table over the four conjuncts of `assertable`:

| `valid_now` | `active` | `quarantined` | `use_only` | `assertable` before `d83775d` | `assertable` now | note |
|---|---|---|---|---|---|---|
| True | True | False | False | True | **True** | unchanged — every already-true, clean fact |
| **False** | True | False | False | **True** | **False** | **the only flipped cell** — a not-yet-true fact, whatever its author or disclosure |
| False | True | True | — | False | False | unchanged (quarantined never asserts) |
| False | True | False | True | False | False | unchanged (use_only never asserts) |
| any | False | — | — | False | False | unchanged (inactive never asserts; the upper bound stays here) |

- Can this cause a **user-asserted fact to become non-assertable**? Yes —
  exactly and only while its `valid_from` is in the future; it becomes
  assertable by itself when the time arrives, with nothing rewritten
  (`test_the_edge_becomes_assertable_by_itself_when_time_arrives`).
- Can it cause **non-user content to gain authority, confidence, or
  currency**? No — it only removes assertability; it grants nothing.
- Can it **clear `needs_confirmation`**? No.
- Does it **merge, drop, or overwrite provenance**? No — read-only.
- **Write-time or maintain-time?** Neither: a READ-time predicate evaluated
  at each consumer's call against the clock. No stored state changes.

---

## 3b. Authorization and scope

No user, tenant or scope boundary is crossed; the predicate SUBTRACTS from
the assertable set only, so no principal can see anything they could not
see before. It composes under 0020's `scoped_assertable` as a further
restriction (`gate.py:51-92`: the conjunction over `record_assertable` can
turn True into False, never the reverse).

---

## 4. Behaviour

- `Edge.valid_now` — `as_utc(valid_from) <= utcnow()`: the LOWER bound of
  the half-open valid interval `[valid_from, invalidated_at)` that 0028 §4a
  step 3 and 0030 §3's "time validity" gate (V-INTERVAL) state for the
  as-of path, applied at `T = now`. **At** `valid_from` the fact is valid (closed below).
- `Episode.valid_now` — `date[:10] <= utcnow().date().isoformat()`: an ISO
  date not after today's UTC date; lexical order on ISO dates is
  chronological; a time part does not decide.
- `assertable` on both records = the previous three conjuncts AND
  `valid_now`.
- **Rendering:** a not-yet-valid EDGE is withheld from recall's GROUNDED
  block exactly as an inactive edge is (not a claim, not asserted); a
  future-dated EPISODE is FENCED into the unverified section per 0023
  §4a-iv Q5 (visible as a claim, never asserted). The gate is unchanged
  (`gate.py:131-139`).
- **Interfaces:** none new. **Migration:** none — no stored state changes;
  an existing store with future-dated records simply stops asserting them
  until they are true. **Unrecoverable:** nothing.

---

## 5. Regime analysis

- The predicate costs one comparison per `assertable` read; 22 call sites,
  no regime where cost changes shape.
- **The only regime that matters is the clock**: `valid_from` within
  `(now, now + MAX_FUTURE_SKEW]` — the window ingest admits and this
  predicate now withholds. `test_edge_valid_now_is_the_half_open_lower_bound`
  reaches it at +1 s and +23 h; the harness Tier-7/S2 receipt reached it
  live (hours_ahead=12) and watched the same edge flip at +8 s.
- Cold vs warm: none. Stable, on by default — the regime is reached by tests.

---

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where it runs |
|---|---|---|
| **V-LOWER-BOUND** `assertable ⇒ as_utc(valid_from) ≤ now`; equality is valid | `tests/test_s2_valid_from_predicate.py::test_edge_valid_now_is_the_half_open_lower_bound` (5 positions incl. AT `valid_from`, +1 s, +23 h) | CI |
| **V-ONE-CONJUNCT** the predicate is the only new refusal; the other three flags unchanged | `::test_future_valid_from_is_the_only_new_refusal` | CI |
| **V-SLEEPER** the same stored record becomes assertable when the clock passes `valid_from`, nothing rewritten | `::test_the_edge_becomes_assertable_by_itself_when_time_arrives` | CI |
| **V-NORM** UTC-aware comparison only (0030's obligation, §2c/V-NORM-TOTAL); naive taken as UTC — THIS spec's convention, binding on any future `as_utc_required`; aware non-UTC converted | `::test_naive_valid_from_is_normalized_not_crashed`, `::test_aware_non_utc_valid_from_compares_in_utc` | CI |
| **V-AGREE-AS-OF** the current path agrees with the as-of predicate `valid_from ≤ T` at `T = now` across a position sweep; the future-`invalidated_at` cell is NOT changed | `::test_the_0030_divergence_cell_is_closed` | CI |
| **V-EPISODE** the episode twin, by ISO date | `::test_episode_valid_now_by_iso_date` (5 dates incl. time parts) | CI |
| **V-GATE** the GROUNDED block excludes both sleepers; the edge is withheld, the episode fenced (0023 §4a-iv) | `::test_gate_grounded_block_excludes_not_yet_valid_records` | CI |
| **V-CLOSED-DEFAULT** an unresolvable or future value costs assertability, never grants it | every cell above refuses in the doubtful direction; the clock-backwards case in §7 | CI |
| **The live instrument** (acceptance): the frozen harness Tier-7 / S2 case, both directions | research's harness, run against `d83775d` under the FROZEN manifest digest `2ffb5ed5588dd482` (the measurement: inside-skew future `valid_from` → `assertable` False, violating the frozen pre-ruling expectation in exactly the predicted direction; the same edge, byte-unchanged, `assertable` True after its `valid_from` arrived — the +8 s live probe). The going-forward expectation is the RE-PINNED manifest `57d85ef2…` (S2's expectation flipped to `assertable: false` with the ruling, the sha, and the original prediction preserved in its `why`), staged in the harness tree and committed WITH this spec's acceptance — one owner word covering both, so the instrument reference is never ambiguous between the two digests | harness (research), receipt banked 2026-09-04 |

**Reproducer retention:** 0030 §4e's measured construction is the
permanent +23 h cell.

---

## 7. Failure modes and reversibility

- **Silent failure:** a clock set BACKWARDS makes already-true facts
  non-assertable until the clock catches up — the predicate fails CLOSED
  (withholds), never open. First symptom: a recall missing a fact "since
  <date>" whose date is in the apparent future. A clock set FORWARDS
  asserts a sleeper early — the same exposure the wall clock already
  gives ingest's skew check; not new.
- **Reversible:** trivially — nothing is written; the predicate is a read.
- **Partial failure:** none possible; no I/O.
- **Attack surface:** reduced, not created — the agent-reachable window
  (MCP `remember(date=...)` inside the skew) no longer yields an early
  assertion. A hostile receiver's `__getattr__` cannot reach this predicate
  (it reads model fields, not attribute lookups on foreign objects).

---

## 8. Claims and limits

- **What we say** (CHANGELOG, Unreleased, verbatim): "⚠ BREAKING
  (behaviour): a fact is not assertable before it is true … it stays stored
  and becomes assertable by itself when its time arrives (nothing is
  rewritten) … Who should take this release: hosts whose agents can write
  future-dated facts through the MCP `remember` tool — under 0031 Phase A's
  `capability=direct` (not yet shipped) that window becomes agent-reachable,
  and this release closes it first, as ruled."
- **What this does NOT establish:** it does not change the as-of path
  (0028/0030 remain accepted design, not shipped code); it does not touch
  the future-`invalidated_at` cell (0019's question — an edge with
  `invalidated_at` set stays inactive now, as before); it does not decide
  whether a future-dated EPISODE should be withheld rather than fenced —
  0023 §4a-iv's routing is applied unchanged and stated in §4; it does not
  represent a SUB-DAY sleeper episode — `Episode.date` is date-granular by
  its own contract, so an episode dated today with a future time part
  asserts now while an edge with `valid_from` later today is withheld until
  the instant arrives (deliberate; not this spec's question); and **it
  does not own the skew**: `MAX_FUTURE_SKEW` (one day) and the S1
  beyond-skew refusal at `ingest.py:83` are INHERITED from ingest, not
  set here — a future change to the skew is an ingest question, not a
  0032 one; this predicate applies whatever window ingest admits.
- **Measurements carry their commit:** the harness receipt is at
  `d83775d`; the 16 cells at the same commit; the partition guard's
  first-day catch (dotted/dataflow 4,583 → 4,594, the eleven accesses this
  predicate added) at `d83775d`.

---

## 9. Brief for the external reviewer

No external round is planned (owner-accepted; §Review closure). If one is
ever taken, the frame to attack: whether "the present" should be a single
`utcnow()` read per consumer call or a per-request snapshot (two consumers
in one recall could straddle a `valid_from` by microseconds — harmless in
direction, but a reviewer may want it stated); and whether a future-dated
episode belongs in the fenced section at all.

---

## 10. Open questions

- **Per-request clock snapshot** — decided by dev, class `deferred`: no
  consumer today compares two `assertable` reads for equality; if one ever
  does, a snapshot lands with it.
- **Future-dated episodes: fenced vs withheld** — decided by the 0023
  owner, class `deferred`: the fence is 0023's stated rule for every
  non-assertable episode and is kept; a withheld class would be a 0023
  amendment.

---

## Reviewer checklist

- [x] §3 has no unanswered cells; the operation is unary and the table is a state transition over the four conjuncts
- [x] §3's classes were read from the enums (`EvidenceAuthor`, `Disclosure`, 2026-09-04)
- [x] Prohibitions AND permissions are both tested — the +23 h refusal beside the AT-`valid_from` and −1 s permissions; the sleeper flip
- [x] Every default fails closed — a doubtful or future value costs assertability
- [x] §2c has a row per uncontrolled input, no empty invariant cell
- [x] §2c-ii carries the command and its printed result for every reach claim
- [x] §2 consumers were enumerated by grep (22)
- [x] Every §6 invariant has a check that runs in CI, plus the live instrument
- [x] §5's regime is reached by tests (+1 s, +23 h) and observed live
- [x] §3b: no principal sees anything new; the predicate only subtracts

## Review closure

**Owner-accepted (pending Quentin's acceptance word on this text), no
external round by design.** specs/0031 §5 records the owner's ruling of
2026-08-31 that the `valid_from` predicate closes "separately (option (b))";
0031's round-1 finding F6 required that a specification exist, be
accepted, and land before Phase A; Quentin chose option (a) on 2026-09-04
— this document — over recording the CHANGELOG and the `as_utc` docstring
as the specification. There are therefore no external-review findings to close.
What closes instead:

| # | obligation | closed by |
|---|---|---|
| 1 | the predicate LANDS | `d83775d` (`Edge.valid_now`, `Episode.valid_now`, `schema.as_utc`); `tests/test_s2_valid_from_predicate.py` — 16 cells |
| 2 | the acceptance instrument passes both directions | research's frozen harness Tier-7 / S2 receipt against `d83775d` (inside-skew future `valid_from` → `assertable` False; the arrived `valid_from` → True, nothing rewritten), 2026-09-04 |
| 3 | 0030 §4e's measured divergence cell reads agreement, the other cell untouched | `::test_the_0030_divergence_cell_is_closed`; 0030's implementation-note cell (research) |
| 4 | 0031 §5's precondition, both legs | leg 1 (owner-ruled, S2 instrument): #2; leg 2 (spec exists, is accepted, lands): this spec + its acceptance + #1 |
| 5 | the specification exists and is co-checked | research's co-check, 2026-09-04: every §2c-ii printed result re-derived from the tree; every line cite landed; §3's one-flipped-cell claim consistent with 0030 §4e; the §6 instrument row matched to the receipt and the staged re-pin; one substantive edit (the naive≡UTC attribution, §2/V-NORM — taken) and a citation family of four (taken, including the shipped `as_utc` docstring) |
