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

from ..schema import (ConsolidationOp, ConsolidationOutputDraft, Confirmation,
                      ConfirmationActor, ConfirmationCallPath, Edge, Episode,
                      OutcomeJudgmentDraft, SupersessionPlan, SupersessionRefusal,
                      SupersessionResult)

# specs/0010 §4a-ii: the one library bound on a lease's duration (seconds). A
# renewal re-adds exactly `lease_duration`; `0 < lease_duration <= LEASE_MAX`.
LEASE_MAX = 3600


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


class NonQuiescent:
    """Sentinel result of `quiescent_episode_snapshot` when the user has a
    non-quiescent consolidation op (CLAIMED/GENERATING/OUTPUTS_DURABLE) at the read's
    linearization point (specs/0010 §4f, X17). Export refuses, mutating nothing; the
    caller runs recovery (`consolidate()`/`maintain()`) and retries."""
    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return "NonQuiescent"


NON_QUIESCENT = NonQuiescent()


class PlanStale:
    """Sentinel result of `apply_supersession_plan` when the `(user, subject, relation)`
    state the plan was computed from changed between the caller's read and the atomic
    commit (specs/0003 §4f, I9). NOTHING was written and the durable receipt was NOT
    consumed; the caller re-reads, recomputes and retries the SAME logical operation. The
    same compare-and-set shape as `HEAD_MOVED` / `DESTINATION_CHANGED`; never durable."""
    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return "PlanStale"


PLAN_STALE = PlanStale()


class SupersessionIntegrityError(Exception):
    """A durable receipt for `(user_id, operation_id)` exists but the incoming plan's
    logical request digest DIFFERS from the committed one (specs/0003 §4f, processing
    order step 1). Reusing one operation id for two different logical operations is a
    caller integrity bug, not a race — so it raises rather than replaying or retrying."""


class ReceiptDomainError(SupersessionIntegrityError):
    """specs/0025 §4b-v, the fail-closed cells: a stored request-digest
    domain this code cannot interpret (unknown/malformed value), or the
    read-side inconsistency no legal writer produces (a domain stamped on a
    digest-less receipt). Never replayed, never classified as a new
    request — guessing either way risks a double-apply or a false
    conflict."""


class ReceiptSchemaBoundaryError(SupersessionIntegrityError):
    """specs/0016 D2 — the receipt ERA boundary (0003 §4f as amended). The
    stored receipt committed under a pre-D2 digest projection
    (`outcome_digest_version` < 4: its snapshot carried the deleted
    `source_type` field), and post-D2 neither historical projection can be
    computed faithfully — so a resubmission refuses UNCONDITIONALLY ON SIGHT,
    at both receipt phases, before any digest is computed. A legitimate retry
    whose only removed input was `source_type` and a genuinely different
    request reusing the operation id produce THE SAME resubmission:
    classification is impossible, and that impossibility is the ruling — the
    outcome is handled at least as conservatively as an integrity violation
    (hence the subclass: existing `except SupersessionIntegrityError`
    handlers keep catching it). It is never treated as benign and never
    replayed; recovery is a fresh operation id."""


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
    # --- specs/0023 §4a (quarantine-at-birth) --------------------------------
    def standing_revocations(self, user_id: str) -> frozenset:
        """The standing revoked identity-digest set (0022 §4a). Default: a
        store without revocation support has NO standing revocations, so
        ingest quarantines nothing — fail-open on breadth is correct here
        because the EMPTY set is the true answer for such a store, not a
        guess about one it cannot read."""
        return frozenset()

    # -- edges -------------------------------------------------------------
    @store_mutator
    @abstractmethod
    def add_edge(self, edge: Edge) -> None:
        """Persist (or same-ID replace) one edge.

        PERSISTENCE-PATH OBLIGATIONS every backend must enforce (compared
        against the PERSISTED prior state, the 0008 §6d guard shape):
        `user_id` never changes; `needs_confirmation` never clears True→False
        (only confirm_edge may — specs/0008 §6d); and `ungrounded` refuses
        EVERY same-ID transition in BOTH directions with no exception —
        absorption inserts a NEW survivor whose flag is the N-ary OR computed
        pre-insert, so the persistence layer sees only immutable flags
        (specs/0019 §3b/§4d, U4)."""
        ...

    @store_mutator
    @abstractmethod
    def invalidate_edge(self, edge_id: str, at, reason: str) -> None: ...

    @store_mutator
    def apply_supersession_plan(self, plan: SupersessionPlan):
        """Apply the WHOLE outcome of one supersession atomically and conditionally
        (specs/0003 §4f, I9). Returns a `SupersessionResult` (Applied), the `PLAN_STALE`
        sentinel, or raises `SupersessionIntegrityError`.

        Processing order (frozen, §4f; era rule per 0016 D2):
          1. receipt for `(user_id, operation_id)` exists?
               `outcome_digest_version` < 4  → raise `ReceiptSchemaBoundaryError`
                 UNCONDITIONALLY ON SIGHT — no digest computed, no comparison
                 branch (the pre-D2 projections are not computable post-D2)
               same `logical_request_digest` → REPLAY the original Applied (no-op)
               different digest              → raise `SupersessionIntegrityError`
          2. new logical operation → revalidate `expected_state` (the complete scope
             fingerprint) INSIDE the transaction
          3. `expected_state` stale → return `PLAN_STALE`; do NOT consume the receipt
          4. success → prior upserts + retirements + the incoming edge (iff
             `insert_incoming`) + store-bound refusal rows + the receipt all commit in
             ONE transaction; the store advances `store_version` and drops the user's
             wiki cache when the plan forms a contention (refusals present).

        Not abstract so pre-existing Store implementations keep working; a backend that
        cannot do this atomically MUST raise, not degrade."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement apply_supersession_plan")

    def refusals(self, user_id: str) -> list[SupersessionRefusal]:
        """The durable, content-free refusal inventory for a user (specs/0003 §4b),
        newest first. Read-only; the source `specs/0011` re-evaluates. Not abstract."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement refusals")

    def contributions(self, user_id: str, survivor_type: str,
                      survivor_id: str) -> list:
        """specs/0014 §4d: every contributor consumed into a survivor, newest
        first — type-keyed (R1-5). Read-only; the ledger is store-local metadata
        like the 0003 refusal inventory. Not abstract."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement contributions")

    def contributions_naming(self, user_id: str, contributor_ref: str) -> list:
        """specs/0021 §7b (the 0014 amendment's typed link): every ledger row
        whose `contributor_ref` NAMES the given record — the REVERSE of
        `contributions` (which is keyed by survivor). The export path's
        `derive_absorbed_by` join: rows written before SCHEMA v8 carry a NULL
        `contributor_ref` and never match (the disclosed legacy class — the
        record exports without the structured field). Returns dicts with
        `survivor_type`, `survivor_id`, `site`, `payload`, `contributor_ref`.
        Read-only; not abstract."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement contributions_naming")

    def contributors_of_source(self, user_id: str, identity_digest: str) -> list:
        """specs/0014 §4d/A9: every survivor a source contributed to —
        `revoke_source`'s blast-radius join. Complete identities only: a NULL
        digest never joins (F1/I13). Not abstract."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement contributors_of_source")

    def supersessions_refused(self, user_id: str) -> int:
        """The count of refused retirements for a user — DERIVED from the refusal
        records, never stored separately (§4f: a second copy of a count is drift)."""
        return len(self.refusals(user_id))

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
        `supersedes_episode = expected_head_id` and `judgment_time_known = True`;
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

        specs/0009 §4c AS AMENDED BY 0020/0021: the plan gains a THIRD member,
        `plan["contributions"]` — ContributionRowPlan dicts, TOTAL over the stored
        row's field set (id = `plan_row_id`, THE one canonical logical-row
        projection; user_id; survivor_type/survivor_id, which must name a record
        in THIS plan or an already-present idempotent-equal record; site — one of
        the TWO plan sites `imported-absorption`/`scope-attribution`;
        identity_digest; evidence_ref_digest; contributor_type/contributor_ref;
        the site's closed payload; the injective per-row `op_key` derived from
        the ONE minted `op-<12hex>` import operation). Rows derive ONLY from
        `reconstruct_absorption_rows` over the export file, PRE-COMMIT (0020
        §4a-iii); the store validates everything (context-aware validator, exact
        in-primitive key/id derivation — a caller-selected key or id refuses)
        and invents nothing but its own clock.

        `expected_destination_state` carries EVERY destination assumption the preflight
        reasoned about (round-6 Correction B — not just chain heads): the presence and
        ownership of referenced edges, the current persisted form of every incoming
        episode id (so a concurrent edit is caught), the head of every outcome
        chain identity the plan touches, and (the 0009 amendment)
        `contribution_state` — for every plan record carrying contribution rows,
        the destination's current ledger row ids for that (user, type, id): the
        current rows must be ABSENT (first import — rows write) or EXACTLY EQUAL
        by `plan_row_id` set equality (idempotent re-import — rows skip, counted
        as existing); anything else returns `DESTINATION_CHANGED`, writing
        nothing — a survivor with different recorded contributors or a different
        recorded history shape is a different history, refused whole. In ONE
        atomic operation the store: (1) revalidates ALL of that against the live
        store — any drift returns `DESTINATION_CHANGED`, writing nothing; (2)
        installs every plan Edge, Episode (outcome links included) AND
        contribution row as ONE logical commit, linearized against
        `append_outcome_if_head`. A lost destination race refuses the WHOLE
        import; NOTHING is written after a prefix; contribution rows ride the
        SAME single atomic commit (rollback included). Returns `{"edges": n,
        "episodes": n, "contributions": n, "contributions_existing": m}` on
        success or `DESTINATION_CHANGED`.

        This is a purpose-built primitive that encodes ONE invariant at the interface
        boundary — "install this validated plan iff these destination assumptions still
        hold" — NOT a general Store transaction API (specs/0009 §4c). Not abstract so
        pre-existing `Store` implementations keep working."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement commit_outcome_import_plan")

    # -- crash-safe consolidation (specs/0010) --------------------------------
    @store_mutator
    def create_or_takeover_consolidation(self, user_id: str, ids: list,
                                         owner: str, lease_duration: int):
        """Atomically claim `ids` for a new consolidation, or take over a clean
        `ABANDONED` op covering exactly them — the specs/0010 §4a-ii/§4b claim
        primitive. Returns the `ConsolidationOp` (state CLAIMED) or None if any id is
        contended (belongs to a LIVE-lease op). MULTI-PHASE (§4a-ii Correction C): an
        EXPIRED pre-cutover op intersecting the request is ABANDONED (cleaned) first,
        then the claim is re-evaluated; a new fence issues ONLY from cleanup-complete
        `ABANDONED` (X15). The store mints the fence (monotonic) and sets
        `lease_expires_at = store_now + lease_duration` (0 < lease_duration <= LEASE_MAX).
        The claim step is all-or-nothing (X4/X11)."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement create_or_takeover_consolidation")

    @store_mutator
    def renew_consolidation_lease(self, operation_id: str, fence: int,
                                  owner: str) -> bool:
        """Extend the lease to `store_now + lease_duration` (the op's PERSISTED
        duration) — specs/0010 §4a-ii. Succeeds only for the exact current
        `(fence, owner)` under an UNEXPIRED lease; it cannot resurrect an expired lease
        (that path is takeover). Returns True on success."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement renew_consolidation_lease")

    @store_mutator
    def write_consolidation_output_if_current(self, operation_id: str, fence: int,
                                              owner: str,
                                              draft: ConsolidationOutputDraft) -> bool:
        """Write ONE provisional (hidden) output for a GENERATING op — specs/0010 §4b-ii,
        X22/X23. Owner-only under a live lease + current fence. The store MINTS a fresh
        id, BINDS the op fields (`user_id==op.user_id`, `operation_id`, `lineage ==
        op.claimed_ids`), DERIVES the trust floor + `date_start/end/date` from
        `op.claimed_ids` (not the draft, X23), and INSERTs — never replaces (a minted-id
        collision is a store error). Returns True on success, False if not current."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement write_consolidation_output_if_current")

    @store_mutator
    def transition_consolidation_if_current(self, operation_id: str, fence: int,
                                            owner, to_state) -> bool:
        """Advance the op's state under `(operation_id, fence)` — specs/0010 §4b-ii.
        Pre-cutover transitions (`CLAIMED→GENERATING`, `GENERATING→OUTPUTS_DURABLE`) are
        owner-only under a live lease; `→OUTPUTS_DURABLE` REFUSES with zero bound outputs
        (X22) and advances `store_version` (the visibility cutover, X14).
        `OUTPUTS_DURABLE→FINALIZED` is ownerless/recovery-safe and REFUSES unless every
        claimed input is already deleted (X20). Returns True on success."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement transition_consolidation_if_current")

    @store_mutator
    def delete_claimed_inputs_if_current(self, operation_id: str, fence: int) -> bool:
        """Delete the op's claimed input rows as ONE all-or-nothing batch — specs/0010
        §4b, X2. Post-cutover, ownerless/recovery-safe, validated by `(operation_id,
        fence)` + `OUTPUTS_DURABLE`. Idempotent re-delete. The reservation (X21) survives
        this physical delete until FINALIZED. Returns True on success."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement delete_claimed_inputs_if_current")

    @store_mutator
    def abandon_consolidation_if_current(self, operation_id: str, fence: int) -> bool:
        """Clean up an EXPIRED-lease pre-cutover op and mark it `ABANDONED` — specs/0010
        §4b-iii, X15. ONE atomic primitive: deletes every provisional output row for the
        op AND clears `claimed_by`/`operation_id` on its claimed inputs (Design A —
        never 'all rows'; inputs carry `operation_id` too), THEN the op is observably
        `ABANDONED`. Succeeds ONLY on an expired lease (won't roll back a live peer, X7).
        Returns True on success."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement abandon_consolidation_if_current")

    def pending_consolidations(self, user_id: str) -> list:
        """READ — the recovery-pending ops for `user_id`: exactly
        `{CLAIMED, GENERATING, OUTPUTS_DURABLE}`, NOT `FINALIZED` and NOT quiescent
        `ABANDONED` (specs/0010 §4b, X13). Recovery reads this, applies the transition
        table to each, and counts them. Not abstract for backend compatibility."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement pending_consolidations")

    def quiescent_episode_snapshot(self, user_id: str):
        """READ — an ATOMIC per-user observation (specs/0010 §4f, X17) that either
        returns the user's episode list (iff every op is quiescent — FINALIZED or clean
        ABANDONED) or `NON_QUIESCENT`. The quiescence check and the episode snapshot are
        ONE linearizable observation against `create_or_takeover_consolidation`, so a
        claim starting mid-snapshot yields `NON_QUIESCENT`, never a dangling
        `claimed_by`. Read-only; never bumps `store_version`. Not abstract for
        backend compatibility."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement quiescent_episode_snapshot")

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
