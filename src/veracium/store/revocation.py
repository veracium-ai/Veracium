"""specs/0022 §4e-i — the R19 revocation operation, against the product store.

The construction is the one the spec prints and the concurrency harness proves
(`specs/evidence/0022/store_concurrency_harness.py`, 18 checks): allocate,
re-read, plan, append the operator's row, APPLY EVERY EFFECT, and commit — or
roll ALL of it back. `BEGIN IMMEDIATE`, never `with conn:` (round 2, R3-1: it
begins nothing); the ordinal from `MAX(seq)` INSIDE the transaction; failure
outcomes TOTAL (round 5, R5-1) with `BaseException` on both boundaries
(round 6, R6-1).

`plan` and `apply_effect` are REQUIRED. Round 4's R4-1 found a version of this
operation that appended the row and never applied the effects — and passed,
because nothing asserted an effect had landed. Making the plan an argument the
operation cannot default away is what makes that defect unrepresentable: the
sweep (0022 §4b) is the production planner, and until it lands nothing else
can call this without saying what the effects are.
"""
from __future__ import annotations

import sqlite3
import time

# The per-user append ordinal's own columns, as SQLite names them in the
# UNIQUE/PK violation message. Matched on BOTH so a UNIQUE or CHECK anywhere
# else — a trigger, a future constraint — cannot masquerade as a
# serialisation failure (R5-1).
_ORDINAL_MARKERS = ("source_revocations.user_id", "source_revocations.seq")


class OrdinalCollision(Exception):
    """The UNIQUE backstop fired. NEVER retried — it means
    allocate-plan-append was not serialised, and retrying hides the defect it
    is reporting."""


class RevocationEffectError(Exception):
    """An effect could not be applied. Rolls back the WHOLE operation — the
    revocation row included — because R19 requires the row and its effects to
    land together or not at all."""


class RevocationIntegrityError(Exception):
    """An integrity constraint OTHER than the ordinal fired (R5-1).
    Mis-classifying a fault is worse than not classifying it: it sends the
    operator to the wrong invariant."""


class RevocationUnknownState(Exception):
    """ROLLBACK ITSELF FAILED, so the transaction's disposition is UNKNOWN
    (R5-1). The connection is CLOSED before this propagates: a connection
    whose transaction state cannot be established must not be reused."""


def _is_ordinal_violation(e: sqlite3.IntegrityError) -> bool:
    msg = str(e)
    return "UNIQUE" in msg.upper() and all(m in msg for m in _ORDINAL_MARKERS)


def _rollback_or_poison(conn, cause):
    """Roll back, or raise RevocationUnknownState and CLOSE the connection.

    BaseException, NOT Exception (R6-1): the operation catches BaseException,
    and the two boundaries must be the SAME boundary or the narrower one is a
    hole in the wider one's guarantee."""
    try:
        conn.execute("ROLLBACK")
    except BaseException as rb:
        try:
            conn.close()
        except BaseException:
            pass
        raise RevocationUnknownState(
            f"ROLLBACK failed after {type(cause).__name__}; the transaction's "
            f"disposition is unknown and the connection is closed") from rb


def standing_revocations(conn, user_id: str) -> frozenset:
    """The standing revoked set: latest row per identity_digest by seq ALONE.

    `at` is host-supplied audit metadata and ORDERS NOTHING (round 1, F2: a
    planted far-future timestamp must not make a revocation permanent — the
    append order is a fact, a clock is an input)."""
    latest: dict = {}
    for digest, action, seq in conn.execute(
            "SELECT identity_digest, action, seq FROM source_revocations "
            "WHERE user_id=? ORDER BY seq", (user_id,)):
        latest[digest] = action                    # seq-ordered: last wins
    return frozenset(d for d, a in latest.items() if a == "revoke")


def revocation_operation(conn, user_id: str, identity_digest: str,
                         action: str, reason: str, at: str, *,
                         plan, apply_effect, busy_deadline_s: float = 5.0,
                         _gate=None, _fault=None):
    """Allocate, re-read, plan, append, APPLY EVERY EFFECT, commit — or roll
    ALL of it back. Returns (seq, standing_before, effects).

    THE SOLE WRITER of `source_revocations` (the R19 product-binding gate
    sweeps for writers and holds each to this construction). `_gate`/`_fault`
    are test hooks, None in every real call; `_fault` fires between the row
    append and the effects — the seam R19's atomicity claim is about."""
    deadline = time.monotonic() + busy_deadline_s
    while True:
        try:
            # EXPLICIT. Not `with conn:` — that begins nothing (R3-1).
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)
            continue                      # contention: re-acquire, RE-READ
        try:
            # the ordinal, from MAX(seq), INSIDE the transaction (R19)
            seq = 1 + (conn.execute(
                "SELECT COALESCE(MAX(seq), -1) FROM source_revocations "
                "WHERE user_id=?", (user_id,)).fetchone()[0])
            standing = standing_revocations(conn, user_id)
            if _gate is not None:
                _gate.wait()
            effects = list(plan(standing))
            conn.execute(
                "INSERT INTO source_revocations(user_id, seq, identity_digest,"
                " action, at, reason) VALUES(?,?,?,?,?,?)",
                (user_id, seq, identity_digest, action, at, reason))
            if _fault is not None:
                _fault()                  # between the row and the effects
            for e in effects:
                apply_effect(conn, e)
            conn.execute("COMMIT")
            return seq, standing, effects
        except sqlite3.IntegrityError as e:
            # WHICH constraint fired decides which invariant reports (R5-1).
            ordinal = _is_ordinal_violation(e)
            _rollback_or_poison(conn, e)
            if ordinal:
                raise OrdinalCollision(str(e)) from e
            raise RevocationIntegrityError(str(e)) from e
        except BaseException as e:
            # the row, the effects, all of it — and if that cannot be
            # established, say so rather than pretending (R5-1)
            _rollback_or_poison(conn, e)
            raise


# ---------------------------------------------------------------------------
# The product adapter (0022 §4e): project the SQLite store into the ported
# computation's store-dict shape, and apply its closed effect vocabulary
# through the store's SOLE writers. All the fidelity risk of the verbatim
# port concentrates HERE, which is why the differential vector test compares
# product and reference over the whole corpus.
# ---------------------------------------------------------------------------

import json as _json

from . import revocation_sweep as _sw


def _iso_z(dt) -> str:
    """Canonical Z-suffixed UTC text. The sweep's recompute folds compare
    timestamps AS STRINGS (the reference's own convention, exercised by the
    corpus), and the ledger payloads already carry Z — a projection emitting
    +00:00 beside them would misorder every mixed comparison, because
    'Z' > '+' lexicographically. One convention, the corpus's."""
    return dt.isoformat().replace("+00:00", "Z")


def _edge_record(e) -> dict:
    from ..schema import EvidenceAuthor
    return {
        "type": "edge", "id": e.id,
        "origin": e.provenance.origin, "source_id": e.provenance.source_id,
        "active": bool(e.active),
        "retired_reason": e.invalidation_reason if not e.active else None,
        "system_authored":
            e.provenance.author_of_evidence == EvidenceAuthor.SYSTEM,
        "valid_from": _iso_z(e.valid_from),
        "observed_at": _iso_z(e.provenance.observed_at),
        "confidence": float(e.provenance.confidence),
        "ungrounded": bool(e.ungrounded),
    }


def _episode_record(ep) -> dict:
    from ..schema import EvidenceAuthor
    return {
        "type": "episode", "id": ep.id,
        "origin": ep.provenance.origin, "source_id": ep.provenance.source_id,
        "active": ep.retired_reason is None,
        "retired_reason": ep.retired_reason,
        "system_authored":
            ep.provenance.author_of_evidence == EvidenceAuthor.SYSTEM,
        # episodes store a DATE; the sweep's shape wants a timestamp. The
        # convention is midnight UTC, and it is exactly representable both
        # ways — the whole corpus uses T00:00:00Z for episode records, and a
        # future vector needing episode time-of-day would be a SHAPE change
        # for Q9's successor carrier, not for this projection to invent.
        "valid_from": f"{ep.date}T00:00:00Z",
        "observed_at": _iso_z(ep.provenance.observed_at),
        "confidence": float(ep.provenance.confidence),
        "ungrounded": False,     # episodes carry no ungrounded flag (0019 is
                                 # an edge-object property; §4b-i's enumeration)
    }


def project_store(store, user_id: str) -> dict:
    """The reference store-dict, read from the live connection. Called INSIDE
    the R19 transaction on the commit path, so the sweep computes over exactly
    the rows the operation will mutate."""
    conn = store._conn
    # RAW reads, not store verbs: this runs INSIDE revoke_source's lock and
    # the R19 transaction, and the store's public verbs re-take the
    # non-reentrant lock — the first version deadlocked on exactly that.
    # Reading the connection directly is also the CORRECT consistency: the
    # sweep must see the rows this transaction will mutate, not a second
    # snapshot.
    from ..schema import Edge as _Edge, Episode as _Episode
    records = [_edge_record(_Edge.model_validate_json(b0))
               for (b0,) in conn.execute(
                   "SELECT json FROM edges WHERE user_id=?", (user_id,))]
    records += [_episode_record(_Episode.model_validate_json(b0))
                for (b0,) in conn.execute(
                    "SELECT json FROM episodes WHERE user_id=?", (user_id,))]
    ledger = []
    for row in conn.execute(
            "SELECT user_id, survivor_type, survivor_id, site, "
            "identity_digest, evidence_ref_digest, payload, op_key, "
            "contributor_type, contributor_ref FROM contribution_ledger "
            "WHERE user_id=?", (user_id,)):
        d = dict(zip(("user_id", "survivor_type", "survivor_id", "site",
                      "identity_digest", "evidence_ref_digest", "payload",
                      "op_key", "contributor_type", "contributor_ref"), row))
        d["payload"] = _json.loads(d["payload"])
        ledger.append(d)
    revs = [dict(zip(("user_id", "seq", "identity_digest", "action", "at",
                      "reason"), r))
            for r in conn.execute(
                "SELECT user_id, seq, identity_digest, action, at, reason "
                "FROM source_revocations WHERE user_id=? ORDER BY seq",
                (user_id,))]
    return {"user_id": user_id, "local_origin": store.local_origin(),
            "records": records, "ledger": ledger, "revocations": revs}


def _apply_statement_effect(store, at, effect: dict) -> None:
    """The CLOSED verb vocabulary, through the store's sole writers. An
    unknown verb REFUSES (the 0004 W5 polarity: the registry can only fail,
    never widen), and refusal rolls back the whole operation (R19)."""
    verb, rtype, rid = effect["verb"], effect["type"], effect["id"]
    if verb == "retire" and rtype == "edge":
        # reason "revoked_source": the seat 0004's registry reserved — the
        # wiki drops through the SOLE active=0 writer, in the same txn
        store._invalidate_edge_row(rid, at, effect["reason"])
    elif verb == "retire" and rtype == "episode":
        store._retire_episode_row(rid, at, effect["reason"])
    elif verb == "reinstate" and rtype == "edge":
        store._reinstate_edge_row(rid)
    elif verb == "reinstate" and rtype == "episode":
        store._reinstate_episode_row(rid)
    elif verb == "recompute" and rtype == "edge":
        store._recompute_edge_row(rid, effect["values"])
    else:
        raise RevocationEffectError(
            f"no applier for effect {verb!r} on {rtype!r} — the vocabulary "
            f"is closed and an unknown verb must refuse, not skip")


def revoke_source(store, user_id: str, target_digest: str, action: str,
                  reason: str, at: str, *, dry_run: bool = False) -> dict:
    """0022 §4e: preview or commit ONE revocation/lift, sweep included.

    Both paths run THE SAME sweep (§4e's one-computation rule, R6's executed
    comparison). `dry_run=True` returns the completeness statement and writes
    nothing; `dry_run=False` appends the row and applies every effect through
    the R19 operation — together or not at all. The statement is RETURNED and
    is audit-event-only (Q6, approved 2026-08-20): the caller's audit sink is
    the durable record; the store keeps no second copy."""
    proposed = {"identity_digest": target_digest, "action": action,
                "at": at, "reason": reason}
    with store._lock:
        if dry_run:
            return _sw.sweep(project_store(store, user_id), target_digest,
                             proposed=proposed)
        statement = {}

        def plan(_standing):
            # INSIDE the R19 transaction: project and sweep over exactly the
            # rows this operation sees and will mutate
            st = _sw.sweep(project_store(store, user_id), target_digest,
                           proposed=proposed)
            statement.update(st)
            return st["effects"]

        # specs/0029 §4a: the effects write `edges` through the store's sole
        # writers, which journal — the allocation scope is THIS operation's
        # (one txn for every effect of one revocation/lift — V-BATCH); the
        # transaction itself is the R19 construction's own BEGIN IMMEDIATE.
        with store._journal_scope():
            revocation_operation(
                store._conn, user_id, target_digest, action, reason, at,
                plan=plan,
                apply_effect=lambda _conn, e: _apply_statement_effect(store, at, e))
        store._bump(user_id)
        store._conn.commit()
        return statement
