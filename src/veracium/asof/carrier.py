"""specs/0030 §4a-i — the carrier types the classifier CONSUMES and the store
DERIVES. Lifted from the joint seam model (`specs/evidence/0029-0030/seam_model/
current_state_carrier.py`, mutation-tested through eighteen rounds); the
model keeps its negative controls as the proof artifact, this module is the
product's ONE definition (round-5 F1: two definitions of one carrier cost a
finding). `RawEdgeState` — the snapshot leg — is 0029's and lives in
`veracium.store.base`.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RestrictionVerdict(str, Enum):
    """THREE-VALUED (round-5 F2), because a boolean would have to lie: the
    projection every row of the user's store feeds can be UNBUILDABLE, and
    over such a store both `clear` and `restricted` are fabrications. The
    carrier states what was actually computed; THE COLLAPSE HAPPENS AT THE
    CLASSIFIER (undeterminable → FENCED_AS_OF, never EXCLUDED)."""
    CLEAR = "clear"                    # sweep ran; this edge is not covered
    RESTRICTED = "restricted"          # sweep ran; a standing revocation covers it
    UNDETERMINABLE = "undeterminable"  # the projection could not be built


@dataclass(frozen=True)
class ScopeCell:
    """The scope decision, computed IN the read window and carried (round-5
    F1) so the classifier never calls `view.visible`/`view.decision` — a live
    call would fire lazy contribution-ledger reads AFTER the window closed.
    `fail_closed=True`: computed from an unreadable payload (hidden, no
    raise). `principal`: the `(origin, source_id)` it was COMPUTED FOR, bound
    at rule 0 (the moved-authority law: when an authority moves, ask what
    pair it just created)."""
    visible: bool
    shape: Optional[str]
    fail_closed: bool = False
    principal: Optional[tuple] = None


@dataclass(frozen=True)
class CurrentState:
    """Row, standing set, sweep, token and scope cell from ONE read window —
    one world. `current_raw is None` = NO current row (defensive totality;
    absence never grants). `scope_cell is None` = NO principal was supplied,
    distinct from a computed-hidden cell. `read_token` is audit/correlation
    only — NOT a cache key (no caching is specified anywhere)."""
    user_id: str
    edge_id: str
    current_raw: Optional[str]
    source_restricted: RestrictionVerdict
    read_token: int
    scope_cell: Optional[ScopeCell] = None


@dataclass(frozen=True)
class Envelope:
    """The REQUESTED (user_id, edge_id) — the caller's own leg of rule 0."""
    user_id: str
    edge_id: str
