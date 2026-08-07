"""Memory lifecycle: expiry and consolidation — the "overnight" maintenance job.

Two mechanisms, both grounded in findings:
- **Expiry (findings on volatility).** A fact past its expected lifetime is
  handled by its volatility's behavior: transient/ephemeral facts LAPSE (silently
  invalidated — "still sick?" three months later is irrelevant, not unknown);
  durable/slow facts are flagged CONFIRM (surfaced as possibly-stale, never
  silently dropped); DECAY lowers confidence until a floor. Reinforcement (a
  re-stated fact) refreshes validity and clears the flag — handled at ingest.
- **Consolidation (finding 11 / compaction-loss guard).** Cold episodes are
  compacted into compact summaries to bound read cost as history grows (finding
  22), but first occurrences of failures, their fixes, illnesses, and dated
  commitments are preserved verbatim — the subtle-pattern loss the research warned
  compaction causes.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from ._json import extract_json
from .llm.base import Complete
from .schema import (DEFAULT_EXPIRY, Disclosure, Episode, EvidenceAuthor, ExpiryBehavior,
                     SourceType,
                     utcnow)


def expire(store, user_id: str, config, *, now: Optional[datetime] = None) -> dict:
    """Apply volatility-driven expiry to `user_id`'s active edges. Idempotent."""
    now = now or utcnow()
    lapsed = decayed = flagged = 0
    for e in store.edges(user_id, active_only=True):
        lifetime = config.volatility_lifetime_days.get(e.volatility)
        if lifetime is None:
            continue
        # liveness ages against observed_at (when we last recorded this),
        # NOT valid_from (when the fact became true) — a fact stated years ago
        # and restated yesterday is live; one recorded once and never again is
        # the one that should lapse
        age_days = (now - e.provenance.observed_at).days
        if age_days <= lifetime:
            continue
        behavior = DEFAULT_EXPIRY[e.volatility]
        if behavior == ExpiryBehavior.LAPSE:
            store.invalidate_edge(e.id, now, "lapsed"); lapsed += 1
        elif behavior == ExpiryBehavior.DECAY:
            e.provenance.confidence *= config.decay_factor
            if e.provenance.confidence < config.confidence_floor:
                store.invalidate_edge(e.id, now, "decayed"); decayed += 1
            else:
                store.add_edge(e)
        else:  # CONFIRM — never silently dropped; surfaced as possibly-stale
            if not e.needs_confirmation:
                e.needs_confirmation = True
                store.add_edge(e); flagged += 1
    return {"lapsed": lapsed, "decayed": decayed, "flagged_for_confirmation": flagged}


CONSOLIDATE_SYSTEM = (
    "You compact an AI assistant's old interaction history into fewer, denser "
    "records without losing anything a future question might need."
)

CONSOLIDATE_PROMPT = """Compact these dated episodes into FEWER consolidated
records. Preserve, VERBATIM and individually dated, every first occurrence of:
a failure, the fix for a failure, an illness/injury, and any dated commitment or
deadline. Merge only routine/repetitive activity.

EPISODES (oldest first):
{episodes}

Return ONLY JSON:
{{"records": [{{"date": "<YYYY-MM-DD>", "summary": "<one sentence>"}}]}}
Fewer records than the input. Keep dates and specifics exact."""


def _recover(store, user_id: str) -> int:
    """specs/0010 X2/X13 — roll each recovery-pending op to a safe terminal state and
    return the count actually resolved this pass. `OUTPUTS_DURABLE` rolls FORWARD
    (idempotent delete-then-finalize, never a re-consolidation); an EXPIRED pre-cutover
    op is cleanly `ABANDONED`. A LIVE pre-cutover op (a peer heartbeating) is left
    pending — `abandon` refuses a live lease (X7), so it is not counted as recovered."""
    from .schema import ConsolidationState as _S
    resolved = 0
    for op in store.pending_consolidations(user_id):
        if op.state is _S.OUTPUTS_DURABLE:
            store.delete_claimed_inputs_if_current(op.operation_id, op.fence)
            if store.transition_consolidation_if_current(
                    op.operation_id, op.fence, None, _S.FINALIZED):
                resolved += 1
        elif store.abandon_consolidation_if_current(op.operation_id, op.fence):
            resolved += 1
    return resolved


def consolidate(store, llm: Complete, user_id: str, config, *,
                now: Optional[datetime] = None) -> dict:
    """Compact cold episodes (older than `consolidate_after_days`) for `user_id`,
    crash-safely (specs/0010). Runs recovery FIRST (X13), then claims a whole batch
    atomically (X4), generates, writes every output BEFORE deleting any input (X1),
    and finalizes only once inputs are gone (X20). No-op unless at least
    `consolidate_min_batch` cold candidates exist."""
    from .schema import (ConsolidationOutputDraft, ConsolidationState,
                         to_historical_id)  # noqa: F401
    import uuid
    now = now or utcnow()
    recovered = _recover(store, user_id)               # X13: recovery at its own start
    cutoff = (now.date() - _timedelta_days(config.consolidate_after_days))
    episodes = store.episodes(user_id)
    # Candidates exclude: outcome episodes (structured records the compactor never
    # sees), consolidation OUTPUTS (non-empty lineage — X16, never a candidate), and
    # already-claimed inputs (a concurrent op holds them — X4).
    cold = [e for e in episodes if e.kind != "outcome" and not e.lineage
            and e.claimed_by is None
            and _safe_date(e.date) and _safe_date(e.date) < cutoff]
    if len(cold) < config.consolidate_min_batch:
        return {"consolidated": 0, "into": 0, "recovered": recovered}
    listing = "\n".join(f"[{e.date}] {e.summary}" for e in cold)
    data = extract_json(llm(CONSOLIDATE_PROMPT.format(episodes=listing),
                            system=CONSOLIDATE_SYSTEM, role="compile"))
    new = [r for r in data.get("records", [])
           if isinstance(r, dict) and r.get("date") and r.get("summary")]
    if not new or len(new) >= len(cold):
        return {"consolidated": 0, "into": 0, "recovered": recovered}  # no compression
    # Claim the whole set atomically (X4). A contended set → None; a stale candidate
    # (concurrently finalized out from under us) → ValueError. Either way, skip this
    # pass having mutated nothing.
    owner = f"consolidate:{uuid.uuid4().hex[:12]}"
    lease = getattr(config, "consolidate_lease_seconds", 300)
    try:
        op = store.create_or_takeover_consolidation(
            user_id, [e.id for e in cold], owner, lease)
    except ValueError:
        return {"consolidated": 0, "into": 0, "recovered": recovered}
    if op is None:
        return {"consolidated": 0, "into": 0, "recovered": recovered}
    # GENERATING → write every output (the store BINDS lineage=whole claimed set and
    # DERIVES the trust floor + date range from it, X8/X12/X23 — the whole-set-minimum
    # provenance logic now lives in the store) → cutover (X1: write-before-delete) →
    # delete inputs (X2) → finalize (X20).
    store.transition_consolidation_if_current(
        op.operation_id, op.fence, owner, ConsolidationState.GENERATING)
    for r in new:
        store.write_consolidation_output_if_current(
            op.operation_id, op.fence, owner,
            ConsolidationOutputDraft(summary=str(r["summary"]),
                                     date_start=str(r["date"]), date_end=str(r["date"])))
    if not store.transition_consolidation_if_current(
            op.operation_id, op.fence, owner, ConsolidationState.OUTPUTS_DURABLE):
        return {"consolidated": 0, "into": 0, "recovered": recovered}
    store.delete_claimed_inputs_if_current(op.operation_id, op.fence)
    store.transition_consolidation_if_current(
        op.operation_id, op.fence, owner, ConsolidationState.FINALIZED)
    return {"consolidated": len(cold), "into": len(new), "recovered": recovered}


# NOTE: the whole-set-minimum-trust provenance logic that used to live here (N9b /
# 0.4.4 security fix — INFERRED author, min confidence, weakest disclosure, retained
# third-party influence, currency capped at the newest input) now lives in the STORE's
# `write_consolidation_output_if_current._derive_output_metadata`, because specs/0010
# X23 requires those derived fields be computed at the fenced write boundary from the
# claimed set, not by the caller. See src/veracium/store/sqlite.py.


def _timedelta_days(n: int):
    from datetime import timedelta
    return timedelta(days=n)


def _safe_date(s: str) -> Optional[date]:
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None
