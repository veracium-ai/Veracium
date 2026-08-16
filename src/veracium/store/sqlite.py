"""Embedded SQLite store — the zero-dependency default.

Everything (edges, episodes, compiled-view cache, per-user write counter) lives
in one SQLite file. Per-user graphs are small (the research saw ~120 edges at
9 weeks of history), so a single indexed table per kind is ample; a Neo4j/
Postgres `Store` can replace this for very large multi-tenant deployments.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from ..authority import RULE_VERSION, scope_fingerprint
from ..schema import (ConsolidationOp, ConsolidationOutputDraft, ConsolidationState,
                      Confirmation, ConfirmationActor, ConfirmationCallPath,
                      Disclosure, Edge, Episode, EvidenceAuthor, OutcomeJudgmentDraft,
                      Provenance, RECOVERY_PENDING_STATES,
                      SupersessionPlan, SupersessionRefusal, SupersessionResult,
                      is_historical_id, to_historical_id)
from .base import (DESTINATION_CHANGED, HEAD_MOVED, LEASE_MAX, NON_QUIESCENT,
                   PLAN_STALE, ReceiptSchemaBoundaryError, Store,
                   SupersessionIntegrityError)
from .schema_version import (SCHEMA_V1, SCHEMA_VERSION, SCHEMAS,  # noqa: F401
                             PostCommitAuditError,
                             StoreVersionError, open_versioned)

# The schema is DERIVED from the versioning registry — one declaration, which
# is 0007 §4a-vi's "honest end state": there is no second copy to drift, and
# `registry_conformance` compares this module against the registry it is built
# from. It tracks the CURRENT `SCHEMA_VERSION` (v2 adds `specs/0008`'s
# `confirmations` table), never a pinned v1. `IF NOT EXISTS` is gone with it:
# creation now happens exactly once, on the §4 "new" path, inside the open
# transaction.
_SCHEMA = ";\n".join(o.ddl for o in SCHEMAS[SCHEMA_VERSION]) + ";\n"


class SqliteStore(Store):
    def __init__(self, path: str | Path = "veracium.db", *,
                 allow_adopt: bool = True, audit_sink=None,
                 busy_timeout_ms: int = 5000, clock=None):
        self._path = str(path)
        # specs/0010 §4b-ii: the lease clock is the STORE's, not any worker's —
        # worker clocks disagree and a lease decided by the holder is not a lease.
        # Injectable so tests can drive lease expiry/renewal deterministically.
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        # 0007 §4e: audit strings are validated against a 4096-byte cap, never
        # truncated — and the path is checked before connecting, so the limit
        # is ours rather than whatever the OS happens to raise.
        if len(self._path.encode()) > 4096:
            raise ValueError("store path exceeds the 4096-byte audit limit")
        # check_same_thread=False + a lock: safe for the library's typical
        # single-writer, many-reader agent usage without a connection pool.
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        # 0007 §4c: `database is locked` waits this long, then refuses loudly
        # with reason="locked" — a startup failure that manifests as a hang is
        # worse than one that manifests as an error.
        self._conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        try:
            # The 0007 §4 decision table: refuse-unrecognised, stamp, adopt-v1.
            # Replaces the former unconditional `executescript(_SCHEMA)`, which
            # opened ANY store and silently added missing tables to foreign
            # ones. open_versioned() takes BEGIN IMMEDIATE before reading
            # anything and commits exactly once.
            open_versioned(self._conn, self._path,
                           allow_adopt=allow_adopt, audit_sink=audit_sink)
        except BaseException:
            self._conn.close()
            raise
        self._lock = threading.Lock()

    def _bump(self, user_id: str) -> None:
        self._conn.execute(
            "INSERT INTO write_counter(user_id, n) VALUES(?, 1) "
            "ON CONFLICT(user_id) DO UPDATE SET n = n + 1", (user_id,))

    # -- source identity (specs/0006) --------------------------------------
    def local_origin(self) -> str:
        """specs/0006 §4.2 — this store's durable, minted `origin` (the `store_identity`
        singleton). It is the value an absent local record-`origin` resolves to at read
        (§4 rule 6, `source_identity.resolve_origin`). Minted once at create/migrate and
        durable across reopen/backup (I11)."""
        row = self._conn.execute(
            "SELECT origin FROM store_identity WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError(
                "store_identity singleton is missing — a v5 store mints it at "
                "creation/migration (specs/0006 §4.2); this store did not")
        return row[0]

    # -- edges -------------------------------------------------------------
    def _upsert_edge_row(self, edge: Edge) -> None:
        """INSERT OR REPLACE one edge with the specs/0008 §6d guards, WITHOUT taking the
        lock, bumping the write counter, or committing — the caller owns the transaction.
        `add_edge` and `apply_supersession_plan` (specs/0003 §4f) both use it, so the
        ownership + needs_confirmation guards hold on every persistence path, not only
        the single-edge one."""
        # specs/0008 §6d: may NOT clear `needs_confirmation` (True→False) when replacing
        # an edge of the same id — only `confirm_edge` may — and may NOT change an edge's
        # `user_id`. Compared against the PERSISTED prior state, so a reconstructed edge
        # cannot slip the transition past the write path (C1, C10).
        prior = self._conn.execute(
            "SELECT user_id, json FROM edges WHERE id=?", (edge.id,)).fetchone()
        if prior is not None:
            if prior[0] != edge.user_id:
                raise ValueError(
                    f"cannot change edge {edge.id!r}'s user_id "
                    f"({prior[0]!r} → {edge.user_id!r}) — ownership is not "
                    f"transferable through the upsert path (specs/0008 §6d)")
            prior_edge = Edge.model_validate_json(prior[1])
            if prior_edge.needs_confirmation and not edge.needs_confirmation:
                raise ValueError(
                    f"cannot clear needs_confirmation (True→False) on "
                    f"edge {edge.id!r} — only confirm_edge may (specs/0008 §6d, C1)")
            # specs/0019 §3b/§4d (R2-4, U4): a STORED row's `ungrounded` never
            # changes — the same-ID replace path refuses EVERY transition, in
            # BOTH directions, with no exception (absorption inserts a NEW
            # survivor whose flag is the N-ary OR computed pre-insert, so no
            # discriminator is needed here). Compared against the PERSISTED
            # prior state, the 0008 §6d guard shape.
            if prior_edge.ungrounded != edge.ungrounded:
                raise ValueError(
                    f"cannot change ungrounded "
                    f"({prior_edge.ungrounded} → {edge.ungrounded}) on edge "
                    f"{edge.id!r} — a stored flag is immutable in both "
                    f"directions (specs/0019 §4d, U4)")
        self._conn.execute(
            "INSERT OR REPLACE INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (edge.id, edge.user_id, edge.subject, edge.relation, edge.object,
             int(edge.active), int(edge.quarantined), edge.model_dump_json()))

    def add_edge(self, edge: Edge) -> None:
        with self._lock:
            self._upsert_edge_row(edge)
            self._bump(edge.user_id)
            self._conn.commit()

    @staticmethod
    def _confirmation_from_row(row) -> Confirmation:
        (cid, uid, eid, cat, actor, cpath, corr, dig) = row
        return Confirmation(
            id=cid, user_id=uid, edge_id=eid, confirmed_at=datetime.fromisoformat(cat),
            actor=ConfirmationActor(actor), call_path=ConfirmationCallPath(cpath),
            correlation_id=corr, request_digest=dig)

    def confirm_edge(self, user_id, edge_id, *, actor, call_path, correlation_id,
                     request_digest, confirmed_at) -> Confirmation:
        _COLS = ("id, user_id, edge_id, confirmed_at, actor, call_path, "
                 "correlation_id, request_digest")
        with self._lock:
            row = self._conn.execute(
                "SELECT json FROM edges WHERE id=? AND user_id=?",
                (edge_id, user_id)).fetchone()
            if row is None:
                raise KeyError(
                    f"edge {edge_id!r} not found for user {user_id!r}")
            edge = Edge.model_validate_json(row[0])
            if not edge.assertable:
                raise ValueError(
                    f"edge {edge_id!r} is not assertable (quarantined/use_only/"
                    f"inactive) — a user affirming a claim is new evidence: ingest "
                    f"it via remember(author=USER) instead")
            # Idempotency, checked BEFORE any mutation: a prior confirmation under
            # this tenant-scoped correlation id is a replay if the canonical request
            # matches, an integrity conflict otherwise (specs/0008 §6c).
            prior = self._conn.execute(
                f"SELECT {_COLS} FROM confirmations WHERE user_id=? AND "
                f"correlation_id=?", (user_id, correlation_id)).fetchone()
            if prior is not None:
                if prior[7] != request_digest:
                    raise ValueError(
                        f"correlation_id {correlation_id!r} was already used for a "
                        f"DIFFERENT request — integrity conflict (specs/0008 §6c)")
                out = self._confirmation_from_row(prior)
                return out.model_copy(update={"replayed": True})
            edge.needs_confirmation = False
            edge.provenance.observed_at = max(edge.provenance.observed_at, confirmed_at)
            edge.provenance.confidence = max(edge.provenance.confidence, 0.9)
            cid = f"c-{uuid.uuid4().hex[:12]}"
            actor_v = ConfirmationActor(actor).value
            call_v = ConfirmationCallPath(call_path).value
            try:
                self._conn.execute("UPDATE edges SET json=? WHERE id=?",
                                   (edge.model_dump_json(), edge_id))
                self._conn.execute(
                    "INSERT OR REPLACE INTO episodes(id,user_id,date,json) "
                    "VALUES(?,?,?,?)",
                    (f"ep-{uuid.uuid4().hex[:12]}", user_id,
                     confirmed_at.date().isoformat(),
                     Episode(id=f"ep-{cid}", user_id=user_id,
                             date=confirmed_at.date().isoformat(),
                             summary=f"({actor_v}) confirmed "
                                     f"'{edge.relation}: {edge.object}' still holds",
                             provenance=Provenance(
                                 author_of_evidence=EvidenceAuthor.USER,
                                 evidence_ref=f"confirm:{edge_id}")
                             ).model_dump_json()))
                self._conn.execute(
                    f"INSERT INTO confirmations({_COLS}) VALUES(?,?,?,?,?,?,?,?)",
                    (cid, user_id, edge_id, confirmed_at.isoformat(), actor_v,
                     call_v, correlation_id, request_digest))
                self._bump(user_id)
                self._conn.commit()
            except sqlite3.IntegrityError:
                # C8: a concurrent duplicate won the UNIQUE(user_id, correlation_id)
                # race. Roll back ours and return the committed original / conflict.
                self._conn.rollback()
                other = self._conn.execute(
                    f"SELECT {_COLS} FROM confirmations WHERE user_id=? AND "
                    f"correlation_id=?", (user_id, correlation_id)).fetchone()
                if other is None or other[7] != request_digest:
                    raise ValueError(
                        f"correlation_id {correlation_id!r} conflict (specs/0008 §6c)")
                return self._confirmation_from_row(other).model_copy(
                    update={"replayed": True})
            except BaseException:
                # C7: all-or-nothing — a failure anywhere (e.g. the mandatory record
                # cannot commit) rolls back EVERY edge field and the episode, so the
                # flag stays set and no partial confirmation is left on the wire.
                self._conn.rollback()
                raise
            return Confirmation(
                id=cid, user_id=user_id, edge_id=edge_id, confirmed_at=confirmed_at,
                actor=ConfirmationActor(actor), call_path=ConfirmationCallPath(call_path),
                correlation_id=correlation_id, request_digest=request_digest)

    def confirmations_for(self, user_id, edge_id) -> list[Confirmation]:
        _COLS = ("id, user_id, edge_id, confirmed_at, actor, call_path, "
                 "correlation_id, request_digest")
        rows = self._conn.execute(
            f"SELECT {_COLS} FROM confirmations WHERE user_id=? AND edge_id=? "
            f"ORDER BY confirmed_at DESC", (user_id, edge_id)).fetchall()
        return [self._confirmation_from_row(r) for r in rows]

    def _invalidate_edge_row(self, edge_id: str, at, reason: str) -> Optional[str]:
        """Retire one edge WITHOUT lock/bump/commit; returns its user_id, or None if the
        edge does not exist. Shared by `invalidate_edge` and `apply_supersession_plan`."""
        row = self._conn.execute("SELECT json, user_id FROM edges WHERE id=?", (edge_id,)).fetchone()
        if not row:
            return None
        edge = Edge.model_validate_json(row[0])
        edge.invalidated_at = at
        edge.invalidation_reason = reason
        self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",
                           (edge.model_dump_json(), edge_id))
        return row[1]

    def _edge_in_refusal(self, user_id: str, edge_id: str) -> bool:
        """True if `edge_id` participates (as prior or incoming) in any refusal record —
        i.e. it may be a member of a live refusal contention (specs/0003 §4c-ii)."""
        return self._conn.execute(
            "SELECT 1 FROM supersession_refusals WHERE user_id=? AND "
            "(prior_edge_id=? OR incoming_edge_id=?) LIMIT 1",
            (user_id, edge_id, edge_id)).fetchone() is not None

    def invalidate_edge(self, edge_id: str, at, reason: str) -> None:
        with self._lock:
            uid = self._invalidate_edge_row(edge_id, at, reason)
            if uid is None:
                return
            self._bump(uid)
            # specs/0003 §4c-ii (round-10 blocker 1): deactivating an edge that
            # participates in a refusal contention is a derived-view RESOLUTION event —
            # `correct()`/`dispute`/lifecycle can end a `live_refusal_contention` while
            # the durable refusal is retained. Drop the wiki in the SAME mutation so the
            # invalidation rule is symmetric (formation AND resolution both recompile).
            if self._edge_in_refusal(uid, edge_id):
                self._conn.execute("DELETE FROM wiki WHERE user_id=?", (uid,))
            self._conn.commit()

    def edges(self, user_id, *, active_only=True, subject=None, relation=None,
              include_quarantined=True) -> list[Edge]:
        q = "SELECT json FROM edges WHERE user_id=?"
        args: list = [user_id]
        if active_only:
            q += " AND active=1"
        if subject is not None:
            q += " AND subject=?"; args.append(subject)
        if relation is not None:
            q += " AND relation=?"; args.append(relation)
        if not include_quarantined:
            q += " AND quarantined=0"
        rows = self._conn.execute(q, args).fetchall()
        return [Edge.model_validate_json(r[0]) for r in rows]

    # -- supersession (specs/0003) ----------------------------------------
    @staticmethod
    def _logical_request_digest(plan: SupersessionPlan) -> str:
        """A fingerprint of the plan's LOGICAL intent — what it does, NOT the
        `expected_state` it assumed (which changes on a CAS recompute). The same logical
        operation replayed produces the same digest (→ replay a committed receipt); a
        genuinely different operation that reuses an `operation_id` produces a different
        digest (→ integrity conflict). §4f processing order step 1."""
        # The digest binds the COMPLETE logical persistent outcome — every field the plan
        # would persist — not a hand-picked subset. The previous form bound only
        # [id, object, author, derived_from] + structural ids, so a resubmission of the
        # same operation_id with DIFFERENT provenance (another source_id, an inflated
        # confidence, a moved observed_at) digested identically and REPLAYED silently,
        # keeping the first submission's provenance while reporting success for the
        # second — exactly the "genuinely different operation" this docstring promises
        # an integrity conflict for (0012 round-1 external review, F4). Excluded, by the
        # docstring's own rule: `expected_state` (changes on CAS recompute) and
        # `operation_id` (it is the lookup key). A verbatim retry still replays: identical
        # plan → identical serialization; the reinforcement recompute stays stable because
        # max() is idempotent.
        # specs/0016 D2: the era-faithful recomputation (0019's strip of the
        # `ungrounded` field for pre-0019 receipts) is REMOVED — a receipt
        # stamped below version 4 refuses ON SIGHT before any digest is
        # computed (no comparison branch exists), so only the CURRENT dump
        # shape is ever digested here.
        def _dump(e):
            return json.loads(e.model_dump_json())
        payload = {
            "incoming": _dump(plan.incoming_edge),
            "insert_incoming": plan.insert_incoming,
            "upserts": sorted((_dump(e) for e in plan.prior_upserts),
                              key=lambda d: d["id"]),
            "invalidations": sorted([eid, at.isoformat(), reason]
                                    for eid, at, reason in plan.prior_invalidations),
            "refusals": sorted(
                (json.loads(r.model_dump_json()) for r in plan.refusals),
                key=lambda d: (d["prior_edge_id"], d["incoming_edge_id"])),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _outcome_digest_v2(self, plan: SupersessionPlan) -> str:
        """specs/0014 R5-2/R6-1/R9-2: the EXTENDED outcome projection — everything
        the pre-split digest bound PLUS the contribution drafts and the absorption
        pre-image, so a store-level resubmission that mutates contribution fields
        is detected (the mutation check, reachable by construction because
        store-level callers submit plans). New receipts stamp version 4 (the
        0016 D2 `source_type`-less snapshot — the 0019 rider A1): the v4
        projection IS this v2 construction computed over the post-D2 field
        set (same wrapper, reduced basis). Stored versions 1–3 were digested
        over snapshots that carried the deleted field; neither historical
        projection is computable post-D2, so those receipts refuse ON SIGHT
        at the era boundary before this function is ever called — there is no
        era-faithful recomputation and no by-version selection."""
        payload = {
            "v1": None,   # structural marker: v2/v3/v4 wrap the v1 projection
            "pre_split": self._logical_request_digest(plan),
            "contributions": sorted(
                (json.loads(d.model_dump_json()) for d in plan.contribution_drafts),
                key=lambda d: (d["site"], d["contributor_type"], d["contributor_id"])),
            "absorption_pre_image": plan.absorption_pre_image,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def validate_receipt_state(request_digest, version, response) -> None:
        """specs/0014 R9-2/R10-4: the receipt-state triple is a CLOSED
        enumerated set — (NULL, 1, NULL) legacy; (NULL, ver, json) and
        (digest, ver, json) for ver in {2, 3, 4}. Any other combination is an
        integrity error at write AND at read; the response, when present,
        must deserialize into the exact effect fields. A LEGAL pre-D2 state
        (version < 4) is still a valid stored receipt — validation passes and
        the 0016 D2 era boundary then refuses it on sight; validation itself
        computes no digest."""
        if version == 1:
            if request_digest is not None or response is not None:
                raise ValueError(
                    f"illegal receipt state ({request_digest!r}, 1, "
                    f"{'json' if response else None}) — version-1 rows are the "
                    f"migrated legacy form (NULL, 1, NULL) only (0014 R10-4)")
            return
        if version in (2, 3, 4):
            # version 3 (specs/0019 rider): the ungrounded-bearing-snapshot
            # era; version 4 (specs/0016 D2, rider A1): the source_type-less
            # era — identical receipt-state SHAPE throughout; the era
            # difference lives in the digest projection, and versions < 4
            # refuse at the boundary before any projection is computed
            if response is None:
                raise ValueError(
                    f"illegal receipt state (…, {version}, NULL) — every "
                    f"version-{version} receipt persists its effect payload "
                    f"(0014 R9-1/R10-4)")
            try:
                effects = json.loads(response)
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"receipt response is not valid JSON (0014 R10-4): {e}") from e
            if (not isinstance(effects, dict)
                    or set(effects) != {"inserted_incoming", "invalidated",
                                        "refused"}):
                raise ValueError(
                    "receipt response does not carry exactly the effect fields "
                    "{inserted_incoming, invalidated, refused} (0014 R10-1/R10-4)")
            return
        raise ValueError(
            f"illegal outcome_digest_version {version!r} — the closed set is "
            f"{{1, 2, 3, 4}} (0014 R9-2/R10-4; 3 per the 0019 rider; 4 per "
            f"0016 D2)")

    def supersession_receipt(self, user_id: str, operation_id: str):
        """specs/0014 §4b: the phase-1 lookup surface — the receipt's request
        identity, projection version, and persisted effects, or None."""
        row = self._conn.execute(
            "SELECT logical_request_digest, status, request_digest, response, "
            "outcome_digest_version FROM supersession_operations "
            "WHERE user_id=? AND operation_id=?",
            (user_id, operation_id)).fetchone()
        if row is None:
            return None
        self.validate_receipt_state(row[2], row[4], row[3])   # flagged at read
        return {"logical_request_digest": row[0], "status": row[1],
                "request_digest": row[2], "response": row[3],
                "outcome_digest_version": row[4]}

    @staticmethod
    def _replay_from_effects(response_json: str):
        """R10-1: replay CONSTRUCTS its result as the persisted effect fields +
        replayed=True — effect identity from the durable carrier, runtime
        provenance from the call. Never a reconstruction from the submitted
        (and discarded) plan."""
        effects = json.loads(response_json)
        return SupersessionResult(**effects, replayed=True)

    def apply_supersession_plan(self, plan: SupersessionPlan):
        from ..contribution import (effect_payload, request_digest,
                                    verify_snapshot_against_plan)
        inc = plan.incoming_edge
        user_id = inc.user_id
        with self._lock:
            # 1. receipt check — PRECEDES the CAS check, so a committed op REPLAYS rather
            #    than tripping PlanStale on its own now-stale expected_state (§4f, r9 B3),
            #    AND precedes EVERY digest computation: the 0016 D2 era boundary fires
            #    ON SIGHT of a stored version < 4 — no digest is computed (not even the
            #    plan's own request digest), no comparison branch exists; the
            #    exploding-sentinel regressions pin exactly this ordering.
            #    PHASE 2 is REQUEST-FIRST where request identity exists on both sides
            #    (R8-1): matching raw_request → replay the PERSISTED effects, the
            #    submitted plan's re-planned outcome DISCARDED unconsulted (the
            #    concurrent-preflight loser lands here); differing → conflict. The
            #    outcome digest governs ONLY receipts/plans WITHOUT request identity —
            #    always the v4 projection: the era gate admits no other stored version.
            row = self._conn.execute(
                "SELECT logical_request_digest, request_digest, response, "
                "outcome_digest_version FROM supersession_operations "
                "WHERE user_id=? AND operation_id=?", (user_id, plan.operation_id)).fetchone()
            if row is not None:
                stored_outcome, stored_rd, stored_resp, stored_ver = row
                self.validate_receipt_state(stored_rd, stored_ver, stored_resp)
                if stored_ver < 4:
                    raise ReceiptSchemaBoundaryError(
                        f"operation_id {plan.operation_id!r} for user {user_id!r} "
                        f"committed under a pre-D2 receipt era (outcome_digest_"
                        f"version {stored_ver}): its digest basis included the "
                        f"deleted source_type field, so no historical projection "
                        f"is computable and this resubmission is not replay-"
                        f"verifiable across the removal — refused on sight, no "
                        f"digest computed, a legitimate retry indistinguishable "
                        f"from a different request (specs/0016 D2; 0003 §4f as "
                        f"amended)")
            # specs/0014 §4b: a present snapshot is verified against the plan under
            # the exhaustive field partition BEFORE any use (forged/malformed →
            # abort); the store derives the request digest ITSELF (R7-1).
            plan_rd = None
            if plan.raw_request is not None:
                try:
                    verify_snapshot_against_plan(plan.raw_request, plan)
                except ValueError as e:
                    raise SupersessionIntegrityError(str(e)) from e
                plan_rd = request_digest(plan.raw_request)
            digest = self._outcome_digest_v2(plan)
            if row is not None:
                if stored_rd is not None and plan_rd is not None:
                    if plan_rd == stored_rd:
                        return self._replay_from_effects(stored_resp)
                    raise SupersessionIntegrityError(
                        f"operation_id {plan.operation_id!r} already committed a "
                        f"DIFFERENT request for user {user_id!r} (specs/0014 §4b "
                        f"phase 2, request-first)")
                if stored_outcome != digest:
                    raise SupersessionIntegrityError(
                        f"operation_id {plan.operation_id!r} already committed a DIFFERENT "
                        f"logical operation for user {user_id!r} — a reused id is a caller "
                        f"integrity bug, not a race (specs/0003 §4f; projection "
                        f"v{stored_ver})")
                # every version-4 receipt persists its effects (validated above)
                return self._replay_from_effects(stored_resp)
            # 2/3. CAS: revalidate the COMPLETE scope fingerprint inside the txn; stale →
            #      PlanStale, no write, receipt NOT consumed (the caller retries).
            scope = self.edges(user_id, subject=inc.subject, relation=inc.relation,
                               active_only=True, include_quarantined=True)
            if scope_fingerprint(scope) != plan.expected_state:
                return PLAN_STALE
            # 4. apply all-or-nothing (one transaction). ANY failure mid-apply rolls the
            #    WHOLE plan back — no incoming edge, no prior mutations, no refusal rows,
            #    no receipt — so there is never a durable partial state (§4f failure rule).
            try:
                # specs/0014 §4b: EXACT SET EQUALITY between the plan's absorption
                # drafts and its absorbed_duplicate invalidations (R5-1) — one draft
                # per absorbed prior, no omissions, no duplicates, no extras. Checked
                # and written BEFORE the contributor rows are invalidated, inside this
                # same transaction (A7: rows atomic with the op).
                absorbed_ids = [eid for eid, _at, r in plan.prior_invalidations
                                if r == "absorbed_duplicate"]
                draft_ids = [d.contributor_id for d in plan.contribution_drafts
                             if d.site == "absorption"]
                if (sorted(absorbed_ids) != sorted(set(absorbed_ids))
                        or sorted(draft_ids) != sorted(set(draft_ids))
                        or set(absorbed_ids) != set(draft_ids)):
                    raise SupersessionIntegrityError(
                        f"absorption drafts {sorted(draft_ids)} != absorbed priors "
                        f"{sorted(absorbed_ids)} — the draft set must equal the "
                        f"absorbed_duplicate set exactly (specs/0014 §4b, R5-1)")
                contributor_flags = [self._write_contribution(user_id, d, plan)
                                     for d in plan.contribution_drafts]
                # specs/0019 §4d / 0014 §2c as amended (U2b): the committed
                # survivor's `ungrounded` must be EXACTLY the N-ary OR over
                # {the raw incoming} ∪ {every absorbed contributor} —
                # recomputed here from the plan's full contributor set against
                # the AUTHORITATIVE rows just read. Any other flag difference
                # aborts. Without a snapshot (phase-2 semantics) the raw
                # incoming flag is unknowable; the laundering direction is
                # still fully checkable: a flagged contributor forces a
                # flagged survivor.
                if any(contributor_flags) and inc.ungrounded is not True:
                    raise SupersessionIntegrityError(
                        "a flagged contributor was absorbed but the survivor "
                        "is unflagged — the N-ary OR never launders the "
                        "signal (specs/0019 §4d; 0014 §2c as amended)")
                if plan.raw_request is not None:
                    expected = (bool(plan.raw_request.get("ungrounded"))
                                or any(contributor_flags))
                    if inc.ungrounded is not expected:
                        raise SupersessionIntegrityError(
                            f"survivor ungrounded={inc.ungrounded!r} is not "
                            f"the N-ary OR of the raw submission and its "
                            f"absorbed contributors (={expected!r}) — the "
                            f"verifier accepts exactly that transform "
                            f"(specs/0019; 0014 §2c as amended)")
                for e in plan.prior_upserts:
                    self._upsert_edge_row(e)
                for eid, at, reason in plan.prior_invalidations:
                    self._invalidate_edge_row(eid, at, reason)
                if plan.insert_incoming:
                    self._upsert_edge_row(inc)
                now = self._now().isoformat()
                for d in plan.refusals:
                    # BIND the refusal: it may only reference the plan's incoming edge and
                    # an existing edge of THIS user (round-6 correction C) — a caller cannot
                    # forge a refusal against an edge this commit does not write or another
                    # tenant's.
                    if d.incoming_edge_id != inc.id:
                        raise ValueError(
                            "refusal.incoming_edge_id must equal the plan's incoming edge id")
                    prow = self._conn.execute(
                        "SELECT user_id FROM edges WHERE id=?", (d.prior_edge_id,)).fetchone()
                    if prow is None or prow[0] != user_id:
                        raise ValueError(
                            "refusal.prior_edge_id must be an existing edge of this user")
                    self._conn.execute(
                        "INSERT INTO supersession_refusals(refusal_id,user_id,prior_edge_id,"
                        "incoming_edge_id,relation,prior_effective,incoming_effective,"
                        "rule_version,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (f"ref-{uuid.uuid4().hex[:12]}", user_id, d.prior_edge_id, inc.id,
                         d.relation, d.prior_effective, d.incoming_effective, RULE_VERSION, now))
                # the durable receipt commits atomically with the effects (§4f
                # idempotency; 0014 R9-1/R9-2/R10-1): the persisted EFFECT payload
                # (result minus the runtime replayed flag), the store-computed
                # request digest (NULL when no snapshot), and the projection
                # version stamped EXPLICITLY — never relying on the DEFAULT.
                result = SupersessionResult(
                    inserted_incoming=plan.insert_incoming,
                    invalidated=len(plan.prior_invalidations),
                    refused=len(plan.refusals))
                resp_json = effect_payload(result)
                # specs/0016 D2 (0019 rider A1): post-D2 writers stamp version
                # 4 — the source_type-less snapshot era
                self.validate_receipt_state(plan_rd, 4, resp_json)  # refused at write
                self._conn.execute(
                    "INSERT INTO supersession_operations(user_id,operation_id,"
                    "logical_request_digest,status,request_digest,response,"
                    "outcome_digest_version) VALUES(?,?,?,?,?,?,?)",
                    (user_id, plan.operation_id, digest, "applied",
                     plan_rd, resp_json, 4))
                self._bump(user_id)                   # a recall-bearing edge changed
                # A live_refusal_contention transition — INTO it (this plan records a
                # refusal) OR OUT of it (this plan retires an edge that a refusal row
                # references) — is a derived-view invalidation event, symmetric per
                # round-10 blocker 1. Drop the wiki cache in the SAME commit (§4c-ii,
                # immediate not batched). The refusal rows still reference a retired
                # member (retention is "while either edge exists"), so the resolution
                # check reads them post-invalidation.
                touches_contention = bool(plan.refusals) or any(
                    self._edge_in_refusal(user_id, eid)
                    for eid, _at, _reason in plan.prior_invalidations)
                if touches_contention:
                    self._conn.execute("DELETE FROM wiki WHERE user_id=?", (user_id,))
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            return result

    def refusals(self, user_id: str) -> list[SupersessionRefusal]:
        rows = self._conn.execute(
            "SELECT refusal_id,user_id,prior_edge_id,incoming_edge_id,relation,"
            "prior_effective,incoming_effective,rule_version,created_at "
            "FROM supersession_refusals WHERE user_id=? "
            "ORDER BY created_at DESC, refusal_id DESC", (user_id,)).fetchall()
        return [SupersessionRefusal(
            refusal_id=r[0], user_id=r[1], prior_edge_id=r[2], incoming_edge_id=r[3],
            relation=r[4], prior_effective=r[5], incoming_effective=r[6],
            rule_version=r[7], created_at=r[8]) for r in rows]

    # -- the contribution ledger (specs/0014 §4a/§4b/§4d) -------------------
    def _write_contribution(self, user_id: str, draft, plan) -> None:
        """Derive and INSERT one absorption ledger row from a reference-only
        draft (R2-1), inside the consuming transaction, BEFORE the contributor
        is invalidated. Everything is read from authoritative rows; the closed
        §4a schema is validated as a self-check (a failure aborts the op, A7)."""
        from ..contribution import (canonical_payload, evidence_ref_digest,
                                    validate_payload)
        from ..source_identity import resolve_origin, source_identity_digest
        if draft.site != "absorption":
            raise SupersessionIntegrityError(
                f"site {draft.site!r} cannot appear on the supersession path — "
                f"consolidation rows are store-derived at the cutover (0014 §4b)")
        if plan.absorption_pre_image is None:
            raise SupersessionIntegrityError(
                "an absorption draft requires the plan's absorption_pre_image "
                "(specs/0014 §4b R3-1)")
        row = self._conn.execute(
            "SELECT json FROM edges WHERE id=?", (draft.contributor_id,)).fetchone()
        if row is None:
            raise SupersessionIntegrityError(
                f"draft contributor {draft.contributor_id!r} does not resolve to a "
                f"row this transaction is consuming (0014 §4b)")
        contributor = Edge.model_validate_json(row[0])
        if contributor.user_id != user_id:
            raise SupersessionIntegrityError(
                "draft contributor belongs to another tenant (0014 §4b)")
        local = self.local_origin()
        ident = source_identity_digest(
            resolve_origin(contributor.provenance.origin, local),
            contributor.provenance.source_id)
        ev = evidence_ref_digest(
            resolve_origin(contributor.provenance.origin, local),
            contributor.provenance.evidence_ref)
        from ..contribution import json_datetime
        side = {
            "observed_at": json_datetime(contributor.provenance.observed_at),
            "confidence": contributor.provenance.confidence,
            "valid_from": json_datetime(contributor.valid_from),
            "disclosure": contributor.provenance.disclosure.value,
        }
        if contributor.provenance.derived_from is not None:
            side["derived_from"] = contributor.provenance.derived_from.value
        payload = {"base": dict(plan.absorption_pre_image), "contributor": side}
        validate_payload("absorption", payload)
        # 0021 §7b (the 0014 amendment, clause 3) / the 0019 rider: the TYPED
        # CONTRIBUTOR LINK — persisted on every new native absorption row from
        # the fields the shipped draft ALREADY carries (draft `contributor_id`
        # -> column `contributor_ref`); legacy rows stay NULL. The accepted
        # {base, contributor} payload above is NOT amended.
        self._conn.execute(
            "INSERT INTO contribution_ledger(id,user_id,survivor_type,survivor_id,"
            "site,identity_digest,evidence_ref_digest,payload,op_key,created_at,"
            "contributor_type,contributor_ref) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"contrib-{uuid.uuid4().hex[:12]}", user_id, draft.survivor_type,
             draft.survivor_id, "absorption", ident, ev,
             canonical_payload(payload), None, self._now().isoformat(),
             draft.contributor_type, draft.contributor_id))
        # specs/0019: the contributor's authoritative flag feeds the caller's
        # N-ary OR verification (U2b) — read from the row this transaction is
        # consuming, never from the draft.
        return contributor.ungrounded

    def _write_consolidation_contributions(self, op) -> None:
        """specs/0014 §4b/§4c: the N×M rows at the OUTPUTS_DURABLE cutover —
        every claimed input × every written output, derived wholly by the store
        (the claimed set and the bound outputs are both store-known, so the set
        is exact by construction). Runs INSIDE the cutover transaction, while
        the claimed inputs are still readable. Idempotent under recovery via the
        persisted op_key (R2-2): a key hit VERIFIES field-for-field (R3-3) —
        a true retry no-ops, any mismatch aborts."""
        from ..contribution import (canonical_payload, consolidation_op_key,
                                    evidence_ref_digest, validate_payload)
        from ..source_identity import resolve_origin, source_identity_digest
        bound = [ep for _, ep in
                 self._episodes_for_operation(op.user_id, op.operation_id)
                 if ep.lineage]
        outputs = list(enumerate(bound))   # index over OUTPUTS only, write order
        local = self.local_origin()
        now = self._now().isoformat()
        for _, out_ep in outputs:
            idx = out_ep.consolidation_output_index
            if idx is None:
                raise SupersessionIntegrityError(
                    f"output {out_ep.id!r} reached the cutover without a "
                    f"store-assigned index (0014 §4c)")
            for eid in op.claimed_ids:
                row = self._conn.execute(
                    "SELECT json FROM episodes WHERE id=? AND user_id=?",
                    (eid, op.user_id)).fetchone()
                if row is None:
                    raise SupersessionIntegrityError(
                        f"claimed input {eid!r} vanished before the cutover — the "
                        f"N×M contribution set cannot be complete (0014 §4b/A7)")
                inp = Episode.model_validate_json(row[0])
                ident = source_identity_digest(
                    resolve_origin(inp.provenance.origin, local),
                    inp.provenance.source_id)
                ev = evidence_ref_digest(
                    resolve_origin(inp.provenance.origin, local),
                    inp.provenance.evidence_ref)
                from ..contribution import json_datetime
                side = {
                    "observed_at": json_datetime(inp.provenance.observed_at),
                    "confidence": inp.provenance.confidence,
                    "disclosure": inp.provenance.disclosure.value,
                    "author_of_evidence": inp.provenance.author_of_evidence.value,
                    "date": inp.date,
                }
                if inp.provenance.derived_from is not None:
                    side["derived_from"] = inp.provenance.derived_from.value
                payload = {"input": side, "output_index": idx}
                validate_payload("consolidation", payload)
                key = consolidation_op_key(op.operation_id, idx, "episode", eid)
                canon = canonical_payload(payload)
                existing = self._conn.execute(
                    "SELECT user_id,survivor_type,survivor_id,site,identity_digest,"
                    "evidence_ref_digest,payload FROM contribution_ledger "
                    "WHERE op_key=?", (key,)).fetchone()
                if existing is not None:
                    # R3-3: a conflict VERIFIES, never ignores — append-only (A8)
                    want = (op.user_id, "episode", out_ep.id, "consolidation",
                            ident, ev, canon)
                    if tuple(existing) != want:
                        raise SupersessionIntegrityError(
                            f"op_key {key!r} exists with DIFFERENT deterministic "
                            f"fields — a mis-keyed second output would lose its "
                            f"attribution invisibly (0014 §4a R3-3)")
                    continue
                # The contributor columns stay NULL here: the 0021 §7b typed link
                # is scoped to the draft-carried plan/absorption sites, and the
                # R3-3 verify above compares the deterministic fields of PRE-v8
                # rows — a recovered op resuming across the v7→v8 migration must
                # keep matching its own legacy rows (NULL) field-for-field.
                self._conn.execute(
                    "INSERT INTO contribution_ledger(id,user_id,survivor_type,"
                    "survivor_id,site,identity_digest,evidence_ref_digest,payload,"
                    "op_key,created_at,contributor_type,contributor_ref) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (f"contrib-{uuid.uuid4().hex[:12]}", op.user_id, "episode",
                     out_ep.id, "consolidation", ident, ev, canon, key, now,
                     None, None))

    @staticmethod
    def _contribution_record(r):
        import json as _json
        from ..schema import ContributionRecord
        return ContributionRecord(
            id=r[0], user_id=r[1], survivor_type=r[2], survivor_id=r[3],
            site=r[4], identity_digest=r[5], evidence_ref_digest=r[6],
            payload=_json.loads(r[7]), op_key=r[8], created_at=r[9],
            contributor_type=r[10], contributor_ref=r[11])

    _CONTRIB_COLS = ("id,user_id,survivor_type,survivor_id,site,identity_digest,"
                     "evidence_ref_digest,payload,op_key,created_at,"
                     "contributor_type,contributor_ref")

    def contributions(self, user_id: str, survivor_type: str,
                      survivor_id: str) -> list:
        """§4d: every contributor consumed into a survivor, newest first —
        type-keyed (R1-5: an Edge and an Episode sharing a raw id never merge)."""
        rows = self._conn.execute(
            f"SELECT {self._CONTRIB_COLS} FROM contribution_ledger "
            "WHERE user_id=? AND survivor_type=? AND survivor_id=? "
            "ORDER BY created_at DESC, id DESC",
            (user_id, survivor_type, survivor_id)).fetchall()
        return [self._contribution_record(r) for r in rows]

    def contributions_naming(self, user_id: str, contributor_ref: str) -> list:
        """specs/0021 §7b: every ledger row whose typed `contributor_ref`
        NAMES the given record — the export path's reverse join
        (`derive_absorbed_by`). Pre-v8 rows carry NULL `contributor_ref` and
        never match (the disclosed legacy class)."""
        rows = self._conn.execute(
            "SELECT survivor_type,survivor_id,site,payload,contributor_ref "
            "FROM contribution_ledger WHERE user_id=? AND contributor_ref=? "
            "ORDER BY created_at DESC, id DESC",
            (user_id, contributor_ref)).fetchall()
        return [{"survivor_type": r[0], "survivor_id": r[1], "site": r[2],
                 "payload": json.loads(r[3]), "contributor_ref": r[4]}
                for r in rows]

    def contributors_of_source(self, user_id: str, identity_digest: str) -> list:
        """§4d: every survivor a source contributed to — revoke_source's
        blast-radius join (A9). COMPLETE identities only: a NULL digest never
        joins (F1/I13), enforced by the NOT-NULL bind here."""
        if identity_digest is None:
            return []
        rows = self._conn.execute(
            f"SELECT {self._CONTRIB_COLS} FROM contribution_ledger "
            "WHERE user_id=? AND identity_digest=? "
            "ORDER BY created_at DESC, id DESC",
            (user_id, identity_digest)).fetchall()
        return [self._contribution_record(r) for r in rows]

    def _drop_contributions_for_survivor(self, user_id: str, survivor_type: str,
                                         survivor_id: str) -> None:
        """A10: a ledger row is kept while its survivor exists and dropped when
        the survivor is — type-keyed, so a same-raw-id Edge/Episode pair deletes
        independently (R1-5)."""
        self._conn.execute(
            "DELETE FROM contribution_ledger WHERE user_id=? AND survivor_type=? "
            "AND survivor_id=?", (user_id, survivor_type, survivor_id))

    # -- episodes ----------------------------------------------------------
    def add_episode(self, episode: Episode) -> None:
        # specs/0014 §4c: store-assigned identity cannot be fabricated — a
        # caller-supplied consolidation_output_index on the generic path is
        # REFUSED; only write_consolidation_output_if_current assigns it.
        if episode.consolidation_output_index is not None:
            raise ValueError(
                f"add_episode refuses episode {episode.id!r} with a "
                f"caller-supplied consolidation_output_index — the index is "
                f"store-assigned by the consolidation primitive only "
                f"(specs/0014 §4c)")
        # specs/0009 H14: outcome-chain rows carry append-only trust state (seq,
        # supersedes_episode, authorship) and may enter ONLY through the sanctioned
        # writers — `append_outcome_if_head` (runtime) or `commit_outcome_import_plan`
        # (import) — never the generic, replace-capable mutator. This refusal is the
        # fence: it closes caller-minted seqs, head-siblings, AND an INSERT-OR-REPLACE
        # of an existing outcome id (the unfenced-door class, cf. 0010 X21).
        if episode.kind == "outcome":
            raise ValueError(
                f"add_episode refuses kind=='outcome' episode {episode.id!r} — "
                f"outcome-chain links enter only via append_outcome_if_head or "
                f"commit_outcome_import_plan (specs/0009 H14)")
        # specs/0010 X18: the generic mutator cannot FABRICATE claimed/provisional/output
        # state — those fields are store-minted by the fenced consolidation primitives.
        if (episode.claimed_by is not None or episode.operation_id is not None
                or episode.lineage):
            raise ValueError(
                f"add_episode refuses episode {episode.id!r} carrying consolidation "
                f"state (claimed_by/operation_id/lineage) — that state is minted only "
                f"by the fenced consolidation primitives (specs/0010 X18)")
        # specs/0010 X19: a LIVE episode id can never inhabit the historical namespace
        # that finalized lineage ids live in, so the two can never collide.
        if is_historical_id(episode.id):
            raise ValueError(
                f"add_episode refuses id {episode.id!r} — the '{episode.id[:5]}' "
                f"namespace is reserved for historical lineage ids (specs/0010 X19)")
        with self._lock:
            # specs/0010 X21: an id RESERVED by a non-quiescent op is refused — the
            # reservation survives the input's physical deletion until the op finalizes
            # or cleanly abandons (so a deleted-but-reserved id cannot be recreated).
            if episode.id in self._reserved_ids(episode.user_id):
                raise ValueError(
                    f"add_episode refuses reserved id {episode.id!r} — it is claimed by "
                    f"an in-flight consolidation (specs/0010 X21)")
            self._conn.execute(
                "INSERT OR REPLACE INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                (episode.id, episode.user_id, episode.date, episode.model_dump_json()))
            self._bump(episode.user_id)
            self._conn.commit()

    def episodes(self, user_id, *, limit=None) -> list[Episode]:
        # specs/0010 X9: every ordinary read sees EXACTLY ONE complete representation —
        # all relevant inputs, or all committed outputs, never both and never neither.
        # The episode rows and the op states are read in ONE snapshot (under the lock),
        # and provisional/hidden rows are filtered by the observed op state.
        with self._lock:
            op_state = {op.operation_id: op.state
                        for op in self._ops_for_user(user_id)}
            rows = self._conn.execute(
                "SELECT json FROM episodes WHERE user_id=? ORDER BY date",
                (user_id,)).fetchall()
        out = []
        for (blob,) in rows:
            ep = Episode.model_validate_json(blob)
            if self._ordinary_read_visible(ep, op_state):
                out.append(ep)
                if limit and len(out) >= limit:
                    break
        return out

    @staticmethod
    def _ordinary_read_visible(ep: Episode, op_state: dict) -> bool:
        """specs/0010 §4c/X9. A provisional OUTPUT is hidden while its LOCAL op is
        pre-cutover (CLAIMED/GENERATING); a finalized/absent-op output is visible (X19).
        A claimed INPUT is hidden once its op reaches OUTPUTS_DURABLE (the cutover flips
        visibility); it is visible while CLAIMED/GENERATING. Everything else is visible."""
        S = ConsolidationState
        if ep.lineage:                                   # a consolidation OUTPUT
            return op_state.get(ep.operation_id) not in (S.CLAIMED, S.GENERATING)
        if ep.operation_id is not None:                  # a claimed INPUT
            return op_state.get(ep.operation_id) is not S.OUTPUTS_DURABLE
        return True

    def delete_episode(self, episode_id) -> None:
        with self._lock:
            row = self._conn.execute(
                "SELECT user_id, json FROM episodes WHERE id=?",
                (episode_id,)).fetchone()
            # specs/0009 H14: an outcome-chain link leaves ONLY via forget_user
            # (wholesale erasure) — never a targeted delete, which would punch a
            # gap in append-only history or orphan a superseding child.
            if row is not None and Episode.model_validate_json(row[1]).kind == "outcome":
                raise ValueError(
                    f"delete_episode refuses outcome-chain link {episode_id!r} — "
                    f"outcome history is append-only and leaves only via forget_user "
                    f"(specs/0009 H14)")
            # specs/0010 X21: a reserved (claimed) input leaves only via the fenced
            # batch-delete or forget_user — never a targeted generic delete.
            if row is not None and episode_id in self._reserved_ids(row[0]):
                raise ValueError(
                    f"delete_episode refuses reserved id {episode_id!r} — it is claimed "
                    f"by an in-flight consolidation; it is removed only by the fenced "
                    f"batch-delete or forget_user (specs/0010 X21)")
            self._conn.execute("DELETE FROM episodes WHERE id=?", (episode_id,))
            if row:
                # specs/0014 A10: rows live while their survivor does — type-keyed
                self._drop_contributions_for_survivor(row[0], "episode", episode_id)
                self._bump(row[0])
            self._conn.commit()

    # -- outcome-authorship chain (specs/0009) ----------------------------------
    def _chain_head(self, user_id: str, edge_id: str, evidence_ref: str):
        """The head (max-`seq` episode) of the `(edge_id, evidence_ref)` outcome
        chain, or None. Derived — there is no materialised head pointer (H-Q2)."""
        head = None
        for r in self._conn.execute(
                "SELECT json FROM episodes WHERE user_id=?", (user_id,)):
            ep = Episode.model_validate_json(r[0])
            if (ep.kind == "outcome" and ep.edge_id == edge_id
                    and ep.provenance.evidence_ref == evidence_ref):
                if head is None or (ep.seq or 0) > (head.seq or 0):
                    head = ep
        return head

    def append_outcome_if_head(self, user_id, edge_id, evidence_ref,
                               expected_head_id, draft: OutcomeJudgmentDraft):
        """specs/0009 §4a. Atomic under `_lock` (which serialises every store
        mutation on the single connection), so the read-then-INSERT is a genuine
        compare-and-set: two concurrent callers cannot both extend one head (H3).
        INSERTs through its OWN statement, not `add_episode`, so it is a sanctioned
        outcome-chain writer even once the generic mutators refuse outcome rows (H14)."""
        with self._lock:
            head = self._chain_head(user_id, edge_id, evidence_ref)
            head_id = head.id if head is not None else None
            if head_id != expected_head_id:
                return HEAD_MOVED                       # CAS failed — caller retries
            if head is None:                            # a new chain: root
                seq, context_ref = 1, draft.context_ref
            else:
                seq = (head.seq or 0) + 1               # contiguous per-chain seq
                # context_ref: omitted → inherit; non-None must equal the chain's
                if draft.context_ref is None:
                    context_ref = head.context_ref
                elif draft.context_ref != head.context_ref:
                    raise ValueError(
                        "context_ref may not change within an outcome chain "
                        f"({draft.context_ref!r} != {head.context_ref!r})")
                else:
                    context_ref = draft.context_ref
            ep = Episode(
                id=f"ep-{uuid.uuid4().hex[:12]}", user_id=user_id,
                date=draft.event_timestamp, summary=draft.summary, kind="outcome",
                edge_id=edge_id, outcome=draft.outcome, context_ref=context_ref,
                seq=seq, supersedes_episode=expected_head_id,
                judgment_time_known=True,
                provenance=Provenance(
                    author_of_evidence=draft.author, evidence_ref=evidence_ref))
            self._conn.execute(
                "INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                (ep.id, ep.user_id, ep.date, ep.model_dump_json()))
            self._bump(user_id)                          # H10
            self._conn.commit()
            return ep

    def commit_outcome_import_plan(self, user_id, plan: dict,
                                   expected_destination_state: dict):
        """specs/0009 §4c. Atomic under `_lock` — the same single-connection
        serialisation that makes `append_outcome_if_head` a genuine CAS makes this
        whole-import commit LINEARIZE against concurrent appends: a head that moved
        between the caller's preflight and here is caught by the `chain_heads`
        re-check and the WHOLE import refuses (`DESTINATION_CHANGED`), never after a
        prefix. Installs outcome links through its OWN INSERT — a sanctioned writer
        even though the generic mutators now refuse outcome rows (H14).

        specs/0009 §4c AS AMENDED (0020/0021): `plan["contributions"]` rows —
        derived by the caller SOLELY from `reconstruct_absorption_rows`,
        pre-commit — are validated context-aware ("import" is the ONLY writer
        context this primitive owns), their op keys and row ids RE-DERIVED
        in-primitive (a caller-selected key or id refuses before any write),
        gated by `expected_destination_state["contribution_state"]`
        (absent → write; plan_row_id-set-equal → skip-as-existing; anything
        else → DESTINATION_CHANGED writing nothing), and installed in the SAME
        single atomic commit as the records."""
        from ..contribution import canonical_payload, validate_payload
        from ..scope_linkage import plan_row_id as _derive_row_id
        edges = plan.get("edges", [])
        episodes = plan.get("episodes", [])
        contributions = plan.get("contributions", [])
        # (0) validate the contribution row-plans — pure derivation checks,
        # before the lock and before ANY write. Presence first (R11-2), then
        # the ONE-minted-op rule, then the exact in-primitive derivation of
        # op_key AND row id (R13-1: keys are derived, never selected — the
        # validator inside plan_row_id consumes the op domain and requires
        # exact key equality; the id equality below closes the same door for
        # the PRIMARY-KEY-riding dedup identity).
        plan_edge_ids = {e.id for e in edges}
        contrib_by_surv: dict = {}
        import_op = None
        for row in contributions:
            missing = [f for f in ("id", "user_id", "survivor_type",
                                   "survivor_id", "op_key") if f not in row]
            if missing:
                raise ValueError(
                    f"contribution row-plan is missing {missing} — the plan "
                    f"row is TOTAL over the stored field set (0009 §4c as "
                    f"amended, R11-2)")
            if row["user_id"] != user_id:
                raise ValueError(
                    "contribution row-plan names another tenant — refused "
                    "(0009 §4c as amended)")
            if row["survivor_type"] != "edge":
                raise ValueError(
                    f"contribution row-plan survivor_type "
                    f"{row['survivor_type']!r} — the import plan sites "
                    f"attribute EDGE survivors only (0020 §4a-iii)")
            op_key = row["op_key"]
            if not isinstance(op_key, str) or ":" not in op_key:
                raise ValueError(
                    f"contribution row op_key {op_key!r} is not the "
                    f"injective {{op}}:{{site}}:{{digest}} form (R9-2)")
            op = op_key.split(":", 1)[0]
            if import_op is None:
                import_op = op
            elif op != import_op:
                raise ValueError(
                    f"contribution rows carry TWO operation ids "
                    f"({import_op!r}, {op!r}) — the import mints ONE "
                    f"op-<12hex> id (0009 §4c as amended, R7-3)")
            derived_id = _derive_row_id(user_id, "edge", row["survivor_id"],
                                        row, "import", op=op)
            if row["id"] != derived_id:
                raise ValueError(
                    f"contribution row id {row['id']!r} is not the canonical "
                    f"plan_row_id projection — the id is DERIVED in-primitive, "
                    f"never selected (0009 §4c as amended, R9-3/R13-1)")
            validate_payload(row["site"], row["payload"])   # site registry
            contrib_by_surv.setdefault(row["survivor_id"], []).append(row)
        with self._lock:
            # (1) Revalidate EVERY destination assumption the preflight reasoned
            # about (round-6 Correction B) — atomically, before any write.
            for eid, expect_present in expected_destination_state.get(
                    "edge_ids", {}).items():
                row = self._conn.execute(
                    "SELECT user_id FROM edges WHERE id=?", (eid,)).fetchone()
                present = row is not None
                if present != expect_present:
                    return DESTINATION_CHANGED       # created/removed under us
                if present and row[0] != user_id:
                    return DESTINATION_CHANGED       # ownership changed under us
            for ep_id, expect_json in expected_destination_state.get(
                    "episode_records", {}).items():
                row = self._conn.execute(
                    "SELECT json FROM episodes WHERE id=?", (ep_id,)).fetchone()
                current = row[0] if row is not None else None
                if current != expect_json:           # RECORD equality, not id
                    return DESTINATION_CHANGED
            for (edge_id, evidence_ref), expect_head in \
                    expected_destination_state.get("chain_heads", {}).items():
                head = self._chain_head(user_id, edge_id, evidence_ref)
                head_id = head.id if head is not None else None
                if head_id != expect_head:           # linearize vs append_outcome_if_head
                    return DESTINATION_CHANGED
            # (1b) 0009 §4c as amended: the contribution gate — EVERY decision
            # is taken here, BEFORE any write, so DESTINATION_CHANGED writes
            # nothing (records included). Per survivor: the current row-id set
            # must equal the caller's expected `contribution_state` (drift is
            # a lost race); then ABSENT → write, plan_row_id-set-EQUAL → skip
            # as existing, anything else → a different recorded history,
            # refused whole.
            contribution_state = expected_destination_state.get(
                "contribution_state", {})
            contrib_writes: list = []
            contrib_existing = 0
            for surv, rows in sorted(contrib_by_surv.items()):
                if surv not in plan_edge_ids:
                    hit = self._conn.execute(
                        "SELECT user_id FROM edges WHERE id=?",
                        (surv,)).fetchone()
                    if hit is None or hit[0] != user_id:
                        raise ValueError(
                            f"contribution rows attribute survivor {surv!r}, "
                            f"which is neither a plan record nor an "
                            f"already-present record of this user — the "
                            f"preflight refuses (0009 §4c as amended)")
                current = {r[0] for r in self._conn.execute(
                    "SELECT id FROM contribution_ledger WHERE user_id=? AND "
                    "survivor_type='edge' AND survivor_id=?",
                    (user_id, surv)).fetchall()}
                if current != set(contribution_state.get(surv, ())):
                    return DESTINATION_CHANGED       # rows moved under us
                planned = {r["id"] for r in rows}
                if current == planned:
                    contrib_existing += len(rows)    # idempotent re-import
                elif not current:
                    contrib_writes.extend(rows)
                else:
                    # different contributors or a different history SHAPE —
                    # a different history, refused whole, writing NOTHING
                    return DESTINATION_CHANGED
            # (2) Install ALL records as one logical commit (edges before episodes so
            # an outcome link's edge_id always resolves; contribution rows ride
            # the SAME transaction — nothing is durable after a prefix).
            try:
                for edge in edges:
                    self._conn.execute(
                        "INSERT OR REPLACE INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                        "VALUES(?,?,?,?,?,?,?,?)",
                        (edge.id, edge.user_id, edge.subject, edge.relation, edge.object,
                         int(edge.active), int(edge.quarantined), edge.model_dump_json()))
                for ep in episodes:
                    self._conn.execute(
                        "INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                        (ep.id, ep.user_id, ep.date, ep.model_dump_json()))
                now = self._now().isoformat()
                for row in contrib_writes:
                    self._conn.execute(
                        "INSERT INTO contribution_ledger(id,user_id,"
                        "survivor_type,survivor_id,site,identity_digest,"
                        "evidence_ref_digest,payload,op_key,created_at,"
                        "contributor_type,contributor_ref) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (row["id"], user_id, "edge", row["survivor_id"],
                         row["site"], row["identity_digest"],
                         row["evidence_ref_digest"],
                         canonical_payload(row["payload"]), row["op_key"],
                         now, row["contributor_type"],
                         row["contributor_ref"]))
                self._bump(user_id)
            except BaseException:
                self._conn.rollback()                # ONE atomic commit —
                raise                                # nothing after a prefix
            self._conn.commit()
            return {"edges": len(edges), "episodes": len(episodes),
                    "contributions": len(contrib_writes),
                    "contributions_existing": contrib_existing}

    # -- crash-safe consolidation (specs/0010) --------------------------------
    _OP_COLS = ("operation_id", "user_id", "fence", "state", "owner",
                "lease_duration", "lease_expires_at", "claimed_ids")

    def _now(self) -> datetime:
        return self._clock()

    def _op_from_row(self, row) -> ConsolidationOp:
        return ConsolidationOp(
            operation_id=row[0], user_id=row[1], fence=row[2],
            state=ConsolidationState(row[3]), owner=row[4], lease_duration=row[5],
            lease_expires_at=row[6], claimed_ids=json.loads(row[7]))

    def _load_op(self, operation_id: str) -> Optional[ConsolidationOp]:
        row = self._conn.execute(
            f"SELECT {', '.join(self._OP_COLS)} FROM consolidation_ops "
            f"WHERE operation_id=?", (operation_id,)).fetchone()
        return self._op_from_row(row) if row is not None else None

    def _ops_for_user(self, user_id: str) -> list:
        return [self._op_from_row(r) for r in self._conn.execute(
            f"SELECT {', '.join(self._OP_COLS)} FROM consolidation_ops "
            f"WHERE user_id=?", (user_id,)).fetchall()]

    def _next_fence(self) -> int:
        return self._conn.execute(
            "SELECT COALESCE(MAX(fence), 0) + 1 FROM consolidation_ops").fetchone()[0]

    def _lease_live(self, op: ConsolidationOp) -> bool:
        return self._now() < datetime.fromisoformat(op.lease_expires_at)

    def _reserved_ids(self, user_id: str) -> set:
        """Every id claimed by a NON-QUIESCENT op (specs/0010 X21). Derived from
        `claimed_ids`, not physical presence, so the reservation survives the fenced
        batch-delete until the op reaches FINALIZED or clean ABANDONED."""
        reserved: set = set()
        for op in self._ops_for_user(user_id):
            if op.state in RECOVERY_PENDING_STATES:
                reserved.update(op.claimed_ids)
        return reserved

    def _write_op(self, op: ConsolidationOp) -> None:
        self._conn.execute(
            f"INSERT OR REPLACE INTO consolidation_ops({', '.join(self._OP_COLS)}) "
            f"VALUES(?,?,?,?,?,?,?,?)",
            (op.operation_id, op.user_id, op.fence, op.state.value, op.owner,
             op.lease_duration, op.lease_expires_at, json.dumps(op.claimed_ids)))

    def _episodes_for_operation(self, user_id: str, operation_id: str) -> list:
        """(episode_id, Episode) for every row physically tagged `operation_id` — both
        claimed INPUTS (claimed_by set, no lineage) and provisional OUTPUTS (lineage
        set). Parsed from the json blob, since operation_id is not a column."""
        out = []
        for eid, blob in self._conn.execute(
                "SELECT id, json FROM episodes WHERE user_id=?", (user_id,)):
            ep = Episode.model_validate_json(blob)
            if ep.operation_id == operation_id:
                out.append((eid, ep))
        return out

    def _claim_inputs(self, op: ConsolidationOp) -> None:
        """Tag each claimed input with `claimed_by`/`operation_id` (X4, atomic under the
        caller's lock+transaction). Every id must exist and belong to the op's user."""
        for eid in op.claimed_ids:
            row = self._conn.execute(
                "SELECT json FROM episodes WHERE id=? AND user_id=?",
                (eid, op.user_id)).fetchone()
            if row is None:
                raise ValueError(f"cannot claim {eid!r}: not an episode of "
                                 f"{op.user_id!r} (specs/0010 §4a)")
            ep = Episode.model_validate_json(row[0])
            bound = ep.model_copy(update={"claimed_by": op.operation_id,
                                          "operation_id": op.operation_id})
            self._conn.execute("UPDATE episodes SET json=? WHERE id=?",
                               (bound.model_dump_json(), eid))

    def _abandon(self, op: ConsolidationOp) -> None:
        """§4b-iii cleanup, under the caller's lock+transaction: delete every
        provisional OUTPUT row for the op, CLEAR the claim fields on every claimed INPUT
        row (never 'all rows' — inputs carry operation_id too), then mark ABANDONED."""
        for eid, ep in self._episodes_for_operation(op.user_id, op.operation_id):
            if ep.lineage:                                   # a provisional output
                self._conn.execute("DELETE FROM episodes WHERE id=?", (eid,))
            else:                                            # a claimed input
                clean = ep.model_copy(update={"claimed_by": None, "operation_id": None})
                self._conn.execute("UPDATE episodes SET json=? WHERE id=?",
                                   (clean.model_dump_json(), eid))
        self._write_op(op.model_copy(update={"state": ConsolidationState.ABANDONED}))

    def create_or_takeover_consolidation(self, user_id, ids, owner, lease_duration):
        if not (0 < lease_duration <= LEASE_MAX):
            raise ValueError(f"lease_duration must be in (0, {LEASE_MAX}], "
                             f"not {lease_duration} (specs/0010 §4a-ii)")
        req = list(dict.fromkeys(ids))          # de-dup, preserve order
        req_set = set(req)
        with self._lock:
            # Recovery race rule (§4a-ii): abandon any EXPIRED pre-cutover op that
            # intersects the request BEFORE claiming, so a new fence issues only from a
            # clean ABANDONED state (X15). Re-evaluate until no expired intersection.
            while True:
                ops = self._ops_for_user(user_id)
                intersecting = [op for op in ops
                                if op.state in RECOVERY_PENDING_STATES
                                and req_set & set(op.claimed_ids)]
                live = [op for op in intersecting
                        if op.state == ConsolidationState.OUTPUTS_DURABLE
                        or self._lease_live(op)]
                if live:
                    return None                  # contended (X7/X11 — no partial claim)
                if intersecting:                 # all expired pre-cutover → clean first
                    for op in intersecting:
                        self._abandon(op)
                    continue
                break
            # A CLEAN ABANDONED op covering EXACTLY these ids is revived under a NEW
            # fence; otherwise a fresh operation is created (X15).
            revivable = next(
                (op for op in ops if op.state == ConsolidationState.ABANDONED
                 and set(op.claimed_ids) == req_set), None)
            fence = self._next_fence()
            expires = (self._now() + timedelta(seconds=lease_duration)).isoformat()
            op = ConsolidationOp(
                operation_id=(revivable.operation_id if revivable
                              else f"op-{uuid.uuid4().hex[:12]}"),
                user_id=user_id, fence=fence, state=ConsolidationState.CLAIMED,
                owner=owner, lease_duration=lease_duration,
                lease_expires_at=expires, claimed_ids=req)
            self._claim_inputs(op)               # all-or-nothing under this transaction
            self._write_op(op)
            self._conn.commit()
            return op

    def renew_consolidation_lease(self, operation_id, fence, owner) -> bool:
        with self._lock:
            op = self._load_op(operation_id)
            if (op is None or op.fence != fence or op.owner != owner
                    or op.state not in (ConsolidationState.CLAIMED,
                                        ConsolidationState.GENERATING)
                    or not self._lease_live(op)):        # cannot resurrect an expired lease
                return False
            expires = (self._now() + timedelta(seconds=op.lease_duration)).isoformat()
            self._write_op(op.model_copy(update={"lease_expires_at": expires}))
            self._conn.commit()
            return True

    def write_consolidation_output_if_current(self, operation_id, fence, owner,
                                              draft: ConsolidationOutputDraft) -> bool:
        with self._lock:
            op = self._load_op(operation_id)
            if (op is None or op.fence != fence or op.owner != owner
                    or op.state != ConsolidationState.GENERATING
                    or not self._lease_live(op)):
                return False
            inputs = []
            for eid in op.claimed_ids:
                row = self._conn.execute(
                    "SELECT json FROM episodes WHERE id=? AND user_id=?",
                    (eid, op.user_id)).fetchone()
                if row is not None:
                    inputs.append(Episode.model_validate_json(row[0]))
            # X23: every derived field is STORE-computed from the claimed set, not the
            # draft/LLM — min trust across the whole set (N9b) and the true date range.
            prov, date_start, date_end = self._derive_output_metadata(inputs, operation_id)
            # specs/0014 §4c: the STORE assigns the output index — the count of
            # outputs already written for this operation (sequential from 0,
            # contiguous by construction; asserted below as the local-op
            # invariant). Only this primitive ever sets the field.
            existing = [e for _, e in
                        self._episodes_for_operation(op.user_id, operation_id)
                        if e.lineage]
            next_index = len(existing)
            assert sorted(
                e.consolidation_output_index for e in existing) == list(
                range(next_index)), "output indices must be contiguous 0..M-1"
            ep = Episode(
                id=f"epc-{uuid.uuid4().hex[:12]}", user_id=op.user_id,
                date=date_start, summary=draft.summary, date_start=date_start,
                date_end=date_end, operation_id=operation_id,
                lineage=[to_historical_id(i) for i in op.claimed_ids],
                consolidation_output_index=next_index,
                provenance=prov)
            # INSERT — never replace (X22): a minted-id collision is a store error.
            self._conn.execute(
                "INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                (ep.id, ep.user_id, ep.date, ep.model_dump_json()))
            self._conn.commit()                  # provisional + hidden until cutover
            return True

    def _derive_output_metadata(self, inputs, operation_id):
        """(Provenance, date_start, date_end) for a consolidation output, computed from
        the claimed inputs (specs/0010 §4d/§4d-ii/X23 — mirrors lifecycle's whole-set
        minimum-trust rule). Empty inputs cannot occur on the write path (a GENERATING
        op holds visible inputs), but guard defensively."""
        _RANK = {Disclosure.QUARANTINED: 0, Disclosure.USE_ONLY: 1,
                 Disclosure.MENTIONABLE: 2}
        base = inputs[0].provenance if inputs else Provenance(
            author_of_evidence=EvidenceAuthor.SYSTEM,
            evidence_ref=operation_id)
        influenced = any(e.provenance.third_party_influenced for e in inputs)
        weakest = (min(inputs, key=lambda e: _RANK[e.provenance.disclosure])
                   .provenance.disclosure if inputs else base.disclosure)
        prov = base.model_copy(update={
            "author_of_evidence": EvidenceAuthor.SYSTEM,
            "evidence_ref": operation_id,
            "derived_from": (EvidenceAuthor.THIRD_PARTY if influenced
                             else base.derived_from),
            "disclosure": weakest,
            "confidence": (min(e.provenance.confidence for e in inputs)
                           if inputs else base.confidence),
            "observed_at": (max(e.provenance.observed_at for e in inputs)
                            if inputs else base.observed_at)})
        dates = sorted(e.date for e in inputs) if inputs else [""]
        return prov, dates[0], dates[-1]

    def transition_consolidation_if_current(self, operation_id, fence, owner,
                                            to_state) -> bool:
        to_state = ConsolidationState(to_state)
        with self._lock:
            op = self._load_op(operation_id)
            if op is None or op.fence != fence:
                return False
            S = ConsolidationState
            if to_state is S.GENERATING:
                if (op.state is not S.CLAIMED or op.owner != owner
                        or not self._lease_live(op)):
                    return False
                self._write_op(op.model_copy(update={"state": S.GENERATING}))
            elif to_state is S.OUTPUTS_DURABLE:
                if (op.state is not S.GENERATING or op.owner != owner
                        or not self._lease_live(op)):
                    return False
                # X22: refuse the cutover unless ≥1 correctly-bound output exists
                bound = [ep for _, ep in
                         self._episodes_for_operation(op.user_id, operation_id)
                         if ep.lineage]
                if not bound:
                    return False
                # specs/0014 §4b/§4c: the N×M contribution rows are written AT
                # the cutover, in this same transaction, while the claimed inputs
                # are still readable (they are deleted only after OUTPUTS_DURABLE).
                self._write_consolidation_contributions(op)
                self._write_op(op.model_copy(update={"state": S.OUTPUTS_DURABLE}))
                self._bump(op.user_id)           # X14: the visibility cutover bumps
            elif to_state is S.FINALIZED:
                if op.state is not S.OUTPUTS_DURABLE:     # ownerless, recovery-safe
                    return False
                # X20: unreachable until every claimed input is deleted
                remaining = self._conn.execute(
                    "SELECT COUNT(*) FROM episodes WHERE user_id=? AND id IN ({})".format(
                        ",".join("?" * len(op.claimed_ids))),
                    (op.user_id, *op.claimed_ids)).fetchone()[0] if op.claimed_ids else 0
                if remaining > 0:
                    return False
                self._write_op(op.model_copy(update={"state": S.FINALIZED}))
            else:
                return False
            self._conn.commit()
            return True

    def delete_claimed_inputs_if_current(self, operation_id, fence) -> bool:
        with self._lock:
            op = self._load_op(operation_id)
            if (op is None or op.fence != fence
                    or op.state is not ConsolidationState.OUTPUTS_DURABLE):
                return False
            for eid in op.claimed_ids:           # idempotent all-or-nothing re-delete
                self._conn.execute(
                    "DELETE FROM episodes WHERE id=? AND user_id=?", (eid, op.user_id))
            self._conn.commit()
            return True

    def abandon_consolidation_if_current(self, operation_id, fence) -> bool:
        with self._lock:
            op = self._load_op(operation_id)
            if (op is None or op.fence != fence
                    or op.state not in (ConsolidationState.CLAIMED,
                                        ConsolidationState.GENERATING)
                    or self._lease_live(op)):    # expired-lease only (X7)
                return False
            self._abandon(op)
            self._conn.commit()
            return True

    def pending_consolidations(self, user_id) -> list:
        with self._lock:
            return [op for op in self._ops_for_user(user_id)
                    if op.state in RECOVERY_PENDING_STATES]

    def quiescent_episode_snapshot(self, user_id):
        # X17: ONE atomic observation — the quiescence check and the episode snapshot
        # under the same lock, linearizable against create_or_takeover_consolidation.
        with self._lock:
            if any(op.state in RECOVERY_PENDING_STATES
                   for op in self._ops_for_user(user_id)):
                return NON_QUIESCENT
            return [Episode.model_validate_json(r[0]) for r in self._conn.execute(
                "SELECT json FROM episodes WHERE user_id=? ORDER BY date", (user_id,))]

    # -- host/admin queries ---------------------------------------------------
    def list_users(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT user_id, SUM(e), SUM(p) FROM ("
            "  SELECT user_id, COUNT(*) AS e, 0 AS p FROM edges GROUP BY user_id"
            "  UNION ALL"
            "  SELECT user_id, 0, COUNT(*) FROM episodes GROUP BY user_id"
            ") GROUP BY user_id ORDER BY user_id").fetchall()
        return [{"user_id": u, "edges": int(e or 0), "episodes": int(p or 0)}
                for u, e, p in rows]

    # -- compliance erasure -------------------------------------------------
    def forget_user(self, user_id) -> dict:
        with self._lock:
            n_edges = self._conn.execute(
                "SELECT COUNT(*) FROM edges WHERE user_id=?", (user_id,)).fetchone()[0]
            n_eps = self._conn.execute(
                "SELECT COUNT(*) FROM episodes WHERE user_id=?", (user_id,)).fetchone()[0]
            # specs/0008 §6d: the data-subject erasure deletes the confirmations
            # too — they are removed with the edges they belong to — and COUNTS them.
            n_conf = self._conn.execute(
                "SELECT COUNT(*) FROM confirmations WHERE user_id=?",
                (user_id,)).fetchone()[0]
            # specs/0010 X17: consolidation operation state is per-user erasable data —
            # forget_user removes it atomically with the rest of the user's memory.
            # specs/0003 §4f: the refusal inventory and the operation receipts are
            # user-linked Store-local metadata, so erasure covers them too.
            for table in ("contribution_ledger",
                          "edges", "episodes", "wiki", "write_counter",
                          "confirmations", "consolidation_ops",
                          "supersession_refusals", "supersession_operations"):
                self._conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
            self._conn.commit()
        return {"edges": n_edges, "episodes": n_eps, "confirmations": n_conf}

    # -- compiled-view cache ----------------------------------------------
    def get_wiki(self, user_id) -> Optional[tuple[str, int]]:
        row = self._conn.execute("SELECT text, store_version FROM wiki WHERE user_id=?",
                                 (user_id,)).fetchone()
        return (row[0], row[1]) if row else None

    def set_wiki(self, user_id, text, store_version) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO wiki(user_id,text,store_version) VALUES(?,?,?)",
                (user_id, text, store_version))
            self._conn.commit()

    def store_version(self, user_id) -> int:
        row = self._conn.execute("SELECT n FROM write_counter WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else 0

    def close(self) -> None:
        self._conn.close()
