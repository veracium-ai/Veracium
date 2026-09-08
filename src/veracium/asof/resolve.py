"""specs/0028 §4a–§4b — the as-of RESOLUTION: *what did we hold to be true
at T*, over 0030's classifier, one clock read, one store snapshot.

The algorithm is §4a's, in its order: (0) normalise T (§2c-i, V-NORM-FIRST),
read the store's INJECTED clock EXACTLY ONCE (V-ONE-CLOCK) and refuse the
future with the typed `FutureAsOfRefused` (V-NO-FUTURE); (1) keep the edges
whose half-open interval `[valid_from, invalidated_at)` contains T — an
empty interval is held at no T (V-EMPTY); (2) ask `classify_as_of` for the
verdict at T with the threaded `now` — the recall path's `assertable` drop
DOES NOT RUN here; (3) resolve by §4b's reason→resolution table, TOTAL over
`DISPOSITIONED_REASONS` plus the `None` and unknown cases, failing closed
(V-TOTAL, V-MUTANT, V-NONE); (4) attach the resolution tag and the interval
to each result. Every store read joins ONE `read_window` (§4b-o,
V-ONE-SNAPSHOT), and scope is applied BEFORE historical eligibility (§3b):
the candidate set is the principal's visible set, so T is never a
capability (V-SCOPE-DIFFERENTIAL).

No row upgrades a 0030 verdict (V-NO-UPGRADE): the table gives the outcome's
SHAPE and the verdict caps it — a `RETURN_SELF` row whose verdict is not
`GROUNDED_AS_OF` returns `FENCED_SELF`. `INDETERMINATE` is never silent
about itself and carries a cause in exactly one of two classes (§4b, R6-1):
a condition observable WITHIN the caller's view (branching, a cycle, an
unclassifiable row) discloses its cause; a `SUCCESSOR_UNAVAILABLE`
disposition carries NONE, so a hidden successor and a missing one stay one
outcome (V-NO-EXISTENCE-SIGNAL).

The snapshot leg handed to the classifier is the LIVE row (kind "live",
txn 0 — 0030's own "no K given" fixture shape): v2 is valid-time only and
reads no journal (§4d).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from ..schema import (ASSERTS_SUPERSESSION, DISPOSITIONED_REASONS, Edge,
                      SuccessorDisposition, SuccessorLookup, as_utc,
                      as_utc_optional, as_utc_required)
from ..scope_linkage import _is_canonical
from ..store.base import RawEdgeState
from .carrier import Envelope
from .classify import (EXCLUDED, GROUNDED_AS_OF, IDENTITY_UNBOUND, MALFORMED,
                       NOT_VALID_AT_T, SCOPE_HIDDEN, STALE_AT_RECALL,
                       classify_as_of)

#: §4b-i — N, pinned HERE for integrity, not cost: an unbounded walk over a
#: corrupted store can cycle, and depth is itself a signal.
HOP_BOUND = 3


class FutureAsOfRefused(ValueError):
    """§2c / §4a step 0 — as-of never answers about the future. Carries the
    requested `T` and the `now` it was compared against (both aware UTC). At
    the library it is RAISED; a tool layer serialises it (§2c)."""

    def __init__(self, T: datetime, now: datetime):
        self.T = T
        self.now = now
        super().__init__(
            f"as-of refuses the future: T={T.isoformat()} is after the resolution's "
            f"one clock read now={now.isoformat()} (specs/0028 §4a step 0, V-NO-FUTURE)")


# ---------------------------------------------------------------- vocabulary
# §4b — the CLOSED outcome vocabulary
RETURN_SELF = "RETURN_SELF"
RETURN_SELF_FLAGGED = "RETURN_SELF_FLAGGED"
FENCED_SELF = "FENCED_SELF"
NOT_RETURNABLE = "NOT_RETURNABLE"
INDETERMINATE = "INDETERMINATE"
POINTER_TO = "POINTER_TO"
OUTCOMES = frozenset({RETURN_SELF, RETURN_SELF_FLAGGED, FENCED_SELF,
                      NOT_RETURNABLE, INDETERMINATE, POINTER_TO})
#: the outcomes a caller may ASSERT (§3: GROUNDED_AS_OF, flagged or not)
GROUNDED_OUTCOMES = frozenset({RETURN_SELF, RETURN_SELF_FLAGGED})

# §4b — the resolution tags, one per row
TAG_CURRENT = "current"
TAG_IN_INTERVAL = "in-interval"
TAG_IN_INTERVAL_STALE = "in-interval-stale"
TAG_ABSORBER_INDETERMINATE = "absorber-indeterminate"
TAG_ABSORBER_POINTER = "absorber-pointer"          # §4b-iii, the unreachable canonical cell
TAG_NO_ABSORBER = "no-absorber"                    # §4b-iii, a corrupted-state cell
TAG_CORRECTED_FENCED = "corrected-fenced"
TAG_DISPUTED = "disputed"
TAG_REVOKED_EXCLUDED = "revoked-excluded"
TAG_UNKNOWN_REASON_EXCLUDED = "unknown-reason-excluded"
TAG_UNCLASSIFIABLE = "unclassifiable-indeterminate"   # §3's (unclassifiable) row

# the INDETERMINATE causes that arise WITHIN the caller's view (disclosed)
CAUSE_HOP_BOUND = "hop-bound-exceeded"
CAUSE_CYCLE = "cycle"
CAUSE_BRANCHING = "branching"
CAUSE_ABSORBER_LEGACY = "absorber-unreachable-legacy"
CAUSE_AMBIGUOUS_ABSORBER = "ambiguous-absorber"
CAUSE_NO_ABSORBER = "no-absorber"
CAUSE_UNCLASSIFIABLE = "unclassifiable"

#: §4b's reason → (outcome shape, tag), TOTAL over the registry (V-TOTAL):
#: an eighth reason fails BOTH this gate and the registry's own totality test.
#: The `absorbed_duplicate` shape is the legacy row's — the only one a shipped
#: writer reaches (§4b-iii); the ledger read below picks the defensive cells.
RESOLUTION: dict = {
    "superseded":         (RETURN_SELF, TAG_IN_INTERVAL),
    "lapsed":             (RETURN_SELF_FLAGGED, TAG_IN_INTERVAL_STALE),
    "decayed":            (RETURN_SELF_FLAGGED, TAG_IN_INTERVAL_STALE),
    "absorbed_duplicate": (INDETERMINATE, TAG_ABSORBER_INDETERMINATE),
    "corrected":          (FENCED_SELF, TAG_CORRECTED_FENCED),
    "disputed":           (FENCED_SELF, TAG_DISPUTED),
    "revoked_source":     (NOT_RETURNABLE, TAG_REVOKED_EXCLUDED),
}
if set(RESOLUTION) != set(DISPOSITIONED_REASONS):
    raise ImportError(
        "specs/0028 §4b RESOLUTION and DISPOSITIONED_REASONS disagree on the reason "
        f"set ({sorted(set(RESOLUTION) ^ set(DISPOSITIONED_REASONS))}) — a new reason "
        "must be dispositioned TWICE (V-TOTAL)")
if {o for o, _t in RESOLUTION.values()} - OUTCOMES:
    raise ImportError("RESOLUTION carries an outcome outside the closed vocabulary")


# ------------------------------------------------------------------ carriers
@dataclass(frozen=True)
class Pointer:
    """§4b-i — *where truth became*, a current-state fact offered beside a
    valid-time answer. `outcome` is POINTER_TO (a head, classified by 0030
    at T=now — a fenced or excluded head renders as a pointer to a fenced or
    excluded record, never as truth: V-HEAD) or INDETERMINATE with `cause`
    hop-bound-exceeded / cycle / branching — or NO cause when the walk met
    SUCCESSOR_UNAVAILABLE (§4b's second class; V-NEVER-HEAD)."""
    outcome: str
    head_id: Optional[str] = None
    head_status: Optional[str] = None
    hops: int = 0
    cause: Optional[str] = None


@dataclass(frozen=True)
class Resolution:
    """§4c — the provenance on every result: the interval, the reason, the
    resolution tag, the 0030 status at T, its flags, the INDETERMINATE
    cause when one is disclosed, and the pointer for a corrected row."""
    edge_id: str
    outcome: str
    tag: str
    valid_from: datetime
    invalidated_at: Optional[datetime]
    invalidation_reason: Optional[str]
    status: str
    flags: frozenset = field(default_factory=frozenset)
    cause: Optional[str] = None
    pointer: Optional[Pointer] = None


@dataclass(frozen=True)
class AsOfFact:
    """One returned record: the (scope-shaped) edge and its resolution."""
    edge: Edge
    resolution: Resolution


@dataclass(frozen=True)
class AsOfAnswer:
    """The resolution's result: the normalised T, the ONE `now` it read, and
    the returnable facts ordered `valid_from` asc then `id` asc. A
    NOT_RETURNABLE row is absent (§3: EXCLUDED → nothing); an INDETERMINATE
    row is PRESENT, never collapsed into an empty result."""
    T: datetime
    now: datetime
    facts: tuple = ()

    def resolution_of(self, edge_id: str) -> Optional[Resolution]:
        for f in self.facts:
            if f.edge.id == edge_id:
                return f.resolution
        return None


# ------------------------------------------------------------- the accessor
def lookup_successors(rows, edge_id: str, visible: Callable) -> SuccessorLookup:
    """§5.1's lookup over ONE already-read edge set — the in-memory half of
    the scan-backed accessor (`SqliteStore.edges_superseding` reads the rows
    inside the window and calls this). The queried edge is read through the
    SAME visibility as the successors (R5-1): invisible, it asserts nothing
    to this caller, exactly as a nonexistent id does — one code path. A
    dangling BACKWARD pointer on the queried edge is never consulted (R5-2:
    the search is forward, for rows whose `supersedes == edge_id`)."""
    me = next((e for e in rows if e.id == edge_id and visible(e)), None)
    successors = sorted((e for e in rows if e.supersedes == edge_id and visible(e)),
                        key=lambda e: (as_utc(e.valid_from), e.id))
    if successors:
        return SuccessorLookup(SuccessorDisposition.SUPERSEDED, tuple(successors))
    if me is not None and me.invalidation_reason in ASSERTS_SUPERSESSION:
        return SuccessorLookup(SuccessorDisposition.SUCCESSOR_UNAVAILABLE, ())
    return SuccessorLookup(SuccessorDisposition.HEAD, ())


def is_head(lookup: SuccessorLookup) -> bool:
    """The walk's head predicate (R4-5): HEAD ONLY — never
    SUCCESSOR_UNAVAILABLE (INDETERMINATE), never SUPERSEDED."""
    return lookup.disposition is SuccessorDisposition.HEAD


# ------------------------------------------------------------ the algorithm
def normalise_T(T) -> datetime:
    """§2c-i's input table for T, ENFORCED HERE: `None` → TypeError (the
    argument is required); a `str` or any non-datetime → ValueError; a NAIVE
    datetime → ValueError, distinct from FutureAsOfRefused; an aware
    datetime → UTC. Stated because the spec attributes these outcomes to
    `as_utc_required`, and that helper does NOT produce them: it takes a
    naive value as UTC (0032's stored-value convention) and PARSES ISO text
    (0030's raw carriers). The caller's T is neither a stored value nor a
    raw carrier, so the table is the resolution's own gate (2026-09-08;
    recorded for the spec's §2c-i amendment)."""
    if T is None:
        raise TypeError("T is required (specs/0028 §2c-i)")
    if isinstance(T, bool) or not isinstance(T, datetime):
        raise ValueError(f"T must be an aware datetime, got {type(T).__name__} "
                         "(specs/0028 §2c-i; 0030 V-NORM-TOTAL)")
    if T.tzinfo is None or T.tzinfo.utcoffset(T) is None:
        raise ValueError("T must be timezone-aware; a naive datetime is refused before "
                         "any comparison with now (specs/0028 §2c-i, V-NORM-FIRST)")
    return as_utc(T)


def held_at(edge: Edge, T: datetime) -> bool:
    """§4a step 1 — the half-open interval test, both ends normalised through
    the SAME helper (V-BOUNDARY): `valid_from ≤ T AND (invalidated_at IS NULL
    OR T < invalidated_at)`. `invalidated_at ≤ valid_from` is an empty
    interval, held at no T (V-EMPTY)."""
    vf = as_utc_required(edge.valid_from)
    ia = as_utc_optional(edge.invalidated_at)
    return vf <= T and (ia is None or T < ia)


def resolve_as_of(store, user_id: str, T, *, principal=None, policy=None,
                  subject: Optional[str] = None, relation: Optional[str] = None,
                  view=None) -> AsOfAnswer:
    """THE resolution (§4a). Deterministic given (store snapshot, requested T,
    captured now, principal scope, policy version). `view` may be supplied
    by a caller that already built the principal's `ScopeView` (recall);
    otherwise it is built here from `principal`/`policy` — both None gives
    the unscoped view exactly as recall does (§4c)."""
    # 0. NORMALISE FIRST (§2c-i) — a naive or non-datetime T is a ValueError,
    #    never FutureAsOfRefused (V-NORM-FIRST) …
    T = normalise_T(T)
    # … then THE ONE CLOCK READ, at entry; threaded everywhere below.
    now = as_utc_required(store._now())
    if T > now:
        raise FutureAsOfRefused(T, now)
    if view is None and principal is not None:
        from ..scope_read import view_for
        view = view_for(store, user_id, principal, policy)
    visible = (lambda e: True) if view is None else view.visible
    facts = []
    # §4b-o — ONE SNAPSHOT: every read below joins this window.
    with store.read_window(user_id):
        rows = store.edges(user_id, active_only=False, include_quarantined=True)
        # §3b — scope BEFORE historical eligibility: the candidate set is the
        # principal's visible set at every T, so T is not a capability.
        candidates = [e for e in rows if visible(e)
                      and (subject is None or e.subject == subject)
                      and (relation is None or e.relation == relation)]
        for e in candidates:
            if not held_at(e, T):                       # step 1
                continue
            r = _resolve_edge(store, user_id, e, rows, T, now, view,
                              principal, policy, visible)
            if r is None or r.outcome == NOT_RETURNABLE:
                continue
            shaped = e if view is None else view.shape(e, asserted=True)
            facts.append(AsOfFact(shaped, r))
    facts.sort(key=lambda f: (as_utc(f.edge.valid_from), f.edge.id))
    return AsOfAnswer(T=T, now=now, facts=tuple(facts))


def _classify_live(store, user_id, edge_id, T, now, view, principal, policy):
    """§4a step 2 — 0030's verdict for one row read INSIDE the window, the
    live row as the snapshot leg. Returns (Result, current_raw)."""
    cs = store.current_state(user_id, edge_id, principal=principal, policy=policy)
    if cs.current_raw is None:
        return None, None
    snap = RawEdgeState(edge_id=edge_id, user_id=user_id, state=cs.current_raw,
                        txn=0, seq=0, kind="live", recorded_at="")
    return classify_as_of(Envelope(user_id, edge_id), snap, cs, T, now, view), cs.current_raw


def _resolve_edge(store, user_id, e, rows, T, now, view, principal, policy,
                  visible) -> Optional[Resolution]:
    """§4a steps 2–3 for one held edge. None means "not a candidate to this
    caller" (the classifier's SCOPE_HIDDEN, or a row gone between reads —
    impossible inside one window, stated for totality)."""
    res, _raw = _classify_live(store, user_id, e.id, T, now, view, principal, policy)
    if res is None:
        return None
    st = res.status
    base = dict(edge_id=e.id, valid_from=as_utc_required(e.valid_from),
                invalidated_at=as_utc_optional(e.invalidated_at),
                invalidation_reason=e.invalidation_reason,
                status=st, flags=res.flags)
    if st in (SCOPE_HIDDEN, NOT_VALID_AT_T):
        return None
    # V-MUTANT / V-NONE — the table is total over the TYPE, not over today's
    # writers: an invalidated row whose reason is outside the registry, or
    # None, is NOT_RETURNABLE before any other reading (fail closed; 0030
    # reads a None reason on a retired row as MALFORMED, which this outranks).
    if e.invalidated_at is not None and e.invalidation_reason not in RESOLUTION:
        return Resolution(outcome=NOT_RETURNABLE, tag=TAG_UNKNOWN_REASON_EXCLUDED, **base)
    if st in (MALFORMED, IDENTITY_UNBOUND):             # §3 (unclassifiable)
        return Resolution(outcome=INDETERMINATE, tag=TAG_UNCLASSIFIABLE,
                          cause=CAUSE_UNCLASSIFIABLE, **base)
    if st == EXCLUDED:                                  # 0022 non-revival, any T
        return Resolution(outcome=NOT_RETURNABLE, tag=TAG_REVOKED_EXCLUDED, **base)
    if e.invalidated_at is None:                        # the `current` row
        return Resolution(outcome=RETURN_SELF if st == GROUNDED_AS_OF else FENCED_SELF,
                          tag=TAG_CURRENT, **base)
    reason = e.invalidation_reason
    outcome, tag = RESOLUTION[reason]
    if outcome == NOT_RETURNABLE:
        return Resolution(outcome=outcome, tag=tag, **base)
    if outcome in GROUNDED_OUTCOMES and st != GROUNDED_AS_OF:
        outcome = FENCED_SELF                           # V-NO-UPGRADE: the verdict caps the row
    cause, pointer = None, None
    if reason == "corrected":
        pointer = _walk(store, user_id, e, rows, now, view, principal, policy, visible)
    elif reason == "absorbed_duplicate":
        outcome, tag, cause, pointer = _absorber(store, user_id, e, rows, now, view,
                                                 principal, policy, visible)
    return Resolution(outcome=outcome, tag=tag, cause=cause, pointer=pointer, **base)


def _walk(store, user_id, start, rows, now, view, principal, policy, visible) -> Pointer:
    """§4b-i — the pointer walk: at most HOP_BOUND hops, NO T inside it.
    Terminates on the chain HEAD (the head predicate is HEAD-only), on
    SUCCESSOR_UNAVAILABLE (INDETERMINATE, no cause — never a head), on
    branching, on the bound, or on a cycle. In-memory over the ONE read
    (§5.1's complexity row): each hop is `lookup_successors` over `rows`."""
    seen = {start.id}
    cur, hops = start, 0
    while True:
        lk = lookup_successors(rows, cur.id, visible)
        if lk.disposition is SuccessorDisposition.SUCCESSOR_UNAVAILABLE:
            return Pointer(INDETERMINATE, hops=hops, cause=None)
        if is_head(lk):
            break
        if len(lk.successors) > 1:
            return Pointer(INDETERMINATE, hops=hops, cause=CAUSE_BRANCHING)
        nxt = lk.successors[0]
        if nxt.id in seen:
            return Pointer(INDETERMINATE, hops=hops, cause=CAUSE_CYCLE)
        hops += 1
        if hops > HOP_BOUND:
            return Pointer(INDETERMINATE, hops=hops, cause=CAUSE_HOP_BOUND)
        seen.add(nxt.id)
        cur = nxt
    # the head carries its own classification, at T=now (V-HEAD). This is
    # THE sanctioned exception to "no now-fact inside a T-answer" (the rule
    # that omits the wiki, the episodes and the contested block): the pointer
    # is offered BESIDE the valid-time answer as a current-state fact and
    # renders as one. Generalise neither the rule nor the exception.
    res, _raw = _classify_live(store, user_id, cur.id, now, now, view, principal, policy)
    status = res.status if res is not None else MALFORMED
    return Pointer(POINTER_TO, head_id=cur.id, head_status=status, hops=hops)


def _absorber(store, user_id, e, rows, now, view, principal, policy, visible):
    """§4b-iii — the absorber, when asked. The ledger read is scoped like
    §5.1's successor search: a canonical row whose survivor is not in the
    caller's view is NOT IN THE VIEW, so it falls to the legacy cell (a
    distinguishable hidden-absorber cause would be the existence signal).
    Exactly one cell is reachable from a shipped writer — legacy (no row
    names the edge) → INDETERMINATE `absorber-unreachable-legacy`; the other
    three are defensive handling of store states no shipped writer produces.
    Returns (outcome, tag, cause, pointer)."""
    by_id = {x.id: x for x in rows}
    ledger = [r for r in store.contributions_naming(user_id, e.id)
              if r.get("survivor_type") == "edge"
              and r.get("survivor_id") in by_id and visible(by_id[r["survivor_id"]])]
    if not ledger:
        return INDETERMINATE, TAG_ABSORBER_INDETERMINATE, CAUSE_ABSORBER_LEGACY, None
    canonical = sorted({r["survivor_id"] for r in ledger if _is_canonical(r)})
    if not canonical:
        return NOT_RETURNABLE, TAG_NO_ABSORBER, CAUSE_NO_ABSORBER, None
    if len(canonical) > 1:                  # the exporter raises; the query is no more permissive
        return INDETERMINATE, TAG_ABSORBER_INDETERMINATE, CAUSE_AMBIGUOUS_ABSORBER, None
    res, _raw = _classify_live(store, user_id, canonical[0], now, now, view, principal, policy)
    status = res.status if res is not None else MALFORMED
    return (POINTER_TO, TAG_ABSORBER_POINTER, None,
            Pointer(POINTER_TO, head_id=canonical[0], head_status=status, hops=1))


# --------------------------------------------------------------- rendering
def render_line(e: Edge, r: Optional[Resolution], T: datetime) -> str:
    """§4a step 4 — one rendered result carrying its tag and interval. The
    grounded outcomes render as facts *as of T*; FENCED_SELF and POINTER_TO
    as what was believed (never assert); INDETERMINATE names itself and its
    disclosed cause. Reads no wall-clock predicate."""
    if r is None:
        return ""
    who = "" if e.subject == "user" else f"{e.subject} "
    note = f" — {e.note}" if e.note else ""
    held = (f"held {r.valid_from.date()}→"
            f"{r.invalidated_at.date() if r.invalidated_at else 'open'}")
    prov = f"(as of {T.date()}: {r.tag}; {held})"
    if r.outcome in GROUNDED_OUTCOMES:
        stale = (" [possibly stale — confirm before relying on it]"
                 if STALE_AT_RECALL in r.flags else "")
        return f"{who}{e.relation}: {e.object}{note} {prov}{stale}"
    if r.outcome == INDETERMINATE:
        cause = f"; cause {r.cause}" if r.cause else ""
        return (f"[INDETERMINATE as of {T.date()}{cause}, never assert as fact] "
                f"{who}{e.relation}: {e.object}{note} {prov}")
    ptr = ""
    if r.pointer is not None:
        if r.pointer.outcome == POINTER_TO:
            ptr = f" [truth became: {r.pointer.head_id} ({r.pointer.head_status})]"
        else:
            c = f" — {r.pointer.cause}" if r.pointer.cause else ""
            ptr = f" [truth became: INDETERMINATE{c}]"
    return (f"[FENCED as of {T.date()} — what was believed, never assert as fact] "
            f"{who}{e.relation}: {e.object}{note} {prov}{ptr}")


def render_fn_for(answer: AsOfAnswer) -> Callable:
    """A `render_edges`-shaped callable (`edges -> str`) bound to one answer,
    for the budget's clamp; an edge without a resolution renders nothing."""
    by_id = {f.edge.id: f.resolution for f in answer.facts}

    def render(edges) -> str:
        return "\n".join(ln for ln in (render_line(e, by_id.get(e.id), answer.T)
                                       for e in edges) if ln)
    return render
