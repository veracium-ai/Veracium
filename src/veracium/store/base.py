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
                      Edge, Episode, OutcomeJudgmentDraft)


class HeadMoved:
    """Sentinel result of `append_outcome_if_head` when the chain head moved
    between the caller's read and the atomic append (specs/0009 §4a). The caller
    re-reads the head and retries; it is never a durable state."""
    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return "HeadMoved"


HEAD_MOVED = HeadMoved()


class DestinationChanged:
    """Sentinel result of `commit_outcome_import_plan` when the destination store
    changed between the whole-import preflight and the atomic commit (specs/0009
    §4c) — a concurrent `append_outcome_if_head`, import, or edit moved a chain
    head, altered a record the plan reasoned about, or changed an edge's presence
    or ownership. NOTHING was written; the caller re-preflights the WHOLE import
    and retries, or refuses. Like `HeadMoved`, it is never a durable state."""
    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return "DestinationChanged"


DESTINATION_CHANGED = DestinationChanged()


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

    @store_mutator
    def append_outcome_if_head(self, user_id: str, edge_id: str,
                               evidence_ref: str, expected_head_id: Optional[str],
                               draft: OutcomeJudgmentDraft):
        """Atomically append one outcome judgment to the append-only chain for
        `(user_id, edge_id, evidence_ref)` — the specs/0009 §4a CAS primitive, the
        ONLY sanctioned way to create a `kind="outcome"` chain link (H3/H14).

        In one atomic operation the store: (1) resolves the chain; (2) verifies
        `expected_head_id` is still its head (else returns `HEAD_MOVED`); (3) for a
        non-root append resolves `context_ref` (omitted → inherit the chain's;
        non-None must equal it); (4) allocates the next per-chain `seq` (root == 1,
        contiguous) and mints a fresh episode id; (5) INSERTs — never replaces — with
        `supersedes_episode = expected_head_id`, `judgment_time_known = True`, and
        `source_type` DERIVED from `draft.author` (USER→STATED, SYSTEM→INFERRED);
        (6) advances the user's `store_version` (H10). Returns the appended `Episode`
        on success or `HEAD_MOVED` (the caller retries against the new head).

        Not abstract so pre-existing `Store` implementations keep working; they get
        this behaviour only once they implement it."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement append_outcome_if_head")

    @store_mutator
    def commit_outcome_import_plan(self, user_id: str, plan: dict,
                                   expected_destination_state: dict):
        """Atomically install a whole validated import plan — the specs/0009 §4c
        commit primitive. `plan` is `{"edges": [Edge...], "episodes": [Episode...]}`,
        already cross-user remapped, legacy-converted (§4f-ii) and topology-validated
        by the caller's WHOLE-import preflight; it contains ONLY the records to write
        (idempotent-equal records were skipped, differing ones already refused).

        `expected_destination_state` carries EVERY destination assumption the preflight
        reasoned about (round-6 Correction B — not just chain heads): the presence and
        ownership of referenced edges, the current persisted form of every incoming
        episode id (so a concurrent edit is caught), and the head of every outcome
        chain identity the plan touches. In ONE atomic operation the store: (1)
        revalidates ALL of that against the live store — any drift returns
        `DESTINATION_CHANGED`, writing nothing; (2) installs every plan Edge and
        Episode (outcome links included) as ONE logical commit, linearized against
        `append_outcome_if_head`. A lost destination race refuses the WHOLE import;
        NOTHING is written after a prefix. Returns `{"edges": n, "episodes": n}` on
        success or `DESTINATION_CHANGED`.

        This is a purpose-built primitive that encodes ONE invariant at the interface
        boundary — "install this validated plan iff these destination assumptions still
        hold" — NOT a general Store transaction API (specs/0009 §4c). Not abstract so
        pre-existing `Store` implementations keep working."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement commit_outcome_import_plan")

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
