"""specs/0030 §4a-i — the store-side derivation of `CurrentState`: row,
standing set, ONE collective sweep, read token and the scope cell, all read
INSIDE ONE READ WINDOW THE CALLER OWNS. Lifted from the seam model's
`restriction_derivation.py` (rounds 3–8: the retire/affected correction, the
`("edge", id)` typed key over a heterogeneous population, the three-valued
verdict returned-not-raised, the region-total projection boundary, the
in-window scope cell) under the co-check's TRANSACTION OWNERSHIP CONTRACT:
nothing here issues BEGIN — `SqliteStore.current_state` opens the window (the
store method beside `edge_events`/`edge_state_at`); 0028 v2's single-snapshot
read that also owns `now` is the other legitimate caller. Lives in the store
package because it reads the connection; nothing outside the package does.
"""
from __future__ import annotations

import sqlite3

from ..asof.adapter import adapt
from ..asof.carrier import CurrentState, RestrictionVerdict, ScopeCell
from .revocation import project_store, standing_revocations
from .revocation_sweep import RevocationError, sweep


class ProjectionUnreadable(Exception):
    """PERSISTED DATA cannot be interpreted into a projection — a REGION, not
    a type list (round 8: the enumerated families under-counted every
    round). `project_store`'s sole job is interpreting persisted bytes, so
    within that call ANY Exception is "the store cannot be read"; failures
    OUTSIDE the region still propagate."""


class NoOpenReadWindow(RuntimeError):
    """The derivation was called outside an open transaction: the caller owns
    the window (the ownership contract), so this is a programming error, not
    a store state."""


def _build_projection(store, user_id: str):
    try:
        return project_store(store, user_id)
    except Exception as e:                      # REGION-TOTAL, deliberately
        raise ProjectionUnreadable(f"{type(e).__name__}: {str(e)[:200]}") from e


def _standing(store, user_id: str) -> frozenset:
    """The standing set, read under the SAME region argument as the projection
    (research's post-merge Q1: two adjacent boundaries in one function, one
    argued and one asserted). `standing_revocations` both PERFORMS the SELECT
    and interprets the rows, so what a net here catches is operational
    unreadability (a closed connection, a missing table) as well as
    uninterpretable persisted values (a BLOB digest that makes `min()` raise).
    Both are the same epistemic state for THIS derivation — the standing state
    cannot be established, so neither `clear` nor `restricted` can be honestly
    computed — and the spec's rule for the path holds for both: refuse to
    ground, never raise (§4a-i: "a raise in this path is the one indefensible
    outcome"). An operational failure is therefore NOT surfaced from here; it
    lands in UNDETERMINABLE → FENCED_AS_OF like the projection's, and a
    consumer that must distinguish them reads the store directly.

    WHAT KEEPS THE COLLAPSE HONEST (research, post-merge): the derivation's
    token and row reads in `derive_current_state` are UNWRAPPED and run
    BEFORE this — a closed connection, a missing `edges` table, any
    store-wide failure raises there and propagates. So the net here can only
    catch failures specific to the revocation tables: LOCAL unreadability
    fences, SYSTEMIC unreadability surfaces. Wrapping those two reads "to make
    the derivation total" would silently remove the surfacing path while this
    docstring still read true; `test_systemic_unreadability_surfaces_not_fences`
    pins the dependency."""
    try:
        standing = standing_revocations(store._conn, user_id)
        if standing:
            min(standing)                       # orders persisted digests: mixed types raise
        return standing
    except Exception as e:
        raise ProjectionUnreadable(f"{type(e).__name__}: {str(e)[:200]}") from e


def source_restricted(store, user_id: str, edge_id: str) -> RestrictionVerdict:
    """§4a-i's derivation, EXECUTED: ONE sweep call against the WHOLE standing
    set; membership is `("edge", edge_id)` in `statement["retire"]` — the
    population SPANS record types, so a bare id is always absent (round-3 F1)
    and `affected` is target-scoped (X-1). NO-STANDING is a DEFINED outcome
    with zero sweep calls. UNDETERMINABLE is RETURNED, never raised, at the
    projection boundary and nowhere wider."""
    try:
        standing = _standing(store, user_id)
    except ProjectionUnreadable:
        return RestrictionVerdict.UNDETERMINABLE
    if not standing:
        return RestrictionVerdict.CLEAR
    d = min(standing)                           # any standing digest works
    try:
        statement = sweep(_build_projection(store, user_id), d)
    except (ProjectionUnreadable, RevocationError):
        return RestrictionVerdict.UNDETERMINABLE
    if ("edge", edge_id) in set(statement["retire"]):
        return RestrictionVerdict.RESTRICTED
    return RestrictionVerdict.CLEAR


def derive_current_state(store, user_id: str, edge_id: str, *, principal=None,
                         policy=None) -> CurrentState:
    """Everything the carrier holds, from the window the CALLER opened. The
    scope cell is computed HERE, in-window, from the ADAPTER's record (never
    `Edge.model_validate_json`: a malformed row yields the FAIL-CLOSED HIDDEN
    cell, not a ValidationError) and states WHO it was computed for."""
    conn: sqlite3.Connection = store._conn
    if not conn.in_transaction:
        raise NoOpenReadWindow(
            "derive_current_state requires the caller's open read window "
            "(specs/0030 §4a-i one-consistent-read; the ownership contract)")
    tok = conn.execute(
        "SELECT COALESCE(n, 0) FROM write_counter WHERE user_id=?", (user_id,)).fetchone()
    row = conn.execute(
        "SELECT json FROM edges WHERE user_id=? AND id=?", (user_id, edge_id)).fetchone()
    restricted = source_restricted(store, user_id, edge_id)
    scope_cell = None
    if principal is not None and row is not None:
        from ..scope_read import ScopeView
        adapted = adapt(row[0], expect_id=edge_id, expect_user=user_id)
        who = (principal.origin, principal.source_id)
        if adapted is None:
            scope_cell = ScopeCell(visible=False, shape=None, fail_closed=True, principal=who)
        else:
            view = ScopeView(store, user_id, principal, policy)
            vis, shape = view.decision(adapted)      # ONE decomposition (round-6 F1)
            scope_cell = ScopeCell(visible=vis, shape=shape, principal=who)
    return CurrentState(
        user_id=user_id, edge_id=edge_id,
        current_raw=None if row is None else row[0],
        source_restricted=restricted,
        read_token=0 if tok is None else int(tok[0]),
        scope_cell=scope_cell,
    )
