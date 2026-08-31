# Feature spec: time-relative trust classification

Spec-Status: draft

*Candidate authored by research (veracium-research), 2026-08-31. The first of
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
| **Author / session** | research (veracium-research); adopted by dev (v2/v4 2026-08-31; v5 symbol correction at pre-dispatch) |
| **Version** | **v4** — dev v3-re-read minors folded (m-1 inverted-vs-empty interval in rule 0; m-2 `now` made load-bearing for stale-at-recall). v3 — pre-review folded (7 findings): (1) scope via time-relative verdict not `shape()`; (2) state-coherence rule 0 / MALFORMED; (3) total `AS_OF_DISPOSITION` dict not allow-set; (4) absorbed groundable, not "unreachable"; (5) `Result{status,flags}` + `now`; (6) §6a state-families not naive product; (7) baseline pinned post-0027 + UTC-aware datetimes. (v2 folded dev's D-1/D-2/d-3/d-4.) |
| **Status** | *canonical state is the `Spec-Status:` line above* |
| **Internal reviewers** | research (author) · dev (reviewer, roles inverted from 0027) |
| **External review** | REQUIRED — new trust surface; touches classification. Entry on Quentin's word |
| **Decision + date** | — |
| **Path** | full |

### Spec-Requires (accepted specs this consumes)
- **0019 / 0023 / 0026 / 0027** — the current trust classes and the render-time
  classifier. **The render-time classifier is `history_label` (`graph.py:270`)**
  — NOT `_render_class`, which was a spec-only fiction (finding 7): it exists in
  no code at any commit; the shipped function returning
  RETIRED_HISTORY/QUARANTINED_CLAIM/CONTESTED_CURRENT/UNVERIFIED_CURRENT/
  GROUNDED_CURRENT is `history_label`. **BASELINE PIN:** 0030 is built on top of
  ACCEPTED 0027, so its baseline is the **post-0027 implementation commit** — not
  because of any render-classifier symbol (`history_label` exists at every
  commit) but because 0030's V-CURRENT-UNCHANGED test reuses **0027's v10
  oracle** (`specs/evidence/0027/v10_oracle/`, post-0027) and 0030 composes with
  0027's accepted recall. Dev pins that commit at adoption; all §Spec-Requires/§6
  citations (`Edge.assertable schema.py:501`, `history_label graph.py:270`,
  `gate.scoped_assertable`, `ScopeView.decision`) are grep-verified against THAT
  commit (pre-dispatch caught `_render_class` failing exactly that grep).
  **UNCHANGED** by 0030: it adds a PARALLEL time-relative classifier, does not
  modify `Edge.assertable` (additive discipline, 0027).
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
  principals to whom it is assertable — composed via `gate.scoped_assertable` on
  the TIME-RELATIVE verdict, NOT `shape()` (finding 1; §4c). 0020 owns read visibility (0028 R1-5 corrected the
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
0030 **decouples** the two: it adds `classify_as_of(edge, T, now, view)` — "was this edge validly,
trustworthily true at T," a `Result{status, flags}` (§4a) keeping every trust exclusion intact.
This is the substrate 0028 v2 needs to return an ASSERTABLE historical answer
rather than a fenced one.

**Why this is delicate (the new trust surface Quentin ruled we build, not
dodge).** Decoupling assertability from `active` means a historical edge can now
ground. Done wrong, that is a laundering path: a `corrected` error, a `disputed`
claim, or `revoked_source` content could ground at some T. The whole spec is the
discipline that this CANNOT happen — a registry-derived, fail-closed total disposition mapping
plus the time-invariant content-trust exclusions plus the scope composition.

## 2. Field contracts touched

`grep -rn` at author time (dev re-runs at implementation):

| field | read / written | contract | preserves? |
|---|---|---|---|
| `Edge.assertable` (`schema.py:501`) | READ, **UNCHANGED** | the current classifier | YES — 0030 adds a parallel predicate; current path byte-identical (V-CURRENT-UNCHANGED) |
| `Edge.invalidation_reason` / `valid_from` / `invalidated_at` (`schema.py:430-432`) | READ | the reason + valid-time interval 0030 keys on | YES — read-only |
| `DISPOSITIONED_REASONS` (`schema.py:407`) | READ + a PARALLEL disposition added | the authoritative reason registry | YES — 0030 adds `AS_OF_DISPOSITION` (total dict), key-equal to the same set, fail-closed |
| NEW `classify_as_of(edge, T, now, view=None) -> Result` (+ boolean `assertable_as_of`) | WRITTEN | the time-relative classifier primitive | additive |
| `ScopeView` (`scope_read.py:280`) | READ | composes for "assertable-to-whom at T" | YES — reuses the shipped lens |

### 2a. The `AS_OF_DISPOSITION` total mapping (derived, fail-closed)
0030 adds a **TOTAL disposition mapping** keyed on the SAME reasons as
`DISPOSITIONED_REASONS` — NOT an allow-set (round-1 finding 3). An allow-set
records only positive dispositions, so it cannot distinguish "deliberately never
groundable" from "forgotten when a new reason was added": adding an eighth
`DISPOSITIONED_REASONS` key would silently default to fenced, safe at runtime but
never forcing the author to rule it. A total dict + exact-key-equality FAILS THE
BUILD on any undispositioned reason (the discipline `DISPOSITIONED_REASONS`
itself uses, not the `WIKI_RETAINING` allow-set):
```
AS_OF_DISPOSITION: dict[str, str] = {   # every DISPOSITIONED_REASONS key, explicitly
    "superseded":         GROUNDABLE,   # was validly true until it changed
    "lapsed":             GROUNDABLE,   # staleness is not falsity
    "decayed":            GROUNDABLE,   # low-confidence-now is not was-false
    "absorbed_duplicate": GROUNDABLE,   # was true; 0028 resolves to the absorber (finding 4)
    "corrected":          FENCED,       # retroactively false
    "disputed":           FENCED,       # trust revoked / contested at any T
    "revoked_source":     EXCLUDED,     # withdrawn — 0022 non-revival, not even fenced
}
# Build gate: assert set(AS_OF_DISPOSITION) == set(DISPOSITIONED_REASONS) exactly
# (like W5) — a new reason in either registry fails until dispositioned in BOTH.
# Runtime lookup DEFAULTS an unknown/missing key to FENCED (fail-closed), so even
# a registry drift can only fence, never ground.
GROUNDABLE / FENCED / EXCLUDED are the three closed dispositions.
```
**`AS_OF_DISPOSITION`'s GROUNDABLE set is deliberately NOT `WIKI_RETAINING`.**
They answer different questions: `WIKI_RETAINING` = {lapsed, decayed,
absorbed_duplicate} is "does the CURRENT view survive this invalidation"; the
GROUNDABLE reasons in `AS_OF_DISPOSITION` add **`superseded`** because "was it
validly TRUE at T" is a different test — a superseded fact was true until it
changed, so it must NOT survive in the current wiki (the value moved on) yet MUST
be groundable as-of a T inside its interval. That asymmetry (`superseded`:
wiki-drop but as-of-groundable) is the whole reason 0030 needs its own mapping
rather than reusing `WIKI_RETAINING`.

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant** |
|---|---|---|---|---|---|
| the query time `T` and eval time `now` | `None T` → caller error (the as-of layer supplies T) | non-datetime → typed refuse; **naive/aware mismatch → normalise to UTC-aware BEFORE compare** (finding 7 — "any datetime valid" was false; a naive-vs-aware `<` raises). `T`,`now`,`valid_from`,`invalidated_at` are all coerced UTC-aware | timezone crafted to skew an interval boundary | **V-INTERVAL** — UTC-aware comparison only |
| the edge's `invalidation_reason` | `None` on an INACTIVE edge → MALFORMED (finding 2); `None` on active → the well-formed active case | non-str → MALFORMED (fenced) | eighth/unknown reason → `FENCED` (default) | a producer emitting a novel reason to ground history | **V-FAILCLOSED** — `AS_OF_DISPOSITION` total dict, default `FENCED` |
| the **edge STATE** (`invalidated_at` × `invalidation_reason` × interval) | — | active+non-`None` reason; inactive+`None` reason; inverted interval (`invalidated_at < valid_from`) — all reachable via `add_edge` (schema does not couple the fields) | — | a crafted incoherent edge to reach the grounding branch | **V-MALFORMED** — state-coherence rule 0 refuses every incoherent shape BEFORE any grounding branch; never grounds |
| the principal | `None` → unscoped (self) | via 0020 | — | a principal querying another's restricted history | **V-SCOPE** — composes via the time-relative verdict through `gate.scoped_assertable`, NOT `view.shape()` (finding 1) |

### 2c-ii. Assertions about reach — REQUIRED

| claim | invariant |
|---|---|
| "0030 never makes `corrected`/`disputed`/`revoked_source`/`quarantined`/`use_only` groundable at ANY T" | **V-NEVER** |
| "an unknown/eighth reason can never ground" | **V-FAILCLOSED** (total dict, `set(AS_OF_DISPOSITION)==set(DISPOSITIONED_REASONS)`, default FENCED) |
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
| **historical truth** | coherent-active → yes; else `AS_OF_DISPOSITION[reason] == GROUNDABLE` (default FENCED) | NO — a `corrected`/`disputed`/`revoked_source` edge is never-groundable at every T |
| **scope** (with principal) | `ScopeView` assertable-to-principal + `shape()` | per-principal |

**Load-bearing statement:** 0030 lets an edge be assertable-as-of-T ONLY when it
was BOTH validly-held at T (time + a groundable reason) AND is trustworthy
content (not quarantined/use_only) AND assertable to the principal. It never
relaxes a trust exclusion; it only removes the *current-ness* requirement, and
only for reasons that mean "was validly true then."

## 4. Behaviour

### 4a. The classifier — exact
`classify_as_of(edge, T, now, view=None) -> Result` is the single source of
truth; `Result = {status, flags}` (finding 5) with `status` a closed enum and
`flags` a set (e.g. `stale-at-recall`). `now` is the evaluation instant, DISTINCT
from the query time `T` — the future-`invalidated_at` cell makes the distinction
observable (§4e), and `stale-at-recall` is defined against `now`. The rules apply
in this precedence (first match wins):
```
def classify_as_of(edge, T, now, view=None) -> Result:
    # 0. STATE COHERENCE — fail-closed BEFORE any grounding branch (finding 2)
    coherent_active   = edge.invalidated_at is None and edge.invalidation_reason is None
    coherent_inactive = (edge.invalidated_at is not None
                         and edge.invalidation_reason in AS_OF_DISPOSITION
                         and edge.valid_from <= edge.invalidated_at)   # m-1: reject INVERTED (<);
                                                                        # EMPTY (==, canonical absorption) is coherent
    if not (coherent_active or coherent_inactive):
        return MALFORMED           # active+reason, inactive+no-reason, non-str/unknown reason,
                                   # INVERTED interval (invalidated_at < valid_from). An EMPTY interval
                                   # (invalidated_at == valid_from) is NOT malformed — it is coherent and
                                   # falls to NOT_VALID_AT_T at rule 2 (no T in a half-open empty interval)
    # 1. SCOPE — via the TIME-RELATIVE verdict, NOT view.shape() (finding 1)
    if view is not None and not view.visible(edge):
        return SCOPE_HIDDEN
    # 2. TIME VALIDITY (half-open [valid_from, invalidated_at))
    if not (edge.valid_from <= T and (edge.invalidated_at is None or T < edge.invalidated_at)):
        return NOT_VALID_AT_T
    # 3. EXCLUDED — strongest disposition (0022 non-revival)
    if edge.invalidation_reason == "revoked_source":         # (coherence guarantees inactive here)
        return EXCLUDED
    # 4. CONTENT TRUST + reason disposition — the base "would this ground" verdict
    base_groundable = (not edge.quarantined and not edge.use_only
                       and (coherent_active
                            or AS_OF_DISPOSITION.get(edge.invalidation_reason, FENCED) == GROUNDABLE))
    # 5. SCOPE SHAPING on the TIME-RELATIVE verdict (finding 1) — NOT view.shape(),
    #    which short-circuits on today's `assertable` and so never demotes a
    #    historical edge. Feed the as-of verdict through the gate's scoped relation:
    scoped = base_groundable and (view is None
                                  or gate.scoped_assertable(base_groundable, view.decision(edge)))
    if not scoped:
        return FENCED_AS_OF        # not-groundable, or cross-scope-restricted for THIS principal
    # m-2: `now` is load-bearing here — stale-at-recall means "already stale AS OF now".
    # A lapsed/decayed edge whose invalidated_at is in the FUTURE (invalidated_at > now,
    # the §4e future-invalidated cell) is still valid at now and NOT yet stale; keying on
    # reason alone would flag it prematurely.
    already_stale = (edge.invalidation_reason in ("lapsed", "decayed")
                     and edge.invalidated_at is not None and edge.invalidated_at <= now)
    flags = {"stale-at-recall"} if already_stale else set()
    return Result(GROUNDED_AS_OF, flags)

def assertable_as_of(edge, T, now, view=None) -> bool:   # convenience boolean
    return classify_as_of(edge, T, now, view).status == GROUNDED_AS_OF
```
Three structural corrections from round 1:
- **State coherence is rule 0** (finding 2). `active` is derived solely from
  `invalidated_at is None`; the schema does NOT couple it to `invalidation_reason`
  (`schema.py:479` vs `:432`, no validator), so `add_edge` can persist an ACTIVE
  edge carrying `reason="corrected"`. The old active-branch shortcut (`if
  invalidated_at is None: return True`) would have grounded it. Rule 0 refuses
  every incoherent shape (active+reason, inactive+no-reason, non-string/unknown
  reason, inverted interval) as `MALFORMED` — never grounded.
- **Scope uses the TIME-RELATIVE verdict** (finding 1), fed through
  `gate.scoped_assertable(base_groundable, view.decision(edge))`. v2 called
  `view.shape()`, which first checks today's `record.assertable` — False for
  every historical edge — and returns it UNCHANGED, so a cross-scope
  `superseded` edge kept `MENTIONABLE` and grounded. The as-of verdict must go
  through the scoped relation directly (or a shaping method that accepts it), not
  the shipped `shape()`.
- **`classify_as_of` is authoritative; `assertable_as_of` is derived from it**
  (finding 2), so the two can never disagree — an active `revoked_source` edge is
  `MALFORMED` (rule 0), so both return non-grounded consistently.

**Safety is order-independent:** rules 0/3/`FENCED_AS_OF` are all non-grounding,
so `MALFORMED`/`revoked`/`disputed`/`corrected`/quarantined/use_only/restricted
never reach `GROUNDED_AS_OF` under any ordering (V-NEVER); precedence only fixes
the reported status.

### 4b. The reason → historical-truth disposition (closed, total, fail-closed)
| reason | `DISPOSITIONED_REASONS` (current) | 0030 historical-truth | rationale |
|---|---|---|---|
| **superseded** | drop | **GROUNDABLE-as-of-T** | was validly true until it changed (the headline case) |
| **lapsed** | retain | **GROUNDABLE** (flag `stale-at-recall`) | staleness is not falsity — it was our true belief then |
| **decayed** | retain | **GROUNDABLE** (flag `stale-at-recall`) | low-confidence-now is not was-false |
| **absorbed_duplicate** | retain | **GROUNDABLE** (0028 resolves to the absorber) | was a true value. CANONICAL absorption yields an empty interval (`graph.py:463,478` — `invalidated_at = min(incoming,prior) ≤ valid_from`), so those never reach the disposition (time-validity fails first). But the GENERIC invalidation/insertion paths can persist a NON-empty interval carrying `absorbed_duplicate` (finding 4), and a classifier seeing only an `Edge` cannot prove canonicity — so it must NOT rely on unreachability. It classes GROUNDABLE (the value was true at T) and lets 0028 resolve to the absorber; §6a exercises the non-empty-interval case, not an unreachable assertion (v2's D-2 over-generalized from canonical-only) |
| **corrected** | drop | **NEVER** | retroactively false — it was an error, replaced (0028 resolves to the corrector) |
| **disputed** | drop | **NEVER** (FENCED_AS_OF) | the host revoked trust; contested at any T |
| **revoked_source** | drop | **NEVER** (EXCLUDED) | withdrawn evidence — 0022 non-revival; not even fenced |
| **(any unknown 8th)** | drops | **NEVER** (fail-closed) | defaults to FENCED in the total `AS_OF_DISPOSITION` (missing key) |

### 4c. Scope composition — assertable-to-WHOM at T (0028 R1-5, finding 1)
`assertable_as_of` is principal-agnostic; the principal-facing form composes with
0020's `ScopeView` (`scope_read.py`) — but **NOT via the shipped `view.shape()`**.
`shape()` short-circuits on today's assertability (`_asserted_today(record) =
bool(record.assertable)`, `scope_read.py:58,381`), which is False for EVERY
historical (inactive) edge, so `shape()` returns a historical edge UNCHANGED and
never demotes it. v2 relied on that demotion; it does not happen. A cross-scope
`superseded` edge would keep `MENTIONABLE` and ground — V-SCOPE false.
- **Correct composition:** feed the TIME-RELATIVE base verdict through the gate's
  scoped relation — `gate.scoped_assertable(base_groundable, view.decision(edge))`
  (§4a rule 5). The `view.decision(edge)` cell (CROSS_VISIBLE etc.) is the same
  authority `shape()` consults; passing it the AS-OF verdict instead of today's
  gives the correct per-principal answer for historical material.
- Equivalently, 0030 may add a `shape_as_of(edge, verdict)` that carries the
  restrict-only demotion onto a historical edge given its time-relative verdict —
  a small addition to 0020's surface — but calling the existing `shape()` is
  insufficient.
- `view.visible(edge)` still gates first (a cross-hidden historical edge is
  `SCOPE_HIDDEN` at every T). Scope is applied per edge, not per interval.

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
| **V-NEVER** never grounds a trust-excluded record at ANY T: for every edge whose reason ∈ {corrected, disputed, revoked_source} OR class ∈ {quarantined, use_only}, `classify_as_of` never returns `GROUNDED_AS_OF` for any sampled T (incl. inside the interval + boundaries) | `test_never_grounds_excluded_at_any_t` | CI |
| **V-MALFORMED** (finding 2) state-coherence rule 0 fires first: an ACTIVE edge carrying a non-`None` reason, an INACTIVE edge with `None` reason, a non-string/unknown reason, or an INVERTED interval (invalidated_at < valid_from) → `MALFORMED` (an EMPTY interval == is coherent, → NOT_VALID_AT_T) — never grounded either way — asserted with edges built directly via `add_edge` (which does not couple `invalidated_at`/`invalidation_reason`) | `test_incoherent_states_are_malformed_never_grounded` | CI |
| **V-FAILCLOSED** (finding 3) `AS_OF_DISPOSITION` is a TOTAL dict; `set(AS_OF_DISPOSITION) == set(DISPOSITIONED_REASONS)` exactly (build fails on any undispositioned reason in EITHER); runtime defaults an unknown/missing key to `FENCED` | `test_as_of_disposition_is_total_and_failclosed` | CI |
| **V-CURRENT-UNCHANGED** (finding 7) `Edge.assertable` is not modified; the current recall path does not call the as-of classifier — proven via a caller-grep AND the current path run against the **post-0027** frozen classification oracle (the baseline is pinned to the post-0027 implementation commit, §Spec-Requires — NOT `d7bf16b`, which predates 0027's v10 oracle). `classify_as_of(...,now).status==GROUNDED_AS_OF` agrees with `edge.assertable` for the ordinary edge and diverges on EXACTLY the two §4e state cells | `test_current_path_oracle_identical_post0027` + `test_as_of_now_diverges_only_on_two_cells` | CI |
| **V-INTERVAL** groundable only within the half-open `[valid_from, invalidated_at)`; `T == invalidated_at` excluded (successor's); UTC-aware comparison only (§10) | `test_half_open_interval_boundaries` | CI |
| **V-SCOPE** (finding 1) composes with 0020 via the TIME-RELATIVE verdict through `gate.scoped_assertable(base_groundable, view.decision(edge))` — NOT `view.shape()` (which returns a historical edge unchanged). Fixture: a cross-scope-visible `superseded` edge groundable unscoped is `FENCED_AS_OF` for the restricted principal; a same-scope one still grounds | `test_scope_composes_via_time_relative_verdict_not_shape` | CI |
| **V-STALE** (finding 5, m-2) `classify_as_of` returns `Result{status, flags}`; `stale-at-recall` is set iff reason ∈ {lapsed,decayed} AND `invalidated_at <= now` (already stale) — a future-lapsing edge (invalidated_at > now) grounds WITHOUT the flag; `now` is thereby load-bearing (an external reviewer greps for the unread param) | `test_result_carries_stale_flag` | CI |
| **V-ADDITIVE** 0030 adds no field to `Edge`; the classifier is a pure function of existing edge fields + the registry + `(T, now, view)` | `test_no_edge_field_added` | CI |

### 6a. Acceptance measurement — REQUIRED, FINITE
A **correctness gate (100%, not a quality metric)** — as 0028's §6a is. NOT a
naive Cartesian product (finding 6): a product omits well-formed active
(`reason=None`), and crossing every reason with the future-time cells makes
incoherent/non-divergent cases (the two divergence cells are STATE SHAPES, not
extra `T` positions). Instead, explicit **STATE FAMILIES**, each × a **T-position
sweep** {before, at `valid_from`, mid-interval, at `invalidated_at` (excluded),
after} × a **principal sweep** {self/unscoped, in-scope, cross-scope-visible,
cross-hidden}, with the expected `Result{status, flags}`:
1. **well-formed active** (`invalidated_at=None`, `reason=None`) — the ordinary
   present case (was omitted);
2. **well-formed inactive**, one family per reason (all seven), content classes
   {grounded, quarantined, use_only};
3. the **two future-time divergence states** — future `valid_from`, future
   `invalidated_at` — as the now-vs-current comparison (needs `now` distinct from
   `T`);
4. **incoherent states** (V-MALFORMED): active+reason, inactive+no-reason,
   non-string reason, unknown "eighth" reason, empty interval, inverted interval;
5. **scoped variants** over families 1-3 (esp. the finding-1 cross-scope
   `superseded` case: grounds unscoped, `FENCED_AS_OF` for the restricted
   principal);
6. **`lapsed`/`decayed`** asserting the `stale-at-recall` flag against `now`.
Pass = **100% match**. Corpus frozen + portable builder (`--check`) + digest
recorded in `## Review closure` before implementation (0028 R1-6/R1-7 pattern).

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
1. **The fail-closed derivation.** Is `AS_OF_DISPOSITION` (total dict + key-equality) genuinely airtight —
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
