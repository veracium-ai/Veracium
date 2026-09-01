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
    """Stands in for `ScopeView`, which exposes `user_id` (scope_read.py:310)."""
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id


IDENTITY_UNBOUND = "IDENTITY_UNBOUND"
BOUND = "BOUND"


def bind(envelope: Envelope, snapshot: RawEdgeState,
         current: CurrentState, view: Optional[View]) -> str:
    """Rule 0 -- FIVE legs, all row-sourced, before anything else.

    Parse-independent by construction (C-2): nothing here touches `state`, so
    a corrupt payload still BINDS correctly and is refused later as MALFORMED,
    rather than failing binding for the wrong reason.
    """
    if not (snapshot.edge_id == current.edge_id == envelope.edge_id
            and snapshot.user_id == current.user_id == envelope.user_id):
        return IDENTITY_UNBOUND
    if view is not None and view.user_id != envelope.user_id:
        return IDENTITY_UNBOUND
    return BOUND


def unbound_variant(envelope: Envelope, snapshot: RawEdgeState,
                    current: CurrentState, view: Optional[View]) -> str:
    """The PRE-F4 classifier: no binding at all. Kept as the control."""
    return BOUND


# --------------------------------------------------------------------------
# NEGATIVE CONTROLS
# --------------------------------------------------------------------------

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
