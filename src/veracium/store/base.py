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

from ..schema import (Confirmation, ConfirmationActor, ConfirmationCallPath,
                      Edge, Episode)


def store_mutator(fn):
    """Marks a Store method that writes persistent state.

    The specs/0002 audit manifest enumerates every call site of every mutator.
    It used to discover them from a remembered list of name prefixes -- add_,
    invalidate_, delete_, forget_, set_ -- which is the original failure of that
    audit repeated one level up: the interface was scanned, but *which methods
    mutate* was still recalled rather than declared. A new primitive named
    anything else (spec 0010 needs `claim_episode_batch`) would have been
    invisible to the manifest while writing persistent trust state.

    Marking is declarative and survives renaming. `audit_manifest.py` reads it.
    """
    fn.__store_mutator__ = True
    return fn


class Store(ABC):
    # -- edges -------------------------------------------------------------
    @store_mutator
    @abstractmethod
    def add_edge(self, edge: Edge) -> None: ...

    @store_mutator
    @abstractmethod
    def invalidate_edge(self, edge_id: str, at, reason: str) -> None: ...

    @store_mutator
    def confirm_edge(self, user_id: str, edge_id: str, *,
                     actor: ConfirmationActor, call_path: ConfirmationCallPath,
                     correlation_id: str, request_digest: str,
                     confirmed_at) -> Confirmation:
        """The ONLY path that clears `needs_confirmation` (specs/0008 §6b). In ONE
        transaction: verify ownership + assertability, clear the flag, advance
        `observed_at`/`confidence`, write the confirmation episode, and persist the
        mandatory `confirmations` record — if the record cannot commit, the whole
        confirmation fails and the flag stays set (C7). Idempotent on
        `(user_id, correlation_id)`: a replay of the SAME canonical request
        (matching `request_digest`) returns the ORIGINAL success reconstructed from
        the stored record (`replayed=True`); a DIFFERENT request under the same id
        is an integrity conflict; concurrent duplicates commit exactly once (C8). A
        backend that cannot do this atomically MUST raise, not degrade (§6d, C10).
        Not abstract so pre-existing Store implementations keep working."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement confirm_edge")

    def confirmations_for(self, user_id: str, edge_id: str) -> list[Confirmation]:
        """Read-only audit inspection (specs/0008 §6d): the confirmations recorded
        for one edge, newest first. Not abstract for backend compatibility."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement confirmations_for")

    @abstractmethod
    def edges(self, user_id: str, *, active_only: bool = True,
              subject: Optional[str] = None, relation: Optional[str] = None,
              include_quarantined: bool = True) -> list[Edge]: ...

    # -- episodes ----------------------------------------------------------
    @store_mutator
    @abstractmethod
    def add_episode(self, episode: Episode) -> None: ...

    @abstractmethod
    def episodes(self, user_id: str, *, limit: Optional[int] = None) -> list[Episode]: ...

    @store_mutator
    @abstractmethod
    def delete_episode(self, episode_id: str) -> None: ...

    # -- host/admin queries ---------------------------------------------------
    def list_users(self) -> list[dict]:
        """Distinct user ids in the store with edge/episode counts, e.g.
        [{"user_id": "alice", "edges": 12, "episodes": 4}, ...]. Host/admin
        surface (proactive recall, ops dashboards) — deliberately NOT exposed
        over MCP: cross-user enumeration handed to an agent is the same class
        of footgun as an agent-callable forget(). Non-abstract so pre-existing
        Store implementations keep working."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement list_users")

    # -- compliance erasure -------------------------------------------------
    @store_mutator
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

    @store_mutator
    @abstractmethod
    def set_wiki(self, user_id: str, text: str, store_version: int) -> None: ...

    @abstractmethod
    def store_version(self, user_id: str) -> int:
        """A monotonically increasing write counter per user — lets recall know
        whether the cached wiki is stale without diffing content."""

    @abstractmethod
    def close(self) -> None: ...
