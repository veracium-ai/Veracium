"""Seam model — the RESTRICTION DERIVATION, executable (round-3 F1/F2).

Round 3's F1 in one sentence: the derivation was designed by READING the
sweep and wired as `edge_id in statement["retire"]` — but retire's keys are
`(record_type, record_id)` TUPLES over a HETEROGENEOUS population (edges AND
episodes), so the bare-id test was always-False and the cap FAILED OPEN on
the exact cell it exists to close. This model EXECUTES the derivation against
the real `sweep` through the real `project_store` builder (the
share-the-projection rule, executable), and keeps the bare-id mistake as a
negative control so the tuple stays provably load-bearing.

Also here: the CurrentState ONE-CONSISTENT-READ shape (round-3 F2) — row,
standing set, sweep and read token from one transaction — with the
token-moves control (an assertion that fails if a mutator skips the bump).

RULE ZERO (both seats): every assertion ships with a negative control that
makes it fail, in this file.
"""
from __future__ import annotations

from typing import Optional, Tuple

from pydantic import ValidationError

from veracium.store import revocation as rv
from veracium.store.revocation import project_store, standing_revocations
from veracium.store.revocation_sweep import RevocationError, sweep

# THE ONE CARRIER DEFINITION lives in current_state_carrier (round-5 F1 —
# the two-definitions divergence flagged in round 3 and left unfixed cost a
# finding; this import is the fix and the lesson).
from current_state_carrier import CurrentState, RestrictionVerdict, ScopeCell

import json as _json


class ProjectionUnreadable(Exception):
    """PERSISTED DATA cannot be interpreted into a projection (round-6 F3,
    WIDENED by round 7): the contract is not an exception-type list but a
    statement — ANY failure to interpret persisted rows, payloads, or
    revocation records becomes this wrapper; a failure of our own logic
    still propagates. Round 6 enumerated three decode families and round 7
    found the family wider (an invalid-UTF-8 ledger payload raises
    UnicodeDecodeError before json ever runs; a corrupted persisted
    revocation row raises RevocationError from the SWEEP's own
    validation). Enumerations of failure modes under-count; the boundary
    is defined by WHAT WAS BEING READ, and at this call site every input
    is persisted."""


def _build_projection(store, user_id: str):
    try:
        return project_store(store, user_id)
    except (ValidationError, _json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ProjectionUnreadable(str(e)[:200]) from e


def source_restricted(store, user_id: str, edge_id: str) -> RestrictionVerdict:
    """The 0030 §4b-iii derivation, corrected THREE times and EXECUTED.

    ONE sweep call (X-1: retire is computed against the WHOLE standing set,
    so any standing digest yields the same desired state); membership is
    `("edge", edge_id)` because the population SPANS RECORD TYPES — a bare
    id is always absent, and a cast could match an episode's id (round-3 F1).
    The NO-STANDING case is a defined outcome, not a fall-through: no
    restriction, ZERO sweep calls.

    RETURNS A THREE-VALUED VERDICT (round-4 F4 -> round-5 F2): the one
    collective sweep proves membership under the WHOLE standing set — a
    boolean already replaced the false per-digest attribution, and round 5
    forced the third value: `project_store` validates EVERY row
    (revocation.py:217), so over a store containing a malformed row the
    projection CANNOT BE BUILT and both `clear` and `restricted` would be
    fabrications. `UNDETERMINABLE` is RETURNED, never raised — caught at
    exactly the projection boundary and nowhere wider — and the classifier
    maps it to FENCED_AS_OF, NEVER EXCLUDED (EXCLUDED uncomputed would
    assert a revocation never established).
    """
    standing = standing_revocations(store._conn, user_id)
    if not standing:
        return RestrictionVerdict.CLEAR          # defined outcome, zero sweeps
    d = sorted(standing)[0]                      # any standing digest works
    try:
        statement = sweep(_build_projection(store, user_id), d)
    except (ProjectionUnreadable, RevocationError):
        # RevocationError HERE is a persisted-data failure, not an argument
        # bug: every input to this sweep call — the projection's rows, the
        # revocation records, the standing digest itself — derives from
        # persisted store state, so the sweep refusing to validate them is
        # the store being unreadable (round-7 F2's second family). At any
        # OTHER call site RevocationError may mean caller error and must
        # not be swallowed; the narrowness control still proves a
        # non-persisted-data failure (RuntimeError) propagates.
        return RestrictionVerdict.UNDETERMINABLE
    if ("edge", edge_id) in set(statement["retire"]):
        return RestrictionVerdict.RESTRICTED
    return RestrictionVerdict.CLEAR


def current_state(store, user_id: str, edge_id: str, principal=None,
                  policy=None, _interleave=None) -> CurrentState:
    """Row + standing set + sweep + token + SCOPE CELL from ONE explicit
    read transaction under the store lock (round-4 F1).

    Round 3 claimed "single connection => one world BY CONSTRUCTION" — the
    reviewer executed the refutation: under AUTOCOMMIT each SELECT is its
    own snapshot, and a second store instance can commit between them (see
    `autocommit_variant`, kept as the negative control). The construction
    is now made TRUE instead of abandoned: `BEGIN` opens a read
    transaction, so every read below — token, row, projection, sweep, and
    the ScopeView's LAZY contribution-ledger reads (which fire during
    visible()/decision(), the round-4 half of the finding) — lands inside
    ONE SQLite read window. THE PROPERTY IS MODE-NEUTRAL AND THE
    MECHANISM IS NOT (round-5 F3 — "writers refused, not a snapshot" was
    the THIRD wrong mechanism statement in this family): the guaranteed
    property is ONE WORLD PER WINDOW — every value carried out describes
    the same database state. In rollback-journal mode the window holds a
    SHARED lock and a concurrent writer is REFUSED for its duration; in
    WAL mode the writer PROCEEDS and the reader keeps its SNAPSHOT —
    different mechanisms, same property, and the interleaving test
    asserts the property in BOTH modes plus each mode's specific
    mechanism. The store's instance lock is held too, so a same-instance
    thread cannot inject DML into this transaction (same connection =
    same transaction in sqlite3).

    `principal`/`policy`: option (a) of the round-4 fix — when given, the
    scope decision is computed HERE, inside the transaction, and carried;
    the classifier consumes the cell and never triggers a post-hoc lazy
    read. `_interleave`: test hook, called immediately BEFORE the scope
    decision — the reviewer's required interleaving point.
    """
    conn = store._conn
    with store._lock:
        conn.execute("BEGIN")
        try:
            tok = conn.execute(
                "SELECT COALESCE(n, 0) FROM write_counter WHERE user_id=?",
                (user_id,)).fetchone()
            row = conn.execute(
                "SELECT json FROM edges WHERE user_id=? AND id=?",
                (user_id, edge_id)).fetchone()
            restricted = source_restricted(store, user_id, edge_id)
            scope_cell = None
            if principal is not None and row is not None:
                if _interleave is not None:
                    _interleave()          # the round-4 interleaving point
                # Round-5 F2: the scope record comes from the ADAPTER, never
                # Edge.model_validate_json — a malformed row must yield the
                # FAIL-CLOSED HIDDEN cell, not a ValidationError. The raise
                # the reviewer executed (source_id=[] + principal) dies here.
                from raw_adapter import adapt
                from veracium.scope_read import ScopeView
                adapted = adapt(row[0], expect_id=edge_id, expect_user=user_id)
                # The cell states WHO it was computed for (round-5, research's
                # principal bind — C-4's pattern made predictive: a fix that
                # reassigns authority creates a new pair that nothing binds;
                # rule 0 checks this against the envelope's principal).
                who = (principal.origin, principal.source_id)
                if adapted is None:
                    scope_cell = ScopeCell(visible=False, shape=None,
                                           fail_closed=True, principal=who)
                else:
                    view = ScopeView(store, user_id, principal, policy)
                    # ROUND-6 F1: decision() ALREADY returns (visible, shape)
                    # — its docstring says so (scope_read.py:328-330). The
                    # previous fill stored the WHOLE PAIR into .shape, so the
                    # classifier's (cell.visible, cell.shape) double-wrapped
                    # and the reviewer's cross-visible probe GROUNDED off the
                    # carried cell where the direct decision refused. One
                    # decomposition, at the fill site, and the separate
                    # visible() call drops (it is the pair's first element).
                    vis, shape = view.decision(adapted)
                    scope_cell = ScopeCell(visible=vis, shape=shape,
                                           principal=who)
        finally:
            conn.execute("COMMIT")
    return CurrentState(
        user_id=user_id, edge_id=edge_id,
        current_raw=None if row is None else row[0],
        source_restricted=restricted,
        read_token=0 if tok is None else int(tok[0]),
        scope_cell=scope_cell,
    )


def autocommit_variant(store, user_id: str, edge_id: str,
                       between=None) -> CurrentState:
    """THE ROUND-3 DESIGN, kept as the negative control: consecutive
    autocommit reads, no BEGIN, no lock. `between` lets the driver commit a
    foreign write between the token read and the row read — the reviewer's
    exact reproduction, made repeatable."""
    tok = store._conn.execute(
        "SELECT COALESCE(n, 0) FROM write_counter WHERE user_id=?",
        (user_id,)).fetchone()
    if between is not None:
        between()
    row = store._conn.execute(
        "SELECT json FROM edges WHERE user_id=? AND id=?",
        (user_id, edge_id)).fetchone()
    return CurrentState(
        user_id=user_id, edge_id=edge_id,
        current_raw=None if row is None else row[0],
        source_restricted=source_restricted(store, user_id, edge_id),
        read_token=0 if tok is None else int(tok[0]),
        scope_cell=None,
    )


# --------------------------------------------------------------------------
# NEGATIVE CONTROLS
# --------------------------------------------------------------------------

def control_bare_id_fails_open(store, user_id: str, edge_id: str) -> bool:
    """ROUND-3 F1, kept as a permanent regression: the bare-id membership
    MISSES a genuinely restricted edge. True means the mistake still fails
    open — i.e. the tuple key is load-bearing, not stylistic."""
    standing = standing_revocations(store._conn, user_id)
    if not standing:
        return False
    d = sorted(standing)[0]
    statement = sweep(project_store(store, user_id), d)
    retire = set(statement["retire"])
    return (("edge", edge_id) in retire) and (edge_id not in retire)


def control_affected_misses_the_direct_case(store, user_id: str,
                                            edge_id: str) -> bool:
    """X-1's live demonstration (research executed it first): an edge whose
    OWN source is revoked lands in `direct`/`retire` and can be ABSENT from
    `affected` — so the earlier affected-membership design failed open too.
    True means retire catches what affected misses."""
    standing = standing_revocations(store._conn, user_id)
    if not standing:
        return False
    d = sorted(standing)[0]
    st = sweep(project_store(store, user_id), d)
    key: Tuple[str, str] = ("edge", edge_id)
    return key in set(st["retire"]) and key not in set(st["affected"])


def control_token_moves_on_mutation(store, user_id: str, edge_id: str,
                                    mutate) -> bool:
    """The read token must ADVANCE whenever the user's current state can
    change (a V-TOTAL-shaped requirement on the implementation). `mutate` is
    any store mutation for the user. True means the token moved — an
    assertion that FAILS if a mutator skips the write-counter bump."""
    before = current_state(store, user_id, edge_id).read_token
    mutate()
    after = current_state(store, user_id, edge_id).read_token
    return after > before


def control_lift_flips_with_no_row_rewrite(store, user_id: str,
                                           edge_id: str, at: str) -> bool:
    """V-TRUST-INPUT's free cell: restricted while standing, clear after the
    LIFT — with the edge ROW never rewritten (its reason is untouched;
    history never rewrites). True means the input flips while the row's
    bytes stand still."""
    row_before = store._conn.execute(
        "SELECT json FROM edges WHERE user_id=? AND id=?",
        (user_id, edge_id)).fetchone()[0]
    restricted_before = source_restricted(store, user_id, edge_id)
    for d in sorted(standing_revocations(store._conn, user_id)):
        rv.revoke_source(store, user_id, d, "lift", "seam-model", at)
    restricted_after = source_restricted(store, user_id, edge_id)
    row_after = store._conn.execute(
        "SELECT json FROM edges WHERE user_id=? AND id=?",
        (user_id, edge_id)).fetchone()[0]
    return (restricted_before is RestrictionVerdict.RESTRICTED
            and restricted_after is RestrictionVerdict.CLEAR
            and row_before == row_after)
