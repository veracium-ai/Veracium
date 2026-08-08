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
                      Provenance, RECOVERY_PENDING_STATES, SourceType,
                      SupersessionPlan, SupersessionRefusal, SupersessionResult,
                      is_historical_id, to_historical_id)
from .base import (DESTINATION_CHANGED, HEAD_MOVED, LEASE_MAX, NON_QUIESCENT,
                   PLAN_STALE, Store, SupersessionIntegrityError)
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
            if (Edge.model_validate_json(prior[1]).needs_confirmation
                    and not edge.needs_confirmation):
                raise ValueError(
                    f"cannot clear needs_confirmation (True→False) on "
                    f"edge {edge.id!r} — only confirm_edge may (specs/0008 §6d, C1)")
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
                                 source_type=SourceType.STATED,
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
        inc = plan.incoming_edge
        payload = {
            "incoming": [inc.id, inc.object,
                         inc.provenance.author_of_evidence.value,
                         inc.provenance.derived_from.value if inc.provenance.derived_from else None],
            "insert_incoming": plan.insert_incoming,
            "upserts": sorted(e.id for e in plan.prior_upserts),
            "invalidations": sorted([eid, reason] for eid, _at, reason in plan.prior_invalidations),
            "refusals": sorted([r.prior_edge_id, r.incoming_edge_id] for r in plan.refusals),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def apply_supersession_plan(self, plan: SupersessionPlan):
        inc = plan.incoming_edge
        user_id = inc.user_id
        digest = self._logical_request_digest(plan)
        with self._lock:
            # 1. receipt check — PRECEDES the CAS check, so a committed op REPLAYS rather
            #    than tripping PlanStale on its own now-stale expected_state (§4f, r9 B3).
            row = self._conn.execute(
                "SELECT logical_request_digest FROM supersession_operations "
                "WHERE user_id=? AND operation_id=?", (user_id, plan.operation_id)).fetchone()
            if row is not None:
                if row[0] != digest:
                    raise SupersessionIntegrityError(
                        f"operation_id {plan.operation_id!r} already committed a DIFFERENT "
                        f"logical operation for user {user_id!r} — a reused id is a caller "
                        f"integrity bug, not a race (specs/0003 §4f)")
                refused = self._conn.execute(
                    "SELECT COUNT(*) FROM supersession_refusals "
                    "WHERE user_id=? AND incoming_edge_id=?", (user_id, inc.id)).fetchone()[0]
                return SupersessionResult(
                    inserted_incoming=plan.insert_incoming,
                    invalidated=len(plan.prior_invalidations), refused=refused, replayed=True)
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
                # the durable receipt commits atomically with the effects (§4f idempotency)
                self._conn.execute(
                    "INSERT INTO supersession_operations(user_id,operation_id,"
                    "logical_request_digest,status) VALUES(?,?,?,?)",
                    (user_id, plan.operation_id, digest, "applied"))
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
            return SupersessionResult(
                inserted_incoming=plan.insert_incoming,
                invalidated=len(plan.prior_invalidations), refused=len(plan.refusals))

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

    # -- episodes ----------------------------------------------------------
    def add_episode(self, episode: Episode) -> None:
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
                self._bump(row[0])
            self._conn.commit()

    # -- outcome-authorship chain (specs/0009) ----------------------------------
    _AUTHOR_SOURCE = {EvidenceAuthor.USER: SourceType.STATED,
                      EvidenceAuthor.SYSTEM: SourceType.INFERRED}

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
                    source_type=self._AUTHOR_SOURCE[draft.author],
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
        even though the generic mutators now refuse outcome rows (H14)."""
        edges = plan.get("edges", [])
        episodes = plan.get("episodes", [])
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
            # (2) Install ALL records as one logical commit (edges before episodes so
            # an outcome link's edge_id always resolves).
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
            self._bump(user_id)
            self._conn.commit()
            return {"edges": len(edges), "episodes": len(episodes)}

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
            ep = Episode(
                id=f"epc-{uuid.uuid4().hex[:12]}", user_id=op.user_id,
                date=date_start, summary=draft.summary, date_start=date_start,
                date_end=date_end, operation_id=operation_id,
                lineage=[to_historical_id(i) for i in op.claimed_ids],
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
            source_type=SourceType.INFERRED, author_of_evidence=EvidenceAuthor.SYSTEM,
            evidence_ref=operation_id)
        influenced = any(e.provenance.third_party_influenced for e in inputs)
        weakest = (min(inputs, key=lambda e: _RANK[e.provenance.disclosure])
                   .provenance.disclosure if inputs else base.disclosure)
        prov = base.model_copy(update={
            "source_type": SourceType.INFERRED,
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
            for table in ("edges", "episodes", "wiki", "write_counter",
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
