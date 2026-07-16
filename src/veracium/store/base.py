"""Storage interface.

Veracium's store of record is edges + episodes, plus a cached compiled view. The
default is embedded SQLite (`veracium.store.sqlite`); this ABC lets a host swap in
Neo4j / Postgres later without touching the rest of the library.

All methods are per-`user_id`: memory is tenant-scoped by construction, which is
also the isolation boundary (one user's memory can never leak into another's).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..schema import Edge, Episode


class Store(ABC):
    # -- edges -------------------------------------------------------------
    @abstractmethod
    def add_edge(self, edge: Edge) -> None: ...

    @abstractmethod
    def invalidate_edge(self, edge_id: str, at, reason: str) -> None: ...

    @abstractmethod
    def edges(self, user_id: str, *, active_only: bool = True,
              subject: Optional[str] = None, relation: Optional[str] = None,
              include_quarantined: bool = True) -> list[Edge]: ...

    # -- episodes ----------------------------------------------------------
    @abstractmethod
    def add_episode(self, episode: Episode) -> None: ...

    @abstractmethod
    def episodes(self, user_id: str, *, limit: Optional[int] = None) -> list[Episode]: ...

    @abstractmethod
    def delete_episode(self, episode_id: str) -> None: ...

    # -- compliance erasure -------------------------------------------------
    def forget_user(self, user_id: str) -> dict:
        """Irreversibly erase EVERYTHING stored for `user_id` — edges (including
        superseded history and quarantined claims), episodes, the wiki cache,
        and counters. Returns {"edges": n, "episodes": n}. This is the
        data-subject right, deliberately distinct from lifecycle (which never
        deletes). Not abstract so pre-existing Store implementations keep
        working; they get this behavior only once they implement it."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement forget_user")

    # -- compiled-view cache ----------------------------------------------
    @abstractmethod
    def get_wiki(self, user_id: str) -> Optional[tuple[str, int]]:
        """Return (wiki_text, store_version_at_compile) or None."""

    @abstractmethod
    def set_wiki(self, user_id: str, text: str, store_version: int) -> None: ...

    @abstractmethod
    def store_version(self, user_id: str) -> int:
        """A monotonically increasing write counter per user — lets recall know
        whether the cached wiki is stale without diffing content."""

    @abstractmethod
    def close(self) -> None: ...
