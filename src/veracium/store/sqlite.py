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

_SCHEMA = """
CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, subject TEXT, relation TEXT,
    object TEXT, active INTEGER NOT NULL, quarantined INTEGER NOT NULL, json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_edges_user_active ON edges(user_id, active);
CREATE INDEX IF NOT EXISTS ix_edges_subj_rel ON edges(user_id, subject, relation, active);
CREATE TABLE IF NOT EXISTS episodes (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, date TEXT, json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_episodes_user ON episodes(user_id, date);
CREATE TABLE IF NOT EXISTS wiki (
    user_id TEXT PRIMARY KEY, text TEXT, store_version INTEGER
);
CREATE TABLE IF NOT EXISTS write_counter (
    user_id TEXT PRIMARY KEY, n INTEGER NOT NULL
);
"""


class SqliteStore(Store):
    def __init__(self, path: str | Path = "veracium.db"):
        self._path = str(path)
        # check_same_thread=False + a lock: safe for the library's typical
        # single-writer, many-reader agent usage without a connection pool.
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
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
