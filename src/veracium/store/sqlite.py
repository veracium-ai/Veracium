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
from pathlib import Path
from typing import Optional

from ..schema import Edge, Episode
from .base import Store
from .schema_version import (SCHEMA_V1, PostCommitAuditError,  # noqa: F401
                             StoreVersionError, open_versioned)

# The schema is DERIVED from the versioning registry — one declaration, which
# is 0007 §4a-vi's "honest end state": there is no second copy to drift, and
# `registry_conformance` compares this module against the registry it is built
# from. `IF NOT EXISTS` is gone with it: creation now happens exactly once, on
# the §4 "new" path, inside the open transaction.
_SCHEMA = ";\n".join(o.ddl for o in SCHEMA_V1) + ";\n"


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
            self._conn.execute(
                "INSERT OR REPLACE INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (edge.id, edge.user_id, edge.subject, edge.relation, edge.object,
                 int(edge.active), int(edge.quarantined), edge.model_dump_json()))
            self._bump(edge.user_id)
            self._conn.commit()

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
            for table in ("edges", "episodes", "wiki", "write_counter"):
                self._conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
            self._conn.commit()
        return {"edges": n_edges, "episodes": n_eps}

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
