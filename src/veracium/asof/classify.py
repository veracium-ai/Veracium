"""specs/0030 §4a — `classify_as_of`, TRANSCRIBED from the accepted spec's
pinned pseudocode (specs/0030-time-relative-classification.md :253-428, v30).
The spec is the authority: the rule numbers and their order below are the
spec's; the propagation check keeps the two in agreement. A PURE function of
its carrier inputs + the registry + (T, now, view) — it reads no clock
(`now` is a parameter; V-STALE reads it), opens no transaction, calls no
`view.visible`/`view.decision` (the scope decision is carried on the cell).

TWO verdicts, not one (F2): `held_at_K` — "the store held this belief at K",
from the SNAPSHOT alone; `status` — "may this be asserted as fact NOW",
`held_at_K` AND the current caps, which only ever SUBTRACT.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .. import gate
from ..schema import (AS_OF_DISPOSITION, FENCED, GROUNDABLE, as_utc_optional,
                      as_utc_required)
from ..semantic import content_digest
from .adapter import adapt
from .carrier import RestrictionVerdict

# the seven statuses the pseudocode returns (closed)
IDENTITY_UNBOUND = "IDENTITY_UNBOUND"
SCOPE_HIDDEN = "SCOPE_HIDDEN"
MALFORMED = "MALFORMED"
NOT_VALID_AT_T = "NOT_VALID_AT_T"
EXCLUDED = "EXCLUDED"
FENCED_AS_OF = "FENCED_AS_OF"
GROUNDED_AS_OF = "GROUNDED_AS_OF"
STATUSES = frozenset({IDENTITY_UNBOUND, SCOPE_HIDDEN, MALFORMED, NOT_VALID_AT_T,
                      EXCLUDED, FENCED_AS_OF, GROUNDED_AS_OF})

STALE_AT_RECALL = "stale-at-recall"       # the only flag named (V-STALE)


@dataclass(frozen=True)
class Result:
    status: str
    held_at_K: Optional[bool]
    flags: frozenset = field(default_factory=frozenset)


def classify_as_of(envelope, snapshot_raw, current_state, T, now, view=None) -> Result:
    # 0. IDENTITY BINDING — SIX legs (snapshot, current_state, envelope, the
    #    view, and the scope cell's PRINCIPAL on both branches), all
    #    row-sourced, all before anything else. Parse-independent (C-2), and
    #    safe ahead of visibility because a binding failure reveals only what
    #    the CALLER supplied.
    if not (snapshot_raw.edge_id == current_state.edge_id == envelope.edge_id
            and snapshot_raw.user_id == current_state.user_id == envelope.user_id):
        return Result(IDENTITY_UNBOUND, held_at_K=None)
    if view is not None and view.user_id != envelope.user_id:
        return Result(IDENTITY_UNBOUND, held_at_K=None)
    # the SCOPE CELL is a leg too (round 5): the cell and the view are a PAIR —
    # present together, absent together, one principal NAMED ON BOTH SIDES and
    # equal. The guard precedes the dereference (round-9 F3 / round-10 F4).
    cell = current_state.scope_cell
    if view is not None:
        if cell is None:
            return Result(IDENTITY_UNBOUND, held_at_K=None)   # view without a cell
        if cell.principal is None or view.principal is None:
            return Result(IDENTITY_UNBOUND, held_at_K=None)
        if cell.principal != (view.principal.origin, view.principal.source_id):
            return Result(IDENTITY_UNBOUND, held_at_K=None)
    elif cell is not None:
        return Result(IDENTITY_UNBOUND, held_at_K=None)   # ANY cell without a view (round-8 F1)

    # 1. THE CURRENT WORLD — a MISSING current row joins the unreadable one:
    #    absence must never GRANT (the subtract-only rule). Believed
    #    unreachable today (rows die only with the whole user, journal
    #    included); stated so a future row-delete is already correct.
    if current_state.current_raw is None:
        return Result(SCOPE_HIDDEN if view is not None else MALFORMED, held_at_K=None)

    # 2. VISIBILITY — the OUTERMOST principal-facing gate (round-1 F7), READ
    #    FROM THE CELL. `fail_closed=True` marks a cell computed from an
    #    unreadable payload: hidden, never a raise (round-5 F2).
    if cell is not None and not cell.visible:
        return Result(SCOPE_HIDDEN, held_at_K=None)

    # 3. PARSE + ADAPT BOTH PAYLOADS through the adapter, which owns schema
    #    validation, enum validation and the DERIVATION of the trust flags.
    snap = adapt(snapshot_raw.state, expect_id=snapshot_raw.edge_id,
                 expect_user=snapshot_raw.user_id)
    cur = adapt(current_state.current_raw, expect_id=current_state.edge_id,
                expect_user=current_state.user_id)
    if cur is None:
        return Result(SCOPE_HIDDEN if view is not None else MALFORMED, held_at_K=None)
    if snap is None:
        return Result(MALFORMED, held_at_K=None)

    # normalization — TOTAL over required inputs (V-NORM-TOTAL), BOTH legs
    # inside the guard (V-NORMALIZE)
    try:
        T = as_utc_required(T)
        now = as_utc_required(now)
        s_vf = as_utc_required(snap.valid_from)
        c_vf = as_utc_required(cur.valid_from)
        s_ia = as_utc_optional(snap.invalidated_at)
        c_ia = as_utc_optional(cur.invalidated_at)
    except (TypeError, ValueError):
        return Result(MALFORMED, held_at_K=None)
    reason = snap.invalidation_reason

    # 4. STATE COHERENCE — structure only, both legs. An unknown-but-well-
    #    formed reason is NOT incoherent (F8b): coherent, and fenced at rule 6.
    def _coherent(ia, r, vf) -> bool:
        if ia is None:
            return r is None
        return r is not None and vf <= ia
    if not (_coherent(s_ia, reason, s_vf)
            and _coherent(c_ia, cur.invalidation_reason, c_vf)):
        return Result(MALFORMED, held_at_K=None)

    # 5. TIME VALIDITY at T over the SNAPSHOT's interval (half-open).
    if not (s_vf <= T and (s_ia is None or T < s_ia)):
        return Result(NOT_VALID_AT_T, held_at_K=False)

    # 6. HELD AT K — snapshot alone. Unknown reason DEFAULTS to FENCED.
    held = (True if s_ia is None
            else AS_OF_DISPOSITION.get(reason, FENCED) == GROUNDABLE)
    held = held and not snap.quarantined and not snap.use_only

    # 7. CURRENT SOURCE RESTRICTION — the standing-state verdict, computed in
    #    the SAME read as `current_raw` (F2). THREE-VALUED (round-5 F2).
    if current_state.source_restricted is RestrictionVerdict.RESTRICTED:
        return Result(EXCLUDED, held_at_K=held)      # 0022 non-revival: any K
    if current_state.source_restricted is RestrictionVerdict.UNDETERMINABLE:
        # FENCED, never EXCLUDED: EXCLUDED uncomputed would ASSERT a
        # revocation never established. Both refuse to ground; only one
        # claims a reason.
        return Result(FENCED_AS_OF, held_at_K=held)

    # 8. SUBTRACTIVE CURRENT PROJECTION — valid-time AND semantic identity.
    if not (c_vf <= T and (c_ia is None or T < c_ia)):
        return Result(FENCED_AS_OF, held_at_K=held)  # current interval ended
    if content_digest(snap) != content_digest(cur):
        return Result(FENCED_AS_OF, held_at_K=held)  # same-id content change

    # 9. REMAINING CURRENT CAPS — subtract only, never grant.
    current_ok = (not cur.quarantined and not cur.use_only
                  and (c_ia is None
                       or AS_OF_DISPOSITION.get(cur.invalidation_reason,
                                                FENCED) == GROUNDABLE))
    if not (held and current_ok):
        return Result(FENCED_AS_OF, held_at_K=held)

    # 10. CURRENT SCOPE SHAPING — on the time-relative verdict, not view.shape().
    if cell is not None and not gate.scoped_assertable(True, (cell.visible, cell.shape)):
        return Result(FENCED_AS_OF, held_at_K=held)  # from the CELL, no live call

    already_stale = (cur.invalidation_reason in ("lapsed", "decayed")
                     and c_ia is not None and c_ia <= now)
    return Result(GROUNDED_AS_OF, held_at_K=True,
                  flags=frozenset({STALE_AT_RECALL}) if already_stale else frozenset())


def assertable_as_of(envelope, snapshot_raw, current_state, T, now, view=None) -> bool:
    return classify_as_of(envelope, snapshot_raw, current_state,
                          T, now, view).status == GROUNDED_AS_OF


__all__ = ["Result", "classify_as_of", "assertable_as_of", "STATUSES",
           "IDENTITY_UNBOUND", "SCOPE_HIDDEN", "MALFORMED", "NOT_VALID_AT_T",
           "EXCLUDED", "FENCED_AS_OF", "GROUNDED_AS_OF", "STALE_AT_RECALL"]
