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
| **Author / session** | research (veracium-research); adopted by dev (v2/v4/v5 2026-08-31; v7 = the joint round-1 fold, this adoption the pair's shared baseline) |
| **Version** | **v7** — dev v6 both-check folded: **B-1** normalization extended to the `current` leg (unhashable reason reaching `dict.get`; `current.invalidated_at` normalized outside the guard) and **B-2** structural coherence applied to `current` (the cap must never read an incoherent state). Both are the mechanical completion of the F6/F2 folds onto the second parameter F2 introduced. v6 — joint round-1 findings folded: **F2** two-state (`snapshot` vs `current`, held_at_K vs assertable-now, current caps never time-travel) + the reason×cutoff matrix (§4a-ii); **F6** type/UTC normalization before any membership or comparison, unknown reason ruled FENCED (not MALFORMED); **F7** visibility is the OUTERMOST gate (hidden never leaks MALFORMED); **F8** carrier sweep. v4 — dev v3-re-read minors folded (m-1 inverted-vs-empty interval in rule 0; m-2 `now` made load-bearing for stale-at-recall). v3 — pre-review folded (7 findings): (1) scope via time-relative verdict not `shape()`; (2) state-coherence rule 0 / MALFORMED; (3) total `AS_OF_DISPOSITION` dict not allow-set; (4) absorbed groundable, not "unreachable"; (5) `Result{status,flags}` + `now`; (6) §6a state-families not naive product; (7) baseline pinned post-0027 + UTC-aware datetimes. (v2 folded dev's D-1/D-2/d-3/d-4.) |
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
0030 **decouples** the two: it adds
`classify_as_of(snapshot, current, T, now, view)` — "was this edge validly,
trustworthily true at T, and may it be asserted now" — returning
`Result{status, held_at_K, flags}` (§4a) and keeping every trust exclusion intact.
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
| NEW `classify_as_of(snapshot, current, T, now, view=None) -> Result{status, held_at_K, flags}` (+ boolean `assertable_as_of`) | WRITTEN | the time-relative classifier primitive | additive |
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
| **historical truth (`held_at_K`)** | from the SNAPSHOT only: coherent-active → yes; else `AS_OF_DISPOSITION[reason] == GROUNDABLE` (default FENCED) | NO — fixed by the snapshot's reason |
| **current caps (F2)** | from the CURRENT row: revocation → `EXCLUDED`; current corrected/disputed/quarantined/use_only → `FENCED_AS_OF`. Subtract-only; never grants | per-`now`, never time-travelled |
| **scope** (with principal) | CURRENT `ScopeView`: `visible()` as the OUTERMOST gate (F7), then `gate.scoped_assertable` on the TIME-RELATIVE verdict — **never the shipped `shape()`** (F8.1; it short-circuits on today's `assertable` and so never demotes history). Current scope always governs; 0029 does not version scope policy or membership (§4a) | per-principal, never time-travelled |

**Load-bearing statement:** 0030 lets an edge be assertable-as-of-T ONLY when it
was BOTH validly-held at T (time + a groundable reason) AND is trustworthy
content (not quarantined/use_only) AND assertable to the principal. It never
relaxes a trust exclusion; it only removes the *current-ness* requirement, and
only for reasons that mean "was validly true then."

## 4. Behaviour

### 4a. The classifier — exact (TWO-STATE, round-1 F2)

**A single `Edge` cannot carry the question** (F2). Answering "was this
assertable at T, given knowledge cutoff K" needs three distinct inputs, and
conflating them is what round 1 broke:

| input | what it is | who supplies it |
|---|---|---|
| **`snapshot`** | the edge's state AT the knowledge cutoff K | 0029's full-state journal (F1) — or the live edge when no K is given |
| **`current`** | the edge's state NOW (reason, quarantine, use_only) | the live store — used ONLY to SUBTRACT (an outer cap), never to grant |
| **`view`** | CURRENT principal visibility/shaping | 0020 `ScopeView` — **current scope always governs** (see below) |

**Why current scope always governs:** 0029 versions edge state, **not** scope
policy or membership evidence — so historical scope is not reconstructable, and
inventing one would be a guess about who could see what. The only sound rule is
that *today's* boundary gates every answer, including historical ones. This is
also the safe direction: scope can only narrow what a principal sees.

**Two verdicts, not one** (the F2 ruling):
- **`held_at_K`** — *"the store held this belief at K."* A historical fact about
  our own knowledge. Computed from `snapshot` ALONE.
- **`status`** — *"may this be asserted as fact NOW."* `held_at_K` AND the
  current caps allow it.

A record corrected/disputed/revoked **after** K is therefore
`held_at_K=True, status=FENCED_AS_OF` (or `EXCLUDED`) — we honestly report that
we believed it then, and equally honestly refuse to assert it now. Current
restrictions **never time-travel away**; 0022 non-revival in particular is
absolute.

```
def classify_as_of(snapshot, current, T, now, view=None) -> Result:
    # 1. VISIBILITY — the OUTERMOST principal-facing gate (F7).
    #    Nothing about a hidden record leaks — not its existence, not that it is
    #    malformed. `held_at_K` is withheld too. (v4 ran coherence first, so a
    #    hidden+malformed edge returned MALFORMED and leaked its condition.)
    if view is not None and not view.visible(current):
        return Result(SCOPE_HIDDEN, held_at_K=None)

    # 2. NORMALIZE — BOTH legs' types and datetimes, BEFORE any membership or
    #    comparison (F6, extended to `current` by B-1). F2 doubled the input
    #    surface; the normalization discipline has to follow BOTH parameters or
    #    the second one reintroduces the exact failure the first one fixed.
    for st in (snapshot, current):
        r = st.invalidation_reason
        if r is not None and not isinstance(r, str):
            return Result(MALFORMED, held_at_K=None)   # type FIRST: an unhashable value
                                                       # must never reach `in` / dict.get
    try:
        T, now = as_utc(T), as_utc(now)
        s_vf, s_ia = as_utc(snapshot.valid_from), as_utc(snapshot.invalidated_at)
        c_vf, c_ia = as_utc(current.valid_from), as_utc(current.invalidated_at)
    except (TypeError, ValueError):
        return Result(MALFORMED, held_at_K=None)   # naive/aware or non-datetime, EITHER leg
    # as_utc: tz-aware -> UTC; naive -> assumed UTC then made aware; None -> None.
    # Nothing below compares or hashes an unnormalized value from EITHER state.
    reason = snapshot.invalidation_reason

    # 3. STATE COHERENCE — STRUCTURE ONLY (F6), applied to BOTH legs (B-2).
    #    Recognition of the reason is NOT a coherence test; an unknown-but-
    #    well-formed reason is handled at rule 5/6.
    def _coherent(ia, r, vf) -> bool:
        if ia is None:
            return r is None            # active must carry NO reason
        return r is not None and vf <= ia   # inactive: reason + non-inverted interval
    if not (_coherent(s_ia, reason, s_vf)
            and _coherent(c_ia, current.invalidation_reason, c_vf)):
        return Result(MALFORMED, held_at_K=None)
    # B-2: the CAP must never read an incoherent state. Without the second test an
    # ACTIVE current carrying reason="revoked_source" EXCLUDED at rule 6, while the
    # same shape carrying "corrected" sailed past (invalidated_at is None short-
    # circuits current_ok) — two incoherent shapes, two outcomes, neither deliberate.
    # EMPTY interval (ia == vf) stays coherent -> NOT_VALID_AT_T at rule 4.

    # 4. TIME VALIDITY at T, over the SNAPSHOT's interval (half-open [vf, ia))
    if not (s_vf <= T and (s_ia is None or T < s_ia)):
        return Result(NOT_VALID_AT_T, held_at_K=False)

    # 5. HELD AT K — snapshot only. Unknown reason DEFAULTS to FENCED here
    #    (reachable, per F6's ruling), never MALFORMED.
    held = (True if s_ia is None
            else AS_OF_DISPOSITION.get(reason, FENCED) == GROUNDABLE)
    held = held and not snapshot.quarantined and not snapshot.use_only

    # 6. CURRENT CAPS — subtract only, never grant (F2).
    if current.invalidation_reason == "revoked_source":
        return Result(EXCLUDED, held_at_K=held)    # 0022 non-revival: absolute, any K
    current_ok = (not current.quarantined and not current.use_only
                  and (c_ia is None                      # normalized (B-1)
                       or AS_OF_DISPOSITION.get(current.invalidation_reason,
                                                FENCED) == GROUNDABLE))
    if not (held and current_ok):
        return Result(FENCED_AS_OF, held_at_K=held)

    # 7. CURRENT SCOPE SHAPING — on the TIME-RELATIVE verdict, NOT view.shape()
    #    (which short-circuits on today's `assertable` and never demotes history).
    if view is not None and not gate.scoped_assertable(True, view.decision(current)):
        return Result(FENCED_AS_OF, held_at_K=held)

    # stale-at-recall reads `now` (already stale, not future-lapsing) and reads
    # CURRENT — staleness is a property of today, not of K.
    already_stale = (current.invalidation_reason in ("lapsed", "decayed")
                     and c_ia is not None and c_ia <= now)   # B-1: c_ia normalized at
                                                             # rule 2, not at this line
    return Result(GROUNDED_AS_OF, held_at_K=True,
                  flags={"stale-at-recall"} if already_stale else set())

def assertable_as_of(snapshot, current, T, now, view=None) -> bool:
    return classify_as_of(snapshot, current, T, now, view).status == GROUNDED_AS_OF
```
**No-K degenerate case:** with no knowledge cutoff (a pure valid-time query),
`snapshot is current` and the two-state collapses to a single-state
classification — the v4 behaviour, preserved.

### 4a-ii. The reason × cutoff matrix (F2's required ruling)

The axis that matters is **when the invalidation was RECORDED relative to K** —
because that decides whether it is in the `snapshot` (and so shapes what we
*believed at K*) or only in `current` (and so acts purely as a cap on what we
may assert *now*). `T` must lie in the snapshot's interval throughout, else
`NOT_VALID_AT_T`.

| reason | recorded BEFORE K → in `snapshot` | recorded AFTER K → only in `current` |
|---|---|---|
| **superseded** | `held=True` → **GROUNDED** (it was the held value at T) | `held=True`; cap allows → **GROUNDED** |
| **lapsed / decayed** | `held=True` → **GROUNDED** | `held=True`; cap allows → **GROUNDED** + `stale-at-recall` if already lapsed at `now` |
| **absorbed_duplicate** | `held=True` → **GROUNDED** (0028 resolves to the absorber) | `held=True`; cap allows → **GROUNDED** |
| **corrected** | `held=False` (at K we already knew it was an error) → **FENCED_AS_OF** | **`held=True`, status=FENCED_AS_OF** — *the F2 headline case*: we honestly believed it at K, and equally honestly refuse to assert it now |
| **disputed** | `held=False` → **FENCED_AS_OF** | `held=True`, status **FENCED_AS_OF** |
| **revoked_source** | `held=False` → **EXCLUDED** | `held=True`, status **EXCLUDED** — 0022 non-revival is absolute and never time-travels away |
| **unknown / 8th** | `held=False` (default FENCED, F6) → **FENCED_AS_OF** | `held=True`; cap defaults FENCED → **FENCED_AS_OF** |

**The asymmetry is the point.** `corrected`/`disputed`/`revoked_source` recorded
*before* K mean we already knew better at K (`held=False`); recorded *after* K
they leave `held=True` but cap the present. Reporting both truthfully is exactly
what "separate the store held this belief at K from this may be asserted as fact
now" requires — and it is why one boolean could never carry it.

*(This matrix supplies joint acceptance scenarios 2 — revocation→reinstatement
with K between — and 7 — a later correction/dispute/revocation applied to an
earlier snapshot.)*
Three structural corrections from round 1:
- **State coherence is rule 0** (finding 2). `active` is derived solely from
  `invalidated_at is None`; the schema does NOT couple it to `invalidation_reason`
  (`schema.py:479` vs `:432`, no validator), so `add_edge` can persist an ACTIVE
  edge carrying `reason="corrected"`. The old active-branch shortcut (`if
  invalidated_at is None: return True`) would have grounded it. Rule 0 refuses
  every incoherent shape (active+reason, inactive+no-reason, non-STRING
  reason — an unknown STRING reason is not malformed, it fences (F6), inverted interval) as `MALFORMED` — never grounded.
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
`classify_as_of` takes `view` directly (F8.6 — v4 called it "principal-agnostic" while its own signature accepted a view). Scope composes with
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
| **V-MALFORMED** (finding 2, F6, **B-2**) STRUCTURE only, applied to **BOTH** `snapshot` AND `current` — the cap must never read an incoherent state (v6 checked only the snapshot, so an ACTIVE current carrying `revoked_source` EXCLUDED at rule 6 while the same shape carrying `corrected` sailed past the cap: two incoherent shapes, two outcomes, neither deliberate): an ACTIVE edge with a non-`None` reason, an INACTIVE edge with `None` reason, a **non-STRING** reason (type-checked BEFORE any membership test — an unhashable value must never reach `in`), or an INVERTED interval (`invalidated_at < valid_from`) → `MALFORMED`. An **unknown-but-string** reason is NOT malformed → `FENCED` (F6's ruling; the default lookup is reachable). An EMPTY interval (`==`) is coherent → `NOT_VALID_AT_T`. Asserted with edges built via `add_edge` (which does not couple the fields) | `test_incoherent_states_are_malformed_never_grounded` | CI |
| **V-TWO-STATE** (F2) `held_at_K` is computed from `snapshot` ALONE; `status` additionally applies CURRENT caps, which only ever SUBTRACT. The headline cell: a record corrected/disputed/revoked AFTER K returns `held_at_K=True` with `status` `FENCED_AS_OF`/`EXCLUDED` — we report that we believed it then AND refuse to assert it now. `revoked_source` current → `EXCLUDED` at every K (0022 non-revival never time-travels away). No current cap can RAISE a verdict | `test_two_state_current_caps_subtract_only` | CI |
| **V-NORMALIZE** (F6 + **B-1**) type and datetime normalization precede every membership test and comparison **on BOTH legs**: a non-string (incl. unhashable) reason on EITHER `snapshot` or `current` returns `MALFORMED` without reaching `in`/`dict.get`; every timestamp from EITHER state is UTC-coerced inside rule 2's guard — including `current.invalidated_at`, which v6 normalized on the final line, outside the guard, so garbage there raised uncaught at the end of an otherwise-green classification | `test_normalization_covers_both_states` | CI |
| **V-FAILCLOSED** (finding 3) `AS_OF_DISPOSITION` is a TOTAL dict; `set(AS_OF_DISPOSITION) == set(DISPOSITIONED_REASONS)` exactly (build fails on any undispositioned reason in EITHER); runtime defaults an unknown/missing key to `FENCED` | `test_as_of_disposition_is_total_and_failclosed` | CI |
| **V-CURRENT-UNCHANGED** (finding 7) `Edge.assertable` is not modified; the current recall path does not call the as-of classifier — proven via a caller-grep AND the current path run against the **post-0027** frozen classification oracle (the baseline is pinned to the post-0027 implementation commit, §Spec-Requires — NOT `d7bf16b`, which predates 0027's v10 oracle). `classify_as_of(...,now).status==GROUNDED_AS_OF` agrees with `edge.assertable` for the ordinary edge and diverges on EXACTLY the two §4e state cells | `test_current_path_oracle_identical_post0027` + `test_as_of_now_diverges_only_on_two_cells` | CI |
| **V-INTERVAL** groundable only within the half-open `[valid_from, invalidated_at)`; `T == invalidated_at` excluded (successor's); UTC-aware comparison only (§10) | `test_half_open_interval_boundaries` | CI |
| **V-SCOPE** (finding 1 + F2 + F7) visibility is the **OUTERMOST** gate — evaluated before normalization, coherence and time — so a hidden record returns ONLY `SCOPE_HIDDEN` (never `MALFORMED`, never `held_at_K`), leaking neither existence nor condition. Shaping then composes via `gate.scoped_assertable` on the TIME-RELATIVE verdict, NEVER `view.shape()`. **CURRENT scope governs every answer including historical ones** (0029 versions edge state, not scope policy/membership). Fixtures: (a) cross-scope-visible `superseded` grounds unscoped, `FENCED_AS_OF` for the restricted principal; (b) **hidden + malformed → `SCOPE_HIDDEN` only** (joint scenario 8) | `test_scope_outermost_hidden_never_leaks` + `test_scope_composes_via_time_relative_verdict_not_shape` | CI |
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
7. **JOINT acceptance scenarios (shared with 0029).** The reviewer's eight
   scenarios become the SHARED §6a corpus across both specs — dev seeds them
   0029-side, and the §4a-ii reason×cutoff matrix supplies the 0030 expectations
   for the two-state cells. 0030 owns exact outcomes for:
   - **(2)** source revocation followed by reinstatement, `K` between them —
     current `revoked_source` → `EXCLUDED` at every K; after reinstatement the
     CURRENT row no longer carries it, so the cap lifts (the snapshot at K is
     unchanged: `held_at_K` is stable while `status` moves — precisely the
     two-state split);
   - **(7)** a later correction/dispute/revocation applied to an earlier
     snapshot → `held_at_K=True`, `status` `FENCED_AS_OF`/`EXCLUDED`;
   - **(8)** a malformed edge hidden from the querying principal →
     `SCOPE_HIDDEN` ONLY (F7). **The malformed axis now has TWO states to be
     malformed in (B-1/B-2):** the family crosses {snapshot malformed, current
     malformed, both} × {unhashable reason, non-datetime, active+reason,
     inactive+no-reason, inverted interval} × {hidden, visible} — asserting
     `MALFORMED` for visible incoherence on EITHER leg, `SCOPE_HIDDEN` when
     hidden, and NO raise anywhere;
   and consumes 0029's outcomes for (1), (3), (4), (5), (6) as snapshot inputs.

Pass = **100% match**. Corpus frozen + portable builder (`--check`) + digest
recorded in `## Review closure` before implementation (0028 R1-6/R1-7 pattern).

## 7. Failure modes and reversibility
- **Fully additive / reversible:** 0030 adds a predicate; removing it restores
  today exactly (`Edge.assertable` never changed). No migration, no schema
  change, no data rewrite.
- **New-reason safety:** a producer's new reason fails the totality test until
  dispositioned; until then the runtime default fences it. **Correction (F8.4):
  the registry is NOT narrow-only** — re-dispositioning a reason to `GROUNDABLE`
  plainly widens what grounds, and v4 claimed otherwise. What IS guaranteed:
  (a) TOTALITY — the build fails on any undispositioned reason, so a widening is
  always an explicit, reviewed edit, never a silent default; and (b) the runtime
  lookup defaults UNKNOWN to `FENCED`, so drift can only fence. Widening is
  possible but never accidental.

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
3. **Scope composition, two-state (F2 + F7).** Visibility is now the OUTERMOST
   gate and CURRENT scope governs every answer, including historical ones
   (0029 versions edge state, not scope policy). Attack that: can a cross-scope
   historical edge ground for the wrong principal via `gate.scoped_assertable`
   on the time-relative verdict? Does anything about a hidden record leak —
   existence, malformedness, or `held_at_K`? And is "current scope governs the
   past" the right ruling, or does it mis-answer "who could see this at K?"
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
- **`absorbed_duplicate` — UN-RETIRED (F8.3).** v2 retired this as "unreachable
  by the empty-interval construction"; round-1 finding 4 overturned that (the
  GENERIC invalidation paths can persist a NON-empty absorbed interval, and a
  classifier seeing only an edge cannot prove canonicity). §4b now classes it
  **GROUNDABLE and exercises the non-empty case**; this entry contradicted §4b
  and is corrected rather than left as a stale retirement. The live question is
  the narrow one: 0030 grounds the absorbed edge and 0028 resolves to the
  absorber — or should only the absorber ever ground? (Leaning: as specified;
  reviewer to rule.)
- **Boundary instant `T == invalidated_at`.** Half-open interval excludes it
  (successor's). Confirm this matches 0003's supersession boundary exactly (no
  gap, no overlap).

## Review closure
*n/a — draft; the frozen §6a manifest digest + the registry-totality evidence
land here before `accepted`. Entry into external review on Quentin's word.*
