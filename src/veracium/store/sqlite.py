"""Embedded SQLite store — the zero-dependency default.

Everything (edges, episodes, compiled-view cache, per-user write counter) lives
in one SQLite file. Per-user graphs are small (the research saw ~120 edges at
9 weeks of history), so a single indexed table per kind is ample; a Neo4j/
Postgres `Store` can replace this for very large multi-tenant deployments.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..schema import (Confirmation, ConfirmationActor, ConfirmationCallPath,
                      Edge, Episode, EvidenceAuthor, OutcomeJudgmentDraft,
                      Provenance, SourceType)
from .base import HEAD_MOVED, Store
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
                 busy_timeout_ms: int = 5000):
        self._path = str(path)
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
    def add_edge(self, edge: Edge) -> None:
        with self._lock:
            # specs/0008 §6d: `add_edge` may NOT clear `needs_confirmation`
            # (True→False) when replacing an edge of the same id — only
            # `confirm_edge` may — and may NOT change an edge's `user_id`
            # (ownership is not transferable through the upsert path). Compared
            # against the PERSISTED prior state, so a reconstructed edge cannot
            # slip the transition past the write path (C1, C10).
            prior = self._conn.execute(
                "SELECT user_id, json FROM edges WHERE id=?", (edge.id,)).fetchone()
            if prior is not None:
                if prior[0] != edge.user_id:
                    raise ValueError(
                        f"add_edge cannot change edge {edge.id!r}'s user_id "
                        f"({prior[0]!r} → {edge.user_id!r}) — ownership is not "
                        f"transferable through the upsert path (specs/0008 §6d)")
                if (Edge.model_validate_json(prior[1]).needs_confirmation
                        and not edge.needs_confirmation):
                    raise ValueError(
                        f"add_edge cannot clear needs_confirmation (True→False) on "
                        f"edge {edge.id!r} — only confirm_edge may (specs/0008 §6d, "
                        f"C1)")
            self._conn.execute(
                "INSERT OR REPLACE INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (edge.id, edge.user_id, edge.subject, edge.relation, edge.object,
                 int(edge.active), int(edge.quarantined), edge.model_dump_json()))
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

    def invalidate_edge(self, edge_id: str, at, reason: str) -> None:
        with self._lock:
            row = self._conn.execute("SELECT json, user_id FROM edges WHERE id=?", (edge_id,)).fetchone()
            if not row:
                return
            edge = Edge.model_validate_json(row[0])
            edge.invalidated_at = at
            edge.invalidation_reason = reason
            self._conn.execute("UPDATE edges SET active=0, json=? WHERE id=?",
                               (edge.model_dump_json(), edge_id))
            self._bump(row[1])
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

    # -- episodes ----------------------------------------------------------
    def add_episode(self, episode: Episode) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                (episode.id, episode.user_id, episode.date, episode.model_dump_json()))
            self._bump(episode.user_id)
            self._conn.commit()

    def episodes(self, user_id, *, limit=None) -> list[Episode]:
        q = "SELECT json FROM episodes WHERE user_id=? ORDER BY date"
        if limit:
            q += f" LIMIT {int(limit)}"
        return [Episode.model_validate_json(r[0])
                for r in self._conn.execute(q, (user_id,)).fetchall()]

    def delete_episode(self, episode_id) -> None:
        with self._lock:
            row = self._conn.execute("SELECT user_id FROM episodes WHERE id=?", (episode_id,)).fetchone()
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
            for table in ("edges", "episodes", "wiki", "write_counter",
                          "confirmations"):
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
