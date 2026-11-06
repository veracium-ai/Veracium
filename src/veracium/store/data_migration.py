"""specs/0018 §4i — the per-user data-migration operation (the folded amendment `0044/0018-data-migration`), for
specs/0044's restoration of the rows the superseded single-value rule retired. OPTIONAL (the owner, 2026-10-11): a v16
store opens normally; until this runs, those values stay hidden and `doctor` warns.

  run_data_migration(path, *, host_attestation, registry, op_id, plan_only=False) -> DataMigrationResult
      §4b. The plan once per store (ONE write transaction: admission, header, relation rows), then ONE `BEGIN
      IMMEDIATE` transaction per user (eligibility evaluated under the lock, restorations, outcome rows and the run
      row together — I26), continuing past a failing user (D1), idempotent on re-call (I27).
  data_migration_status(path, op_id) -> DataMigrationStatus
      §4c's recovery read after an unknown return: the operation's CUMULATIVE durable commits (I32).
  data_migration_receipt(path, plan_id, user_id) -> tuple[ReceiptRow, ...]
      §4d / 0044 §4g: a view over one user's outcome rows; object text read from the LIVE edge at call time.
  undo_restoration(store, user_id, edge_id, correlation_id) -> dict
      0044 §4i (with research's T7 annotation): the body of `SqliteStore.undo_restoration`, run inside its write
      transaction — the registry verb `undo`, decided before any read of the edge; eligibility from the outcome row
      and its `applicable` episode flag; the per-field restore through the invalidate method.

THE PER-USER UNIVERSE (0018 §4i's research annotation, 2026-10-16; dev's T6 build note Q2): the users holding at least
one `arity_inventory` row, read at the call and RE-CHECKED inside each user's transaction, so a user erased between
the two reads gets no run row (§4g-ii). Only an inventoried row can be restored, so a user created at v16 needs no
run row and `doctor` never warns for it.

REUSED, never re-implemented: 0018's attestation check and its read-only preflight classification
(`release_migration`), 0025's registry validator (`registry.effective_registry`), 0008 §6c's caller grammar
(`schema.validate_correlation_id`), the revocation sweep's own predicate (`revocation.would_retire_if_active`), the
lifetime equality test (`lifetime.same_retirement`), and 0022's reinstate writer — so the restoration passes 0029's
choke point, where the T5-2 lifetime hook ends the row's inventory membership and the journal records `reinstated`
with the reason `arity_reclassified`.

Successor evidence is scanned within the user (`edges.user_id`); the reference model scans the store. The two are
identical while `supersedes` names an edge of the same user, which every writer at this pin guarantees (a
supersession pairs two edges of one subject's user).
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from collections.abc import Mapping
from typing import NamedTuple, Optional

from . import lifetime as _lifetime
from . import release_migration as _rm
from . import revocation as _revocation
from . import schema_version as sv
from ..census import declare_site
from .base import UndoRefused
from ..redaction import edge_carries_marker
from ..registry import declared_arity, effective_registry

# specs/0042: this module's enforcement points (research's T6 classification, a7d1a64a — each refuses or withholds
# what the caller asked for, enforcing a stated guarantee), each a declared site the decision is returned THROUGH
_SITE_OP_ID_CONFLICT = declare_site("store.data-migration.op-id-conflict")          # 0018 §4i I32
_SITE_REGISTRY_CHANGED = declare_site("store.data-migration.registry-changed")      # 0018 §4i I25
_SITE_WITHHELD_REVOKED = declare_site("store.data-migration.withheld-revoked")      # 0044 §4f.2, INV-A11
_SITE_REDACTED_NOT_CONSIDERED = declare_site("store.data-migration.redacted-not-considered",
                                             declines=True)                         # 0044 §4f.1, INV-A7
_SITE_INVENTORY_INTEGRITY = declare_site("store.data-migration.inventory-integrity")  # 0018 §4i D1, T6 S2 F5
_SITE_READ_REFUSED = declare_site("store.data-migration.read-refused")              # 0018 §4i §4c/§4d
# T7 (0044 §4i, undo; research's T7 stage-1 classification f8ec28ed — each refuses the undo the caller asked for)
_SITE_UNDO_AMBIGUOUS = declare_site("store.undo.ambiguous-outcome")                 # 0044 §4i annotation (T7)
_SITE_UNDO_REQUEST_DIGEST = declare_site("store.undo.request-digest")               # 0008 §6c C9
_SITE_UNDO_RESULT_MISSING = declare_site("store.undo.result-missing")               # 0008 §6c v7
_SITE_UNDO_NO_OUTCOME = declare_site("store.undo.no-outcome")                       # 0044 §4i.2, INV-A12
_SITE_UNDO_NOT_RESTORED = declare_site("store.undo.not-restored")                   # 0044 §4i.2, INV-A12
_SITE_UNDO_TESTIMONY = declare_site("store.undo.testimony")                         # 0044 §4i.2 R2-05, INV-A17
_SITE_UNDO_NOT_APPLICABLE = declare_site("store.undo.not-applicable")               # 0044 §4i.2, INV-A12
_SITE_UNDO_EDGE_UNAVAILABLE = declare_site("store.undo.edge-unavailable")           # 0044 §4i.2
_SITE_UNDO_CORRELATION = declare_site("store.undo.correlation")                     # 0008 §6c C8/C9

# specs/0044 §4b: the three relations the plan can reclassify, and the declaration that is "canonically the default"
# (§4e): arity only (research's T6 read, Q4), so a host's gloss edit neither drops a name from the plan nor moves the
# digest. A name absent from the host's registry is not the default.
PLAN_RELATIONS = tuple(sorted(_lifetime.RECLASSIFIED_RELATIONS))
DEFAULT_ARITY = "multi"
NO_LONGER_HELD = "no longer held"

# §4c's ten outcomes, with the store_changed each fixes (None: `failed`, whose store_changed IS plan_written)
OUTCOMES = {
    "requires-schema-step": False,
    "preflight-refused": False,
    "registry-changed": False,
    "op-id-conflict": False,
    "planned": True,
    "already-planned": False,
    "complete": False,
    "migrated": True,
    "partial": True,
    "failed": None,
}
_NO_PLAN_WRITE = frozenset({"requires-schema-step", "preflight-refused", "registry-changed", "op-id-conflict",
                            "already-planned", "complete"})
# row 9 (research's T6 read, the BLOCKING rewording of Q3): plan_id is stated per outcome, never "iff a header exists"
_WITH_PLAN_ID = frozenset({"planned", "already-planned", "complete", "migrated", "partial", "failed",
                           "registry-changed"})


class _DataMigrationResultBase(NamedTuple):
    outcome: str
    store_changed: bool
    plan_written: bool
    committed: tuple
    failed: tuple
    op_id: str
    plan_id: Optional[str]
    diagnostic: str


def _users_ok(v) -> bool:
    return type(v) is tuple and all(type(u) is str and u for u in v) and len(set(v)) == len(v)


def data_migration_result_problems(outcome, store_changed, plan_written, committed, failed, op_id, plan_id,
                                   diagnostic) -> list:
    """§4c's rejection matrix, ROW BY ROW, each refusal naming its row (rows 1–8 are the spec's; row 9 is the
    research-ruled `plan_id` row; `diagnostic` is text outside the matrix, as `MigrationResult.diagnostic` is)."""
    if type(outcome) is not str or outcome not in OUTCOMES:
        return [f"row 1: outcome {outcome!r} is not a row of §4c"]
    p = []
    if type(store_changed) is not bool or type(plan_written) is not bool or not _users_ok(committed) \
            or not _users_ok(failed) or type(diagnostic) is not str:
        return ["row 2: a field missing or of the wrong type (store_changed and plan_written exact bools, committed "
                "and failed tuples of distinct user ids, diagnostic a str)"]
    if store_changed != (plan_written or bool(committed)):
        p.append("row 3: store_changed ≠ (plan_written ∨ committed ≠ ∅)")
    if (outcome in ("partial", "failed")) != bool(failed):
        p.append(f"row 4: `failed` is {'empty' if not failed else 'non-empty'} on {outcome!r}")
    if (outcome in ("migrated", "partial")) != bool(committed):
        p.append(f"row 5: `committed` is {'empty' if not committed else 'non-empty'} on {outcome!r}")
    if set(committed) & set(failed):
        p.append("row 6: a user both committed and failed")
    if (plan_written and outcome in _NO_PLAN_WRITE) or (not plan_written and outcome == "planned"):
        p.append(f"row 7: plan_written={plan_written} on {outcome!r}")
    if type(op_id) is not str or not _caller_key(op_id):
        p.append("row 8: op_id outside §6c's caller grammar")
    if outcome in _WITH_PLAN_ID:
        if type(plan_id) is not str or not plan_id:
            p.append(f"row 9: {outcome!r} carries the store's plan_id")
    elif plan_id is not None:
        p.append(f"row 9: {outcome!r} carries no plan_id")
    want = OUTCOMES[outcome]
    if want is not None and store_changed is not want:
        p.append(f"row 3: {outcome!r} fixes store_changed={want}")
    return p


class DataMigrationResult(_DataMigrationResultBase):
    """§4c's TOTAL, closed carrier (I29). The validating constructor rejects every carrier outside the table;
    `store_changed` is DEFINED as "this call changed durable state" (a written header, or >=1 committed user) and is
    never inferred from the outcome's name. `committed` names the users THIS invocation committed;
    `data_migration_status` returns the operation's cumulative commits."""
    __slots__ = ()

    def __new__(cls, outcome, store_changed, plan_written, committed, failed, op_id, plan_id, diagnostic):
        problems = data_migration_result_problems(outcome, store_changed, plan_written, committed, failed, op_id,
                                                  plan_id, diagnostic)
        if problems:
            raise ValueError("DataMigrationResult outside specs/0018 §4c: " + "; ".join(problems))
        return super().__new__(cls, outcome, store_changed, plan_written, committed, failed, op_id, plan_id,
                               diagnostic)


class DataMigrationStatus(NamedTuple):
    """§4c's recovery read: `outcome` is `known` or `unknown-op` (no admission record holds the id); for a known op,
    whether it wrote the plan header and the users its run rows name, over EVERY invocation under the id."""
    outcome: str
    plan_written_by_op: bool
    committed: tuple


class ReceiptRow(NamedTuple):
    """One considered row of 0044 §4g's receipt. `replaced_by` is None when no edge names this one in `supersedes`
    (rendered "replaced by: unknown"); `object` is the LIVE edge's object text (a redacted edge shows the marker),
    or "no longer held" from the outcome row alone."""
    edge_id: str
    outcome: str
    pre_invalidated_at: str
    pre_reason: str
    replaced_by: Optional[tuple]
    object: str
    applicable: bool
    undone_at: Optional[str]
    origin: str


def _caller_key(op_id) -> bool:
    from ..schema import validate_correlation_id
    try:
        validate_correlation_id(op_id)
    except ValueError:
        return False
    return True


def portable_uid(*parts) -> str:
    """specs/0008 §6e's canonical identity encoding: a JSON array of strings (UTF-8, no whitespace) hashed, never a
    separator join, so no two distinct tuples share a key. 0044 §4g's `outcome_uid` is `(origin_store, origin_user,
    plan_id, edge_ref)`."""
    return hashlib.sha256(json.dumps([str(p) for p in parts], ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def plan_input_digest(eff) -> str:
    """§4b.2 (D2, I25): a digest of the plan's INPUTS only — the declared arity of each of the three reclassified
    relations (an absent name as null) — so an unrelated registry edit never trips `registry-changed`."""
    return _sha([[name, declared_arity(eff[name]) if name in eff else None] for name in PLAN_RELATIONS])


def plan_relations(eff) -> tuple:
    """0044 §4e: a relation enters the plan only if its effective declaration is canonically the default."""
    return tuple(n for n in PLAN_RELATIONS if n in eff and declared_arity(eff[n]) == DEFAULT_ARITY)


def inputs_digest(plan_digest: str, mode: str) -> str:
    """§4b.1b: the canonical digest of the operation's inputs — the plan-input digest and the mode. The attestation is
    not an input: a resume legitimately carries a fresh one."""
    return portable_uid(plan_digest, mode)


def _result(outcome, *, plan_written=False, committed=(), failed=(), op_id, plan_id=None, diagnostic=""):
    changed = plan_written or bool(committed)
    return DataMigrationResult(outcome, changed, plan_written, tuple(committed), tuple(failed), op_id,
                               plan_id, diagnostic)


class _Refusal(Exception):
    """Unwinds a write transaction with an outcome of §4c's table (nothing this transaction wrote is kept)."""

    def __init__(self, outcome: str, diagnostic: str, plan_id: Optional[str] = None):
        super().__init__(diagnostic)
        self.outcome, self.diagnostic, self.plan_id = outcome, diagnostic, plan_id


def _preflight(path, op_id):
    """§4b.1: the shared read-only classification, 0018's cells. Returns (canonical_path, None) to proceed, or
    (None, DataMigrationResult) for a refusal. `PackageConsistencyError` propagates bare (a defect outside a per-user
    transaction raises — research's T6 read, Q5: §4c has no internal-error row)."""
    if not _rm._usable_store_path(path):
        return None, _result("preflight-refused", op_id=op_id,
                             diagnostic=f"path {_rm._safe_repr(path)} is not a usable store path")
    kind, payload = _rm._preflight_classify(path)
    if kind == "intercept":
        if payload.outcome == "current":
            return os.path.realpath(path), None
        if payload.outcome == "unsupported-base":
            return None, _result("requires-schema-step", op_id=op_id,
                                 diagnostic=f"the store is below v{sv.SCHEMA_VERSION}: {payload.diagnostic}")
        return None, _result("preflight-refused", op_id=op_id,
                             diagnostic=f"{payload.outcome}: {payload.diagnostic}")
    if kind == "mint":
        return None, _result("requires-schema-step", op_id=op_id,
                             diagnostic=f"the store is at v{payload.resolved_base}, below v{sv.SCHEMA_VERSION}: run "
                                        f"the schema walk first (`veracium migrate`, or migrate_store)")
    # kind == "repair": research's T6 read, Q1 — the repair would be a durable change §4c's store_changed does not
    # define, so this operation refuses rather than repairing silently
    return None, _result("preflight-refused", op_id=op_id,
                         diagnostic=f"rebuildable drift at v{sv.SCHEMA_VERSION}: open the store once (the 0007 "
                                    f"§4a-iii repair-during-opening) and re-run")


def run_data_migration(path, *, host_attestation, registry, op_id, plan_only=False) -> DataMigrationResult:
    """specs/0018 §4i.6 §4b. See the module docstring. `op_id` outside 0008 §6c's caller grammar RAISES `ValueError`
    at entry, before any read, with no result constructed (I32); so does a `plan_only` that is not exactly a `bool`
    (`1`, `"yes"`, `None`: a caller-type error, not a store outcome, so §4c has no row for it — research's T6 stage-2
    N2). Every other refusal is a row of §4c, a path that does not encode included (N1)."""
    from ..schema import validate_correlation_id
    validate_correlation_id(op_id)
    if type(plan_only) is not bool:
        raise ValueError(f"plan_only must be a bool, not {plan_only!r}")
    ap = _rm._attestation_problems(host_attestation)
    if ap:
        return _result("preflight-refused", op_id=op_id, diagnostic="host_attestation refused: " + "; ".join(ap))
    canonical, refused = _preflight(path, op_id)
    if refused is not None:
        return refused
    try:
        if not isinstance(registry, Mapping):
            raise ValueError(f"registry must be the host's relation registry (a mapping of name to Relation), not "
                             f"{type(registry).__name__}")
        eff = effective_registry(registry)
    except ValueError as x:                         # RegistryError is a ValueError
        return _result("preflight-refused", op_id=op_id, diagnostic=f"registry refused (specs/0025): {x}")
    mode = "plan_only" if plan_only else "restore"
    digest = plan_input_digest(eff)
    admission = (op_id, mode, inputs_digest(digest, mode))
    from .sqlite import SqliteStore
    store = SqliteStore(canonical)
    try:
        return _run(store, eff, digest, admission, plan_only)
    finally:
        store.close()


def _held_admission(conn, op_id):
    return conn.execute("SELECT mode, inputs_digest FROM migration_op WHERE op_id=?", (op_id,)).fetchone()


def _admit(store, admission, *, write: bool) -> None:
    """§4b.1b, under the write lock — the ONE body of the op-id-conflict decision, called by the plan transaction
    (first to check, then, when it writes the header, to write) and by each user's transaction: a held op_id with a
    different inputs digest (the mode included) refuses with nothing written; with `write`, an op_id with no record
    gets one, in the transaction of the call's first durable write."""
    op_id, mode, idig = admission
    held = _held_admission(store._conn, op_id)
    with _SITE_OP_ID_CONFLICT.consult():
        if held is not None and held[1] != idig:
            raise _SITE_OP_ID_CONFLICT.fire(_Refusal(
                "op-id-conflict", f"op_id {op_id!r} is held by a {held[0]} operation with a different inputs digest "
                                  f"({held[1][:16]}…, this call {idig[:16]}…); nothing written"))
    if held is None and write:
        store._conn.execute("INSERT INTO migration_op(op_id, mode, inputs_digest, admitted_at) VALUES(?,?,?,?)",
                            (op_id, mode, idig, store._now().isoformat()))


def _plan_phase(store, eff, digest, admission):
    """§4b.2, ONE write transaction. Returns (plan_id, written). A header with a different input digest refuses
    `registry-changed`, both digests named; a held op_id with other inputs refuses `op-id-conflict`. The header is
    written even when no relation qualifies (initialized-empty, R2-02); `id = 1` and UNIQUE(plan_id) are the
    backstop outside the lock."""
    op_id = admission[0]
    with store._lock, store._write_txn():
        _admit(store, admission, write=False)
        row = store._conn.execute("SELECT plan_id, registry_digest FROM plan_header WHERE id=1").fetchone()
        if row is not None:
            with _SITE_REGISTRY_CHANGED.consult():
                if row[1] != digest:
                    raise _SITE_REGISTRY_CHANGED.fire(_Refusal(
                        "registry-changed", f"the plan was written under registry digest {row[1]} and this call's "
                                            f"is {digest}; the plan is fixed at its first write (specs/0044 §4e), so "
                                            f"nothing was changed", plan_id=row[0]))
            return row[0], False
        era = store._conn.execute("SELECT effective_at FROM arity_era WHERE id=1").fetchone()
        plan_id = uuid.uuid4().hex
        store._conn.execute("INSERT INTO plan_header(id, plan_id, effective_at, registry_digest, op_id) "
                            "VALUES(1,?,?,?,?)", (plan_id, era[0], digest, op_id))
        for rel in plan_relations(eff):
            store._conn.execute("INSERT INTO reclassification_plan(plan_id, relation, from_arity, to_arity) "
                                "VALUES(?,?,'single','multi')", (plan_id, rel))
        _admit(store, admission, write=True)
        return plan_id, True


def _inventory_users(conn) -> list:
    return [r[0] for r in conn.execute("SELECT DISTINCT user_id FROM arity_inventory ORDER BY user_id")]


def _run(store, eff, digest, admission, plan_only) -> DataMigrationResult:
    op_id = admission[0]
    try:
        plan_id, written = _plan_phase(store, eff, digest, admission)
    except _Refusal as r:
        return _result(r.outcome, op_id=op_id, plan_id=r.plan_id, diagnostic=r.diagnostic)
    if plan_only:
        return _result("planned" if written else "already-planned", plan_written=written, op_id=op_id,
                       plan_id=plan_id)
    relations = frozenset(r[0] for r in store._conn.execute(
        "SELECT relation FROM reclassification_plan WHERE plan_id=?", (plan_id,)))
    committed, failed, reasons = [], [], []
    for user in _inventory_users(store._conn):
        try:
            done = _migrate_user(store, user, plan_id, admission, relations)
        except _Refusal as r:
            # reachable only at this call's FIRST durable write (any later transaction holds its own record), so
            # nothing of this call is committed: an op-id-conflict, never a user's failure (research's T6 read, Q5)
            assert not committed, "an op-id-conflict after this call committed a user"
            return _result(r.outcome, op_id=op_id, diagnostic=r.diagnostic)
        except Exception as x:                      # noqa: BLE001 — D1: one user's failure never stops the phase
            failed.append(user)
            reasons.append(f"{user}: {type(x).__name__}")      # never str(x): a validation error can echo content
            continue
        if done:
            committed.append(user)
    diag = ("failed users: " + "; ".join(reasons)) if reasons else ""
    if failed and not committed:
        return _result("failed", plan_written=written, failed=failed, op_id=op_id, plan_id=plan_id, diagnostic=diag)
    if failed:
        return _result("partial", plan_written=written, committed=committed, failed=failed, op_id=op_id,
                       plan_id=plan_id, diagnostic=diag)
    if committed:
        return _result("migrated", plan_written=written, committed=committed, op_id=op_id, plan_id=plan_id)
    return _result("planned" if written else "complete", plan_written=written, op_id=op_id, plan_id=plan_id)


def _migrate_user(store, user, plan_id, admission, relations) -> bool:
    """§4b.3, ONE `BEGIN IMMEDIATE` transaction for one user: the run row and the universe re-checked under the lock,
    the admission, then 0044 §4f's evaluation, the restorations, the outcome rows and the run row — committed
    together or not at all (I26). Returns True when this call committed the user, False when it skipped it."""
    with store._lock, store._write_txn():
        conn = store._conn
        if conn.execute("SELECT 1 FROM migration_run WHERE plan_id=? AND user_id=?", (plan_id, user)).fetchone():
            return False                            # a concurrent call (or an earlier invocation) committed it
        if not conn.execute("SELECT 1 FROM arity_inventory WHERE user_id=? LIMIT 1", (user,)).fetchone():
            return False                            # erased since the universe read (F3): no run row after erasure
        # research's T6 S2 F5: an inventory row naming no edge of ITS user (the edge gone, or another user's) is a
        # damaged store; `_considered`'s join would drop it silently and the user would read `migrated` with the row
        # still inventoried. Refused inside the user's transaction, BEFORE any write: the user is a named `failed`
        # (0018 §4i D1's carrier, its class-only diagnostic), and a re-call retries it once the store is repaired
        bad = conn.execute(
            "SELECT COUNT(*) FROM arity_inventory i LEFT JOIN edges e ON e.id = i.edge_id "
            "WHERE i.user_id=? AND (e.id IS NULL OR e.user_id != i.user_id)", (user,)).fetchone()[0]
        with _SITE_INVENTORY_INTEGRITY.consult():
            if bad:
                raise _SITE_INVENTORY_INTEGRITY.fire(ValueError(
                    f"{bad} arity_inventory row(s) of this user name no edge of the same user — the store is damaged "
                    f"(specs/0044 §4f; run `veracium doctor`)"))
        _admit(store, admission, write=True)
        _restore_user(store, user, plan_id, relations, admission[0])
        conn.execute("INSERT INTO migration_run(plan_id, user_id, op_id, committed_at) VALUES(?,?,?,?)",
                     (plan_id, user, admission[0], store._now().isoformat()))
    return True


def _considered(store, user, plan_id, relations) -> list:
    """0044 §4f: the user's inventoried rows whose relation (the edge's JSON, never the column — N3's class) has a
    plan row, still retired `superseded` with the inventoried retirement (an INSTANT comparison, lifetime's), with no
    outcome row under this plan (once per plan, ever — independently of the inventory, INV-A9), and not redacted
    (step 1: its carriers hold the marker, or an applied attestation names it)."""
    conn = store._conn
    attested = store.redacted_targets(user, "edge")
    out = []
    for eid, pre_at, pre_reason, raw in conn.execute(
            "SELECT i.edge_id, i.pre_invalidated_at, i.pre_reason, e.json FROM arity_inventory i "
            "JOIN edges e ON e.id = i.edge_id AND e.user_id = i.user_id WHERE i.user_id=? ORDER BY i.edge_id",
            (user,)).fetchall():
        d = json.loads(raw)
        if d.get("relation") not in relations:
            continue
        cur = _lifetime.retirement(d)
        if cur is None or cur[1] != _lifetime.SUPERSEDED or not _lifetime.same_retirement(cur, (pre_at, pre_reason)):
            continue
        if conn.execute("SELECT 1 FROM migration_outcome WHERE plan_id=? AND edge_id=?", (plan_id, eid)).fetchone():
            continue
        if _redacted(d, eid, attested):
            continue
        out.append((eid, pre_at, pre_reason))
    return out


def _redacted(d: dict, eid: str, attested) -> bool:
    """0044 §4f step 1: a row whose carriers hold the marker, or which an applied attestation names, is never
    considered (True withholds it). Defence in depth: a real redaction also replaces `relation`, which the plan
    test above catches first, so this fires only on a row whose relation is still a plan relation."""
    with _SITE_REDACTED_NOT_CONSIDERED.consult():
        return _SITE_REDACTED_NOT_CONSIDERED.fire(edge_carries_marker(d) or eid in attested, "withhold")


def _withheld(store, user, rows) -> set:
    """0044 §4f step 2 (INV-A11): the considered rows the revocation sweep's own predicate would retire were they
    active (`revocation.would_retire_if_active`, jointly) — withheld as `withheld_revoked`, never restored."""
    with _SITE_WITHHELD_REVOKED.consult():
        hit = _revocation.would_retire_if_active(store, user, [r[0] for r in rows])
        return _SITE_WITHHELD_REVOKED.fire({r[0] for r in rows if r[0] in hit}, "withhold", declined=bool(hit))


def _restore_user(store, user, plan_id, relations, op_id) -> None:
    """Steps 2–4 of 0044 §4f for one user, inside its transaction, over its considered rows (`convert_rows`)."""
    convert_rows(store, user, plan_id, _considered(store, user, plan_id, relations), op_id)


def convert_rows(store, user, plan_id, rows, op_id) -> tuple:
    """Steps 2–4 of 0044 §4f over `rows` [(edge_id, pre_invalidated_at, pre_reason)], inside the caller's write
    transaction: `withheld_revoked` where the sweep's own predicate would retire the row were it active (evaluated
    jointly, the committed state), else `restored` through 0022's reinstate writer with the reason
    `arity_reclassified`; one outcome row each (§4g), origin `local`, carrying `op_id` — the restore operation's, or a
    converting import's (0044 §4l, T11a). Returns (restored ids, withheld ids)."""
    conn = store._conn
    withheld = _withheld(store, user, rows)
    origin_store = store.local_origin()
    done = ([], [])
    for eid, pre_at, pre_reason in rows:
        outcome = "withheld_revoked" if eid in withheld else "restored"
        succ = [r[0] for r in conn.execute(
            "SELECT id FROM edges WHERE user_id=? AND json_extract(json, '$.supersedes')=? ORDER BY id", (user, eid))]
        if outcome == "restored":
            store._reinstate_edge_row(eid, reason="arity_reclassified")
        conn.execute(
            "INSERT INTO migration_outcome(plan_id, user_id, edge_id, outcome, pre_invalidated_at, pre_reason, "
            "successor_evidence, applicable, origin, outcome_uid, undone_at, undo_request_ref, op_id) "
            "VALUES(?,?,?,?,?,?,?,?,'local',?,NULL,NULL,?)",
            (plan_id, user, eid, outcome, pre_at, pre_reason,
             json.dumps(["pointer", succ] if succ else ["none", []], separators=(",", ":")),
             int(outcome == "restored"), portable_uid(origin_store, user, plan_id, eid), op_id))
        done[0 if outcome == "restored" else 1].append(eid)
    return tuple(tuple(x) for x in done)


# ------------------------------------------------------------------------------------------------- the read helpers
def _read_only(path):
    """The two read helpers' open: the same preflight — a store the operation could not run on is refused LOUDLY,
    since these are reads, not total carriers — then the SHARED opener (`SqliteStore`, 0031's one file-backed
    connection path). Opening a store the preflight classified `current` (accepted shape, no rebuildable drift)
    repairs nothing, so the read writes nothing; the receipt cell compares the database's bytes to show it."""
    if not _rm._usable_store_path(path):
        raise ValueError(f"path {_rm._safe_repr(path)} is not a usable store path")
    kind, payload = _rm._preflight_classify(path)
    with _SITE_READ_REFUSED.consult():
        if kind != "intercept" or payload.outcome != "current":
            what = payload.outcome if kind == "intercept" else kind
            raise _SITE_READ_REFUSED.fire(ValueError(
                f"not a current v{sv.SCHEMA_VERSION} store ({what}); the data-migration reads need one"))
    from .sqlite import SqliteStore
    return SqliteStore(os.path.realpath(path))


def data_migration_status(path, op_id) -> DataMigrationStatus:
    """§4c: after an unknown return, the operation's cumulative durable facts — whether its op_id wrote the plan
    header, and the users its run rows name over every invocation — or `unknown-op` when no admission record holds
    the id (a call that wrote nothing wrote no record). A user it did not commit reads as not run."""
    from ..schema import validate_correlation_id
    validate_correlation_id(op_id)
    store = _read_only(path)
    try:
        conn = store._conn
        if _held_admission(conn, op_id) is None:
            return DataMigrationStatus("unknown-op", False, ())
        header = conn.execute("SELECT op_id FROM plan_header WHERE id=1").fetchone()
        users = tuple(r[0] for r in conn.execute(
            "SELECT user_id FROM migration_run WHERE op_id=? ORDER BY user_id", (op_id,)))
        return DataMigrationStatus("known", header is not None and header[0] == op_id, users)
    finally:
        store.close()


def data_migration_receipt(path, plan_id, user_id) -> tuple:
    """§4d / 0044 §4g: every considered row of this user under the plan, with its outcome, pre-state, successor
    evidence and undo state. No copy of memory content is stored: `object` is read from the live edge now (a redacted
    edge shows the marker); an absent edge renders "no longer held" from the outcome row alone. Erasure ends it."""
    store = _read_only(path)
    try:
        conn = store._conn
        rows = []
        for eid, outcome, pre_at, pre_reason, succ, applicable, undone_at, origin in conn.execute(
                "SELECT edge_id, outcome, pre_invalidated_at, pre_reason, successor_evidence, applicable, undone_at, "
                "origin FROM migration_outcome WHERE plan_id=? AND user_id=? ORDER BY edge_id", (plan_id, user_id)):
            kind, ids = json.loads(succ)
            live = conn.execute("SELECT json FROM edges WHERE id=? AND user_id=?", (eid, user_id)).fetchone()
            rows.append(ReceiptRow(eid, outcome, pre_at, pre_reason, tuple(ids) if kind == "pointer" else None,
                                   json.loads(live[0]).get("object") if live is not None else NO_LONGER_HELD,
                                   bool(applicable), undone_at, origin))
        return tuple(rows)
    finally:
        store.close()


# ================================================================================================ 0044 §4i: undo
PROOF_ORIGINS = ("local", "restored")       # 0044 §4k / R2-05: an `imported` outcome is testimony, never undone


def _undo_result(edge_id, undone_at, correlation_id, *, replayed, already_undone) -> dict:
    return {"undone": edge_id, "undone_at": undone_at, "correlation_id": correlation_id,
            "replayed": replayed, "already_undone": already_undone}


def undo_restoration(store, user_id: str, edge_id: str, correlation_id: str) -> dict:
    """0044 §4i, inside the caller's write transaction (`SqliteStore.undo_restoration`). In order:
      0. the user's outcome rows for the edge — the OUTCOME table, never the edge; two rows refuse
         `ambiguous-outcome` BEFORE the registry, because the request digest needs the row's plan (the annotation);
      1. the registry (`_registry_held`, the ONE body `confirm()` shares): terminal, then the verb; then this verb's
         digest; a completed undo REPLAYS from its `result_ref` (the outcome_uid) without reading the edge;
      2. eligibility: restored, not undone (else the recorded `already undone at T`, writing nothing), PROOF,
         `applicable`, the edge held and not redacted;
      3. the per-field restore through `_invalidate_edge_row` — the invalidate METHOD, so 0029's choke point
         journals `invalidated` and the T5-2 lifetime hook clears `applicable` (§4f-ii); the outcome row's
         `undone_at` is written only where the hook has cleared the flag (research's Q8: CHECK it, never write it);
      4. the registry row, `undo`, in this transaction. No act row and no act position (0008 §6f, D4)."""
    conn = store._conn
    rows = conn.execute(
        "SELECT plan_id, outcome, undone_at, origin, applicable, pre_invalidated_at, pre_reason, outcome_uid "
        "FROM migration_outcome WHERE user_id=? AND edge_id=?", (user_id, edge_id)).fetchall()
    with _SITE_UNDO_AMBIGUOUS.consult():
        if len(rows) > 1:
            raise _SITE_UNDO_AMBIGUOUS.fire(UndoRefused(
                "ambiguous-outcome", user_id, edge_id,
                f"{len(rows)} outcome rows name it (plans {sorted(r[0] for r in rows)}); no undo lookup chooses "
                f"between two (§4l)"))
    digest = portable_uid("undo", user_id, edge_id, rows[0][0] if rows else "")
    held = _registry_decision(store, user_id, edge_id, correlation_id, digest)
    if held is not None:
        return held
    with _SITE_UNDO_NO_OUTCOME.consult():
        if not rows:
            raise _SITE_UNDO_NO_OUTCOME.fire(UndoRefused(
                "no-outcome", user_id, edge_id, "the data migration recorded no outcome for it"))
    plan_id, outcome, undone_at, origin, applicable, pre_at, pre_reason, outcome_uid = rows[0]
    with _SITE_UNDO_NOT_RESTORED.consult():
        if outcome != "restored":
            raise _SITE_UNDO_NOT_RESTORED.fire(UndoRefused(
                "not-restored", user_id, edge_id, f"its outcome is {outcome!r}: nothing was restored to undo"))
    if undone_at is not None:
        # §4i.1: the recorded answer; this call wrote nothing, so it holds no id (the annotation; 0018 §4i §4b.1b)
        return _undo_result(edge_id, undone_at, correlation_id, replayed=False, already_undone=True)
    with _SITE_UNDO_TESTIMONY.consult():
        if origin not in PROOF_ORIGINS:
            raise _SITE_UNDO_TESTIMONY.fire(UndoRefused(
                "testimony", user_id, edge_id, f"its outcome is {origin!r} testimony of another store's restoration, "
                                               f"which this store cannot reverse (R2-05)"))
    with _SITE_UNDO_NOT_APPLICABLE.consult():
        if not applicable:
            raise _SITE_UNDO_NOT_APPLICABLE.fire(UndoRefused(
                "not-applicable", user_id, edge_id, "the restoration episode ended (a later retirement, redaction "
                                                    "or the edge's removal; a source lift never revives it)"))
    edge = conn.execute("SELECT json FROM edges WHERE id=? AND user_id=?", (edge_id, user_id)).fetchone()
    with _SITE_UNDO_EDGE_UNAVAILABLE.consult():
        if edge is None or edge_carries_marker(json.loads(edge[0])):
            raise _SITE_UNDO_EDGE_UNAVAILABLE.fire(UndoRefused(
                "edge-unavailable", user_id, edge_id, "the edge is no longer held, or is redacted"))
    store._invalidate_edge_row(edge_id, pre_at, pre_reason)
    now = store._now().isoformat()
    n = conn.execute("UPDATE migration_outcome SET undone_at=?, undo_request_ref=? "
                     "WHERE plan_id=? AND edge_id=? AND undone_at IS NULL AND applicable=0",
                     (now, correlation_id, plan_id, edge_id)).rowcount
    if n != 1:
        # the retirement above passes 0029's choke point, whose lifetime hook clears `applicable` (§4f-ii); a row
        # still applicable here means the hook did not run on this path — refuse rather than write a second rule
        raise RuntimeError(f"undo of {edge_id!r}: the outcome row's `applicable` was not cleared by the retirement "
                           f"(specs/0044 §4f-ii's lifetime hook) — nothing written")
    try:
        conn.execute("INSERT INTO request_registry(user_id, correlation_id, verb, target_edge_id, request_digest, "
                     "result_ref, written_at) VALUES(?,?,'undo',?,?,?,?)",
                     (user_id, correlation_id, edge_id, digest, outcome_uid, now))
    except sqlite3.IntegrityError:
        # C8's shape (confirm's): a duplicate won the UNIQUE(user_id, correlation_id). Under BEGIN IMMEDIATE taken
        # before the registry read no other connection can; kept defensively, through the SAME lookup
        conn.rollback()
        held = _registry_decision(store, user_id, edge_id, correlation_id, digest)
        with _SITE_UNDO_CORRELATION.consult():
            if held is None:
                raise _SITE_UNDO_CORRELATION.fire(ValueError(
                    f"correlation_id {correlation_id!r} conflict (specs/0008 §6c)"))
        return held
    store._bump(user_id)
    return _undo_result(edge_id, now, correlation_id, replayed=False, already_undone=False)


def _registry_decision(store, user_id, edge_id, correlation_id, digest) -> Optional[dict]:
    """The registry, before any read of the edge (INV-A13, INV-Q2): None when the id is free; else the replay."""
    held = store._registry_held(user_id, correlation_id, "undo")
    if held is None:
        return None
    held_digest, result_ref = held
    with _SITE_UNDO_REQUEST_DIGEST.consult():
        if held_digest != digest:
            raise _SITE_UNDO_REQUEST_DIGEST.fire(ValueError(
                f"correlation_id {correlation_id!r} was already used for a DIFFERENT undo request — integrity "
                f"conflict (specs/0008 §6c)"))
    row = store._conn.execute("SELECT edge_id, undone_at FROM migration_outcome WHERE outcome_uid=? AND user_id=?",
                              (result_ref, user_id)).fetchone()
    with _SITE_UNDO_RESULT_MISSING.consult():
        if row is None or row[1] is None:
            raise _SITE_UNDO_RESULT_MISSING.fire(ValueError(
                f"correlation_id {correlation_id!r}: the registry names outcome {result_ref!r}, which is absent or "
                f"not undone — integrity conflict (specs/0008 §6c)"))
    return _undo_result(row[0], row[1], correlation_id, replayed=True, already_undone=False)
