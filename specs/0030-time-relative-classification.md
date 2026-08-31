# Feature spec: time-relative trust classification

Spec-Status: draft

*Candidate authored by research (veracium-research), 2026-08-31; ADOPTED BY DEV 2026-08-31 at v2 (dev's internal review — D-1 bidirectional divergence, D-2 absorbed-unreachable, d-3 precedence, d-4 oracle pin — folded and re-read GREEN before adoption; the internal cycle ran both-check, roles inverted from 0027). The first of
two substrate specs Quentin ruled must precede a full 0028 v2 (as-of query):
0030 is the TRUST surface (this spec), 0029 the transaction-time carrier (dev-
led). 0028 r1 exposed that the shipped classifier cannot ground history at all
(`Edge.assertable` requires `active`); Quentin's ruling was to build the
time-relative trust surface CORRECTLY rather than ship a reference-only dodge.
Authored mechanically-complete from the start (0027/0028 template maturity), with
the round-1 lessons front-loaded — every totality claim is derived from the
AUTHORITATIVE registry (`DISPOSITIONED_REASONS`), never a field comment (0028
R1-1), and unknown reasons FAIL CLOSED.*

| | |
|---|---|
| **Author / session** | research (veracium-research); adopted by dev 2026-08-31 |
| **Version** | **v2** — dev internal review folded (D-1 bidirectional divergence + future-`invalidated_at` ruling; D-2 absorbed-unreachable; d-3 status precedence; d-4 frozen-oracle pin) |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (author) · dev (reviewer, roles inverted from 0027) |
| **External review** | REQUIRED — new trust surface; touches classification. Quentin's word given 2026-08-31; round 1 in preparation |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0019 / 0023 / 0026** — the current trust classes and the render-time
  classifier (`Edge.assertable`, `schema.py:501`; `_render_class`,
  `graph.py:283`). **UNCHANGED.** 0030 adds a PARALLEL time-relative classifier;
  it does not modify `Edge.assertable`, so the current recall path is
  byte-identical (V-CURRENT-UNCHANGED). This is the additive discipline 0027
  used.
- **0003** — reason-carrying, history-retaining supersession: the
  `invalidation_reason` this spec keys on (`schema.py:432`), and the retained
  history (`invalidated_at` set — "so history is queryable", `schema.py:421`).
- **the `DISPOSITIONED_REASONS` registry (`schema.py:407`)** — the AUTHORITATIVE
  closed reason set (seven: `disputed`, `corrected`, `superseded`,
  `revoked_source`, `lapsed`, `decayed`, `absorbed_duplicate`). 0030's
  historical-truth disposition is TOTAL over this set and derived from it, so a
  producer growing an eighth reason fails the registry-totality test until 0030
  dispositions it (mirroring W5 / `test_invalidation_reason_registry_is_total`).
- **0022 / 0023** — revocation / non-revival: `revoked_source` (0022's reserved
  seat) is withdrawn evidence and NEVER grounds at any T (V-NEVER).
- **0020** — scope (S1 principal boundary): `assertable_as_of` composes with
  `ScopeView` — a historical edge groundable-as-of-T is grounded ONLY for
  principals to whom it is assertable, and `shape()` still applies (0028 R1-5:
  "assertable-to-WHOM at T"). 0020 owns read visibility (0028 R1-5 corrected the
  0021 miscite).
- **0011** — `correct()`: the `corrected` invalidation whose retroactive-falsity
  this spec classes NEVER-groundable.

### What 0030 is NOT (scope fences — 0028 R1 lessons)
- **NOT a change to `Edge.assertable`.** The current classifier is untouched;
  0030 adds `assertable_as_of`. No recall regression (V-CURRENT-UNCHANGED).
- **NOT reason RESOLUTION.** 0030 CLASSIFIES a given edge at T (groundable /
  fenced / excluded / not-valid-at-T). It does NOT decide which edge a query
  returns — following `corrected`→corrector or `absorbed_duplicate`→absorber is
  the QUERY layer's job (0028 v2's reason→resolution table). 0030 says "a
  corrected edge is never groundable at any T"; 0028 says "when you hit one,
  resolve to the corrector."
- **NOT transaction-time.** 0030 is VALID-time classification only
  (`valid_from`/`invalidated_at`). The `observed_at` transaction axis and
  `known_as_of` are 0029 + a later 0028 phase.

---

## 1. Problem and motivation

`Edge.assertable` (`schema.py:501`) is `self.active and not self.quarantined and
not self.use_only`, and `active` is `invalidated_at is None` (`schema.py:478`).
So assertability is tied to being the **current** value: a historical edge —
even one that was validly, groundedly true throughout its interval — can NEVER
be asserted, only rendered as fenced context. 0028 round 1 named this the
"killer": "time and trust orthogonal," as written, cannot produce a historical
assertion at all, so as-of over history could only ever fence.

The current classifier **conflates two independent questions**:
1. *Is this the current value?* (`active` — `invalidated_at is None`)
2. *Is this trustworthy content?* (not `quarantined`, not `use_only`)

For a point-in-time question — "was Priya's city Boston in May?" — the honest
answer is grounded (Boston WAS her city then, validly held until it changed).
0030 **decouples** the two: it adds `assertable_as_of(edge, T)` = "was this edge
validly, trustworthily true at time T," keeping every trust exclusion intact.
This is the substrate 0028 v2 needs to return an ASSERTABLE historical answer
rather than a fenced one.

**Why this is delicate (the new trust surface Quentin ruled we build, not
dodge).** Decoupling assertability from `active` means a historical edge can now
ground. Done wrong, that is a laundering path: a `corrected` error, a `disputed`
claim, or `revoked_source` content could ground at some T. The whole spec is the
discipline that this CANNOT happen — a registry-derived, fail-closed allow-set
plus the time-invariant content-trust exclusions plus the scope composition.

## 2. Field contracts touched

`grep -rn` at author time (dev re-runs at implementation):

| field | read / written | contract | preserves? |
|---|---|---|---|
| `Edge.assertable` (`schema.py:501`) | READ, **UNCHANGED** | the current classifier | YES — 0030 adds a parallel predicate; current path byte-identical (V-CURRENT-UNCHANGED) |
| `Edge.invalidation_reason` / `valid_from` / `invalidated_at` (`schema.py:430-432`) | READ | the reason + valid-time interval 0030 keys on | YES — read-only |
| `DISPOSITIONED_REASONS` (`schema.py:407`) | READ + a PARALLEL disposition added | the authoritative reason registry | YES — 0030 adds `GROUNDABLE_AS_OF`, total over the same set, fail-closed |
| NEW `assertable_as_of(edge, T)` / `classify_as_of(edge, T, view)` | WRITTEN | the time-relative classifier primitive | additive |
| `ScopeView` (`scope_read.py:280`) | READ | composes for "assertable-to-whom at T" | YES — reuses the shipped lens |

### 2a. The `GROUNDABLE_AS_OF` registry (derived, fail-closed)
0030 adds a parallel disposition keyed on the SAME reasons as
`DISPOSITIONED_REASONS`, so it is total by construction and an unknown reason
fails closed:
```
GROUNDABLE_AS_OF: frozenset = frozenset({
    "superseded",          # was validly true until it changed
    "lapsed",              # staleness is not falsity
    "decayed",             # low-confidence-now is not was-false
    "absorbed_duplicate",  # redundant-but-true (the absorber carries it)
})
# Every OTHER reason — corrected, disputed, revoked_source, AND any reason no
# spec has named yet — is NEVER groundable-as-of. The runtime tests membership
# in this ALLOW-set (never a deny-list), so a new reason can only fence, never
# ground (the inverse of the WIKI_RETAINING bug internal-R1 fixed). A
# registry-totality test (like W5) requires every DISPOSITIONED_REASONS key be
# explicitly present-or-absent here, failing the build on an undispositioned new
# reason.
```
**`GROUNDABLE_AS_OF` is deliberately NOT `WIKI_RETAINING`.** They answer
different questions: `WIKI_RETAINING` = {lapsed, decayed, absorbed_duplicate} is
"does the CURRENT view survive this invalidation"; `GROUNDABLE_AS_OF` adds
**`superseded`** because "was it validly TRUE at T" is a different test — a
superseded fact was true until it changed, so it must NOT survive in the current
wiki (the value moved on) yet MUST be groundable as-of a T inside its interval.
That asymmetry (`superseded`: wiki-drop but as-of-groundable) is the whole reason
0030 needs its own registry rather than reusing `WIKI_RETAINING`.

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| the query time `T` | `None` → caller error (not 0030's concern; the as-of layer supplies T) | non-datetime → typed refuse | any datetime valid | T crafted to hit a `corrected`/`disputed` edge's old interval | **V-NEVER** — a never-groundable reason is fenced at EVERY T, including inside its interval |
| the edge's `invalidation_reason` | `None` → the edge is ACTIVE (current); classify by `Edge.assertable` | non-str → typed refuse | an eighth/unknown reason | a producer emitting a novel reason to try to ground history | **V-FAILCLOSED** — not in `GROUNDABLE_AS_OF` → NEVER grounds |
| the principal | `None` → unscoped (self); classify without the scope lens | via 0020 | — | a principal querying another's restricted history | **V-SCOPE** — composes with `ScopeView`; a shaped/invisible edge never grounds for that principal |

### 2c-ii. Assertions about reach — REQUIRED

| claim | invariant |
|---|---|
| "0030 never makes `corrected`/`disputed`/`revoked_source`/`quarantined`/`use_only` groundable at ANY T" | **V-NEVER** |
| "an unknown/eighth reason can never ground" | **V-FAILCLOSED** (allow-set membership, registry-total) |
| "0030 changes no current-recall behaviour" | **V-CURRENT-UNCHANGED** — `Edge.assertable` is not modified and the current recall path never calls `assertable_as_of`. The two predicates agree EXCEPT on two edge cells where valid-time and current-ness genuinely differ (§4e), in both of which `assertable_as_of` gives the temporally-correct answer; neither is a current-path change |
| "a historical edge grounds only for principals who may assert it" | **V-SCOPE** — 0020 composition |
| "0030 adds no field to `Edge`" | **V-ADDITIVE** |

## 3. Trust-class matrix — REQUIRED, blocking

The classifier is three independent gates ANDed — time validity, time-invariant
content trust, and the reason-keyed historical-truth disposition — then composed
with scope:

| gate | what it checks | time-varying? |
|---|---|---|
| **time validity** | `valid_from ≤ T AND (invalidated_at is None OR T < invalidated_at)` (half-open interval) | yes — the only time-varying gate |
| **content trust** | `not quarantined AND not use_only` | NO — a quarantined/use_only edge is unassertable at every T |
| **historical truth** | active → yes; else `invalidation_reason ∈ GROUNDABLE_AS_OF` | NO — a `corrected`/`disputed`/`revoked_source` edge is never-groundable at every T |
| **scope** (with principal) | `ScopeView` assertable-to-principal + `shape()` | per-principal |

**Load-bearing statement:** 0030 lets an edge be assertable-as-of-T ONLY when it
was BOTH validly-held at T (time + a groundable reason) AND is trustworthy
content (not quarantined/use_only) AND assertable to the principal. It never
relaxes a trust exclusion; it only removes the *current-ness* requirement, and
only for reasons that mean "was validly true then."

## 4. Behaviour

### 4a. The classifier — exact
```
def assertable_as_of(edge, T) -> bool:      # valid-time, principal-agnostic
    # 1. time validity (half-open [valid_from, invalidated_at))
    if not (edge.valid_from <= T and (edge.invalidated_at is None
                                      or T < edge.invalidated_at)):
        return False                         # NOT_VALID_AT_T
    # 2. content trust — time-invariant
    if edge.quarantined or edge.use_only:
        return False                         # never grounded, any T
    # 3. historical-truth disposition (fail-closed allow-set)
    if edge.invalidated_at is None:
        return True                          # active: it is the current value
    return edge.invalidation_reason in GROUNDABLE_AS_OF
```
`classify_as_of(edge, T, view=None)` returns a closed status with an **explicit
evaluation precedence (d-3)** — the first matching rule wins, so an edge meeting
several conditions gets the strongest-applicable, deterministically:
```
1. SCOPE_HIDDEN    — view and not view.visible(edge)     (invisible to principal; 0028 drops it)
   (then e = view.shape(edge) — shaping may demote disclosure before 2-5)
2. NOT_VALID_AT_T  — T not in [valid_from, invalidated_at)   (time validity, OUTERMOST trust-agnostic gate)
3. EXCLUDED        — invalidation_reason == "revoked_source"  (0022 non-revival — strongest; > FENCED)
4. FENCED_AS_OF    — quarantined OR use_only OR (inactive AND reason ∉ GROUNDABLE_AS_OF)
5. GROUNDED_AS_OF  — otherwise (assertable to this principal at T)
```
This resolves d-3's two ambiguities: an edge BOTH `revoked_source` AND
quarantined → `EXCLUDED` (rule 3 before 4, the stronger disposition wins); an
out-of-interval `revoked_source` edge → `NOT_VALID_AT_T` (rule 2 before 3 — time
is the outer gate; the edge is not a candidate at that T regardless). **Safety is
order-independent:** rules 3 and 4 are both non-grounding, so `revoked`/`disputed`/
`corrected`/quarantined/use_only never reach `GROUNDED_AS_OF` under ANY ordering
(V-NEVER holds); the precedence only fixes the reported STATUS. `assertable_as_of`
(the boolean, §4a) is True iff `classify_as_of` returns `GROUNDED_AS_OF`.

### 4b. The reason → historical-truth disposition (closed, total, fail-closed)
| reason | `DISPOSITIONED_REASONS` (current) | 0030 historical-truth | rationale |
|---|---|---|---|
| **superseded** | drop | **GROUNDABLE-as-of-T** | was validly true until it changed (the headline case) |
| **lapsed** | retain | **GROUNDABLE** (flag `stale-at-recall`) | staleness is not falsity — it was our true belief then |
| **decayed** | retain | **GROUNDABLE** (flag `stale-at-recall`) | low-confidence-now is not was-false |
| **absorbed_duplicate** | retain | in the allow-set for TOTALITY, but **UNREACHABLE through §4a** by the shipped empty-interval construction (D-2) | absorption sets `incoming.valid_from = min(incoming, prior)` then invalidates the prior AT that instant (`graph.py:463,478`), so the absorbed edge's half-open interval is EMPTY — step 1 (time validity) always fails first. Kept in `GROUNDABLE_AS_OF` for registry totality; its groundability is asserted UNREACHABLE by test (the 0028 R1-4 closure pattern), not exercised |
| **corrected** | drop | **NEVER** | retroactively false — it was an error, replaced (0028 resolves to the corrector) |
| **disputed** | drop | **NEVER** (FENCED_AS_OF) | the host revoked trust; contested at any T |
| **revoked_source** | drop | **NEVER** (EXCLUDED) | withdrawn evidence — 0022 non-revival; not even fenced |
| **(any unknown 8th)** | drops | **NEVER** (fail-closed) | absent from `GROUNDABLE_AS_OF` allow-set |

### 4c. Scope composition — assertable-to-WHOM at T (0028 R1-5)
`assertable_as_of` is principal-agnostic; the principal-facing form composes with
0020's `ScopeView` (`scope_read.py`), applied to the historical edge the SAME way
recall applies it today:
- `view.visible(edge)` must hold (a cross-hidden historical edge is invisible to
  this principal at every T).
- `view.shape(edge)` is applied FIRST; if shaping demotes the edge
  (MENTIONABLE→USE_ONLY / `derived_from`→THIRD_PARTY) it fails content-trust →
  never grounds for that principal. So "restricted" material (0028 R1-3's list)
  is fenced by scope, per-principal, at any T.
- The successor/interval question composes cleanly because scope is applied per
  edge, not per interval.

### 4d. Rendering channel (informative — 0028 owns the query render)
A `GROUNDED_AS_OF` historical edge is assertable, but it is HISTORY, not the
current value. 0028 v2 renders it in a labelled as-of channel carrying its
resolution provenance (`valid_from`, `invalidated_at`, `invalidation_reason`),
distinct from the current grounded block, so a reader never mistakes a
groundable-as-of historical fact for the current one. 0030 supplies the
classification; the channel is 0028's.

### 4e. Relationship to the current classifier — the two divergence cells (D-1)
`assertable_as_of(edge, now)` and `Edge.assertable` agree for the ordinary edge,
and diverge on exactly two cells where **valid-time and current-ness genuinely
differ**. Both are reachable in the shipped store, and in BOTH `assertable_as_of`
gives the temporally-correct answer. Neither changes the current recall path
(which never calls `assertable_as_of`).

| cell | `Edge.assertable` | `assertable_as_of(now)` | which is right, and why |
|---|---|---|---|
| **future `valid_from`** (`valid_from > now`, active) | True (active) | **False** | as-of is STRICTER and correct — a not-yet-valid fact is not assertable now |
| **future `invalidated_at`** (`valid_from ≤ now < invalidated_at`, groundable reason) | False (`active` is False once `invalidated_at` is set) | **True** | as-of is LESS strict and correct — the value is STILL validly held now; its successor's `valid_from` is in the future (`graph.py:362` sets `prior.invalidated_at = replacement.valid_from`, which is caller-suppliable), so the prior IS the true-now value |

The future-`invalidated_at` cell is the load-bearing one: it shows the current
classifier UNDER-asserts (fences a still-true value merely because `invalidated_at`
is set at all), and `assertable_as_of` corrects that — for the as-of path ONLY.
**Ruling (this spec):** `assertable_as_of` is authoritative on valid-time; both
divergences are intended, tested (§6a adds the future-`invalidated_at` T-position),
and confined to the as-of path. 0030 does NOT change what the current classifier
does with either cell (that is a 0019 question left untouched).

## 5. Regime analysis
- **Active edge, T = now, `valid_from ≤ now < any invalidated_at`:**
  `assertable_as_of == Edge.assertable` (V-CURRENT-UNCHANGED) — 0030 agrees on the
  present.
- **The two divergence cells** (future `valid_from`, future `invalidated_at`):
  see §4e — as-of is the correct one in both, current path unchanged.
- **Historical edge, groundable reason, T in interval:** `GROUNDED_AS_OF` — the
  new capability.
- **Historical edge, never-groundable reason, any T:** `FENCED_AS_OF` /
  `EXCLUDED` — the trust exclusion the whole spec protects.
- **T outside every interval:** `NOT_VALID_AT_T` — truthful gap (0028 handles the
  gap semantics; 0030 just reports it).

## 6. Invariants and executable checks — REQUIRED, blocking

| invariant | executable check | where |
|---|---|---|
| **V-NEVER** never grounds a trust-excluded record at ANY T: for every edge whose reason ∈ {corrected, disputed, revoked_source} OR whose class is quarantined/use_only, `assertable_as_of(edge, T)` is False for all sampled T (incl. inside its interval + boundaries) | `test_never_grounds_excluded_at_any_t` | CI |
| **V-FAILCLOSED** an unknown reason never grounds; `GROUNDABLE_AS_OF` is an allow-set and every `DISPOSITIONED_REASONS` key is explicitly dispositioned (build fails on a new undispositioned reason) | `test_groundable_registry_is_total_and_failclosed` | CI |
| **V-CURRENT-UNCHANGED** `Edge.assertable` is not modified; the current recall path does not call `assertable_as_of` — proven TWO ways (d-4, avoiding a grep-for-absence): a caller-grep AND the current path run against 0027's frozen V10 pre-feature oracle asserting byte-identity. `assertable_as_of(edge, now) == edge.assertable` for the ordinary edge, and diverges on EXACTLY the two §4e cells (future `valid_from` → stricter; future `invalidated_at` → less strict), both asserted as intended | `test_current_path_frozen_oracle_identical` + `test_as_of_now_diverges_only_on_two_cells` | CI |
| **V-INTERVAL** groundable only within the half-open `[valid_from, invalidated_at)`; `T == invalidated_at` is NOT in interval (belongs to the successor); `T < valid_from` and `T ≥ invalidated_at` → not valid | `test_half_open_interval_boundaries` | CI |
| **V-SCOPE** composes with 0020: a shaped-demoted or invisible historical edge never grounds for that principal; an edge groundable-as-of-T unscoped can be fenced for a restricted principal | `test_assertable_as_of_composes_with_scope` | CI |
| **V-STALE** `lapsed`/`decayed` ground but carry a `stale-at-recall` flag | `test_lapsed_decayed_grounded_but_flagged` | CI |
| **V-ADDITIVE** 0030 adds no field to `Edge`; the classifier is a pure function of existing fields + the registry | `test_no_edge_field_added` | CI |

### 6a. Acceptance measurement — REQUIRED, FINITE
A **correctness gate (100%, not a quality metric)** — as 0028's §6a is. A frozen
manifest (portable builder + `--check`, per 0028 R1-7): the CROSS PRODUCT of
- **all seven reasons** (+ one deliberately-unknown "eighth" reason → fail-closed),
- **content classes** {grounded, quarantined, use_only},
- **T positions** {before `valid_from`, at `valid_from`, mid-interval, at
  `invalidated_at` (excluded — successor's), after `invalidated_at`, **plus the
  two §4e divergence cells: future `valid_from` and future `invalidated_at` — the
  now-vs-current-classifier comparison (D-1)**},
- **principal variants** {self/unscoped, in-scope, cross-scope-shaped,
  cross-hidden},
→ each with its expected `classify_as_of` status. Pass = **100% match**. Corpus
frozen + digest recorded in `## Review closure` before implementation.

## 7. Failure modes and reversibility
- **Fully additive / reversible:** 0030 adds a predicate; removing it restores
  today exactly (`Edge.assertable` never changed). No migration, no schema
  change, no data rewrite.
- **New-reason safety:** a producer's new reason fails the totality test until
  dispositioned; until then it fails closed (fences). The registry can only
  narrow what grounds, never widen (internal-R1 discipline).

## 8. Claims and limits
- **Claim:** 0030 lets history be asserted *when and only when* it was validly,
  trustworthily true at T — a strictly-additive trust surface that never relaxes
  a current exclusion and fails closed on the unknown. *Limit:* valid-time only;
  the transaction axis is 0029; the query/resolution/render is 0028 v2.
- **Position:** no surveyed competitor classifies historical assertability by a
  reason-carrying, fail-closed registry — the field's as-of (where it exists) is
  interval math with no trust axis (0028 design §5). This is the trust-native
  piece Quentin prioritised (0030-first) precisely because it is the part no one
  else can copy.

## 9. Brief for the external reviewer
Attack hardest:
1. **The fail-closed derivation.** Is `GROUNDABLE_AS_OF` genuinely airtight —
   can any path (a new reason, a `None` reason on an inactive edge, a race
   between `invalidated_at` and `invalidation_reason` being set) let a
   non-allow-set edge ground? The registry-totality test is the guard; break it.
2. **Decoupling assertable from active.** Does removing the `active` requirement
   open ANY laundering path for corrected/disputed/revoked/quarantined/use_only
   at some T (especially at interval boundaries, or for an edge that is both
   historical AND quarantined)?
3. **Scope composition (R1-5).** Can a cross-scope historical edge ground for the
   wrong principal — does applying `shape()` before content-trust actually fence
   restricted material at every T, and does an edge shaped-demoted for principal
   A but native for B classify correctly for each?
4. **The 0030/0028/0029 boundary.** Is "0030 classifies, 0028 resolves, 0029
   carries transaction time" a clean cut, or does classification secretly need
   resolution (e.g. does classifying an `absorbed_duplicate` groundable require
   knowing the absorber exists)?

## 10. Open questions
- **`disputed` at T — fenced vs excluded.** 0030 classes it `FENCED_AS_OF`
  (rendered, never asserted); 0028 R1-3 leaned "fence-and-return". `revoked_source`
  is stronger (`EXCLUDED`, not even fenced — 0022 non-revival). Confirm the
  fenced/excluded boundary with the gate-owner (the disputed→non-assertable
  ruling that 0028 also carries).
- ~~**`absorbed_duplicate` classification vs resolution.**~~ RETIRED (D-2): moot
  by the shipped empty-interval construction — the absorbed edge's interval is
  empty, so time-validity fails first and the groundable row is unreachable. Kept
  in the allow-set for totality, asserted unreachable by test (§4b).
- **Boundary instant `T == invalidated_at`.** Half-open interval excludes it
  (successor's). Confirm this matches 0003's supersession boundary exactly (no
  gap, no overlap).

## Review closure
*n/a — draft; the frozen §6a manifest digest + the registry-totality evidence
land here before `accepted`. Entry into external review on Quentin's word.*
