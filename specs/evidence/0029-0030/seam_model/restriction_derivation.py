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

from dataclasses import dataclass
from typing import FrozenSet, Optional, Tuple

from veracium.store import revocation as rv
from veracium.store.revocation import project_store, standing_revocations
from veracium.store.revocation_sweep import sweep


def source_restricted(store, user_id: str, edge_id: str) -> FrozenSet[str]:
    """The 0030 §4b-iii derivation, corrected twice and now EXECUTED.

    ONE sweep call (X-1: retire is computed against the WHOLE standing set,
    so any standing digest yields the same desired state); membership is
    `("edge", edge_id)` because the population SPANS RECORD TYPES — a bare
    id is always absent, and a cast could match an episode's id (round-3 F1).
    The NO-STANDING case is a defined outcome, not a fall-through: no
    restriction, ZERO sweep calls.
    """
    standing = standing_revocations(store._conn, user_id)
    if not standing:
        return frozenset()
    d = sorted(standing)[0]                      # any standing digest works
    statement = sweep(project_store(store, user_id), d)
    if ("edge", edge_id) in set(statement["retire"]):
        return frozenset(standing)
    return frozenset()


@dataclass(frozen=True)
class CurrentState:
    """Round-3 F2: the bound, one-consistent-read current carrier.

    REPLACES the separate current_raw parameter — there is no second current
    read to be stale against. `current_raw is None` is defensive totality
    (rows die only with the whole user, journal included — forget_user's
    table loop is the single edges DELETE, sqlite.py:1753/:1776).
    """
    user_id: str
    edge_id: str
    current_raw: Optional[str]
    source_restricted: FrozenSet[str]
    read_token: int


def current_state(store, user_id: str, edge_id: str) -> CurrentState:
    """Row + standing set + sweep + token from ONE connection, one snapshot.

    The store is single-connection, so consecutive reads with no interleaved
    writer on the same connection see one world; the model states the
    requirement the implementation must keep (one read transaction) and
    executes the derivation through the SAME projection builder the shipped
    revoke_source uses — the share-the-projection rule.
    """
    tok = store._conn.execute(
        "SELECT COALESCE(n, 0) FROM write_counter WHERE user_id=?",
        (user_id,)).fetchone()
    row = store._conn.execute(
        "SELECT json FROM edges WHERE user_id=? AND id=?",
        (user_id, edge_id)).fetchone()
    return CurrentState(
        user_id=user_id, edge_id=edge_id,
        current_raw=None if row is None else row[0],
        source_restricted=source_restricted(store, user_id, edge_id),
        read_token=0 if tok is None else int(tok[0]),
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
    restricted_before = bool(source_restricted(store, user_id, edge_id))
    for d in sorted(standing_revocations(store._conn, user_id)):
        rv.revoke_source(store, user_id, d, "lift", "seam-model", at)
    restricted_after = bool(source_restricted(store, user_id, edge_id))
    row_after = store._conn.execute(
        "SELECT json FROM edges WHERE user_id=? AND id=?",
        (user_id, edge_id)).fetchone()[0]
    return (restricted_before and not restricted_after
            and row_before == row_after)
