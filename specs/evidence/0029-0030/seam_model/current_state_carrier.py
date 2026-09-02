"""Seam model — the BOUND CurrentState carrier, executable.

Round-3 F2: `CurrentState` REPLACES the separate current carrier, so there is
no second current read to be stale against. Round-2 F4/C-2/C-4: identity is
ROW-SOURCED and binding is parse-independent, checked BEFORE visibility.

This model executes the BINDING half -- the store-side one-consistent-read
derivation is the 0029 seat's `restriction_derivation.py`.

RULE ZERO: every assertion ships with a negative control in this file.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass(frozen=True)
class RawEdgeState:
    """0029's carrier. Identity from the event ROW columns; `state` is TEXT."""
    edge_id: str
    user_id: str
    state: str
    txn: int = 0
    seq: int = 0
    kind: str = "mutated"
    recorded_at: str = ""


class RestrictionVerdict(str, Enum):
    """THREE-VALUED (round-5 F2), because a boolean would have to lie.

    `project_store` validates EVERY row via `Edge.model_validate_json`
    (revocation.py:217), so ONE malformed row anywhere in the user's store
    makes the sweep raise — the restriction is not merely awkward to compute,
    it is IMPOSSIBLE to compute. Over such a store both `True` and `False`
    would be fabrications, and a raise is the one indefensible outcome in this
    path. So the carrier states WHAT WAS ACTUALLY COMPUTED -- round-4 F4's
    principle applied again.
    """
    CLEAR = "clear"                    # sweep ran; this edge is not covered
    RESTRICTED = "restricted"          # sweep ran; a standing revocation covers it
    UNDETERMINABLE = "undeterminable"  # the projection could not be built


@dataclass(frozen=True)
class ScopeCell:
    """The scope decision, computed IN-TRANSACTION and carried (round-5 F1).

    The classifier CONSUMES this and never calls `view.visible`/`view.decision`
    itself: a live call would trigger lazy contribution-ledger reads AFTER the
    read window closed, which is the seam the one-consistent-read design exists
    to kill. `fail_closed=True` marks the cell that was NOT computed from a
    readable payload -- a malformed current row with a principal present yields
    hidden, no raise.
    """
    visible: bool
    shape: Optional[str]
    fail_closed: bool = False
    principal: Optional[tuple] = None   # the (origin, source_id) the cell was
                                        # COMPUTED FOR. Round-5, research:
                                        # moving the scope decision into the
                                        # carrier removes the live call but
                                        # recreates C-4's unbound-leg risk one
                                        # level down -- a cell computed for
                                        # principal A, passed with an envelope
                                        # classified for B, would silently
                                        # answer the wrong question. X-3 bound
                                        # the VIEW for exactly this reason; the
                                        # precomputed cell needs the same bind,
                                        # so it carries what it was computed for
                                        # and rule 0 checks it.


@dataclass(frozen=True)
class CurrentState:
    """Row, standing set and sweep from ONE read transaction -- one snapshot.

    `current_raw is None` means NO CURRENT ROW. Defensive totality over a shape
    the type admits, believed unreachable today (rows die only with the whole
    user, journal included, via forget_user's table loop). Absence never grants.
    """
    user_id: str
    edge_id: str
    current_raw: Optional[str]
    source_restricted: RestrictionVerdict   # round-4 F4 -> round-5 F2: a VERDICT.
                                            # `frozenset(standing)` claimed a
                                            # per-digest computation never
                                            # performed; a bare bool then had to
                                            # lie over an unprojectable store.
    read_token: int
    scope_cell: Optional[ScopeCell] = None  # None = NO PRINCIPAL was supplied.
                                            # THE COLLAPSE HAPPENS AT THE
                                            # CLASSIFIER, NEVER HERE: the carrier
                                            # keeps all three verdicts and the
                                            # cell so a render or audit consumer
                                            # can distinguish "restricted" from
                                            # "could not determine" even though
                                            # both refuse to ground. A carrier
                                            # that pre-collapsed would re-lose the
                                            # information one hop later.


@dataclass(frozen=True)
class Envelope:
    user_id: str
    edge_id: str


class View:
    """Stands in for `ScopeView`, which exposes `user_id` (scope_read.py:310)
    AND `principal` (:311).

    ROUND-6 F2: this stand-in carried ONLY `user_id`, which is why `bind` could
    not check the cell's principal -- the field it needed to compare against did
    not exist on the model's own view. A stand-in narrower than production
    silently makes a check unwritable, and the missing check then reads as a
    design choice. `principal` here is the `(origin, source_id)` pair that
    production's principal object yields; the model compares the pair because
    that is what `ScopeCell.principal` records.
    """
    def __init__(self, user_id: str, principal: Optional[tuple] = None) -> None:
        self.user_id = user_id
        self.principal = principal


IDENTITY_UNBOUND = "IDENTITY_UNBOUND"
BOUND = "BOUND"


def bind(envelope: Envelope, snapshot: RawEdgeState,
         current: CurrentState, view: Optional[View]) -> str:
    """Rule 0 -- SIX legs, all row-sourced, before anything else.

    Parse-independent by construction (C-2): nothing here touches `state`, so
    a corrupt payload still BINDS correctly and is refused later as MALFORMED,
    rather than failing binding for the wrong reason.

    ROUND-6 F2 -- THE SIXTH LEG. v17 claimed "rule 0 binds it" of the scope
    cell's principal and `ScopeCell.principal`'s own comment said "rule 0 checks
    it". Neither was true: the cell was STORED and never consulted, so a cell
    computed for principal A could answer for an envelope classified under B --
    the exact escalation the field was added to prevent. The tests shared the
    blame precisely: they asserted the principal was STORED, not that binding
    ENFORCES it. An executed test of the wrong property.
    """
    if not (snapshot.edge_id == current.edge_id == envelope.edge_id
            and snapshot.user_id == current.user_id == envelope.user_id):
        return IDENTITY_UNBOUND
    if view is not None and view.user_id != envelope.user_id:
        return IDENTITY_UNBOUND
    # Leg 6 (round-8 F1, the rule finally in its stable form):
    # THE CELL AND THE VIEW ARE A PAIR -- present together, absent together,
    # and bound to one principal when present. Any violation is a rule-0
    # refusal, because the failure is the ASSEMBLY (inputs answering two
    # different questions), not the record.
    #
    # VIEW PRESENT: the cell is REQUIRED (the classifier reads visibility FROM
    # it; a missing cell means a None dereference or fail-open), and its
    # principal must match the view's.
    #
    # VIEW ABSENT: ANY cell is REFUSED -- principal-bearing or not. History of
    # this branch, kept because it took three rounds: round 6 bound everything
    # here ("the cell is surplus and unconsumed" -- false at the classifier's
    # steps 2 and 10, which consume the cell guarded on ITS presence, not the
    # view's); round 7 refused only the principal-BEARING cell, reasoning that
    # a principal-less one "identifies no one" -- but it still carries
    # visible/shape that steps 2/10 consume, i.e. the same influence channel
    # MINUS attribution, which is strictly worse; and the producer never emits
    # a cell without a view (restriction_derivation builds scope_cell=None
    # there), so refusal costs no legitimate path anything. Round 8's reviewer
    # asked for exactly this; the permissiveness was the round-6 misreading's
    # last residue.
    cell = current.scope_cell
    if view is not None:
        if cell is None:
            return IDENTITY_UNBOUND
        if cell.principal != view.principal:
            return IDENTITY_UNBOUND
    elif cell is not None:
        return IDENTITY_UNBOUND
    return BOUND


def unbound_variant(envelope: Envelope, snapshot: RawEdgeState,
                    current: CurrentState, view: Optional[View]) -> str:
    """The PRE-F4 classifier: no binding at all. Kept as the control."""
    return BOUND


# --------------------------------------------------------------------------
# NEGATIVE CONTROLS
# --------------------------------------------------------------------------

def control_cell_absence_refused_under_a_view() -> bool:
    """ROUND-6 X-B: a view with NO cell at all, on an otherwise bound record.

    True means binding REFUSES while the pre-F2 variant ACCEPTS. This is the
    dangerous direction the first draft left open: the classifier consumes
    `cell.visible`, so binding a view-without-cell hands it None.
    """
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "{}")
    cur = CurrentState("u", "A", "{}", RestrictionVerdict.CLEAR, 1)   # no cell
    v = View("u", principal=("orig", "A"))
    return (bind(env, snap, cur, v) == IDENTITY_UNBOUND
            and unbound_variant(env, snap, cur, v) == BOUND)


def control_no_view_refuses_a_principal_bearing_cell() -> bool:
    """ROUND-7 F1, replacing `control_no_view_does_not_require_a_cell`, which
    asserted the OPPOSITE and was wrong.

    A cell computed FOR principal Z, passed with NO view. True means binding
    REFUSES while the pre-F2 variant ACCEPTS. The old control asserted this
    case must BIND, on the reasoning that a viewless record never consumes the
    cell -- false at the classifier's steps 2 and 10, which guard on the CELL's
    presence, not the view's.

    A control can be executed, green, and still assert the wrong property. This
    one did, for a whole round.
    """
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "{}")
    cur = CurrentState("u", "A", "{}", RestrictionVerdict.CLEAR, 1,
                       scope_cell=ScopeCell(True, "full", principal=("o", "Z")))
    return (bind(env, snap, cur, None) == IDENTITY_UNBOUND
            and unbound_variant(env, snap, cur, None) == BOUND)


def control_viewless_cell_is_refused() -> bool:
    """ROUND-8 F1: ANY cell under no view is refused -- principal-bearing or
    not. Replaces `control_no_view_allows_a_principal_less_cell`, which asserted
    the round-7 narrowing this round removed: a principal-less cell still
    carries the visible/shape the classifier consumes, so it is the same
    influence channel minus attribution. The bare no-cell case must still BIND,
    or the rule would reject every legitimate viewless record -- both halves
    asserted here so neither can silently widen or narrow."""
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "{}")
    bare = CurrentState("u", "A", "{}", RestrictionVerdict.CLEAR, 1)
    with_less = CurrentState("u", "A", "{}", RestrictionVerdict.CLEAR, 1,
                             scope_cell=ScopeCell(True, "full"))
    with_full = CurrentState("u", "A", "{}", RestrictionVerdict.CLEAR, 1,
                             scope_cell=ScopeCell(True, "full", principal=("o", "Z")))
    return (bind(env, snap, bare, None) == BOUND
            and bind(env, snap, with_less, None) == IDENTITY_UNBOUND
            and bind(env, snap, with_full, None) == IDENTITY_UNBOUND
            and unbound_variant(env, snap, with_less, None) == BOUND)


def control_cell_principal_is_enforced() -> bool:
    """ROUND-6 F2's discriminating control: a cell COMPUTED FOR principal A,
    passed with a view for principal B, on an otherwise perfectly bound record.

    True means binding REFUSES it while the pre-F2 variant ACCEPTS -- i.e. the
    sixth leg does work. This is the test that did not exist: the old ones
    asserted `cell.principal == A` after construction, which is satisfied by a
    field nothing reads.
    """
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "{}")
    cell_for_a = ScopeCell(visible=True, shape="full", principal=("orig", "A"))
    cur = CurrentState("u", "A", "{}", RestrictionVerdict.CLEAR, 1,
                       scope_cell=cell_for_a)
    view_for_b = View("u", principal=("orig", "B"))
    return (bind(env, snap, cur, view_for_b) == IDENTITY_UNBOUND
            and unbound_variant(env, snap, cur, view_for_b) == BOUND)


def control_cell_principal_absence_refused() -> bool:
    """The absence half, kept separate because it is a DIFFERENT claim: a cell
    carrying no principal at all, under a real view, must also refuse. Without
    this, `principal=None` would be the universal skeleton key past leg 6."""
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "{}")
    cur = CurrentState("u", "A", "{}", RestrictionVerdict.CLEAR, 1,
                       scope_cell=ScopeCell(visible=True, shape="full"))
    return bind(env, snap, cur, View("u", principal=("orig", "A"))) == IDENTITY_UNBOUND


def control_binding_is_load_bearing() -> bool:
    """A snapshot for edge A with a CurrentState for edge B.

    True means: the bound classifier REFUSES it while the unbound variant
    ACCEPTS -- i.e. rule 0 is doing work, and F4's escalation (borrowing B's
    caps and scope) was real rather than theoretical.
    """
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "{}")
    cur = CurrentState("u", "B", "{}", RestrictionVerdict.CLEAR, 1)      # foreign leg
    return (bind(env, snap, cur, None) == IDENTITY_UNBOUND
            and unbound_variant(env, snap, cur, None) == BOUND)


def control_view_leg_is_bound() -> bool:
    """A foreign principal's view must not ride along (round-2 X-3).

    True means the bound classifier refuses a view whose owner is not the
    envelope's user, while the unbound variant accepts.
    """
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "{}")
    cur = CurrentState("u", "A", "{}", RestrictionVerdict.CLEAR, 1)
    foreign = View("someone-else")
    return (bind(env, snap, cur, foreign) == IDENTITY_UNBOUND
            and unbound_variant(env, snap, cur, foreign) == BOUND)


def control_binding_survives_a_corrupt_payload() -> bool:
    """C-2's point: binding is parse-independent.

    True means a payload that cannot be parsed at all still BINDS, so the
    later refusal is MALFORMED (the honest reason) rather than an identity
    fault (the wrong one).
    """
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "}{ not json")
    cur = CurrentState("u", "A", "}{ not json", RestrictionVerdict.CLEAR, 1)
    return bind(env, snap, cur, None) == BOUND


def control_absence_does_not_grant() -> bool:
    """`current_raw is None` must not read as an unrestricted current world.

    True means the carrier still binds (identity is row-sourced and present)
    but carries no current payload for the caps to clear -- so the classifier's
    fail-closed branch is reachable and absence cannot be mistaken for
    permission.
    """
    env = Envelope("u", "A")
    snap = RawEdgeState("A", "u", "{}")
    cur = CurrentState("u", "A", None, RestrictionVerdict.CLEAR, 1)
    return bind(env, snap, cur, None) == BOUND and cur.current_raw is None
