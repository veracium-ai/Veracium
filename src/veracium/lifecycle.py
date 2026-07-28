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
from .schema import DEFAULT_EXPIRY, Episode, ExpiryBehavior, utcnow


def expire(store, user_id: str, config, *, now: Optional[datetime] = None) -> dict:
    """Apply volatility-driven expiry to `user_id`'s active edges. Idempotent."""
    now = now or utcnow()
    lapsed = decayed = flagged = 0
    for e in store.edges(user_id, active_only=True):
        lifetime = config.volatility_lifetime_days.get(e.volatility)
        if lifetime is None:
            continue
        age_days = (now - e.valid_from).days
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


def consolidate(store, llm: Complete, user_id: str, config, *,
                now: Optional[datetime] = None) -> dict:
    """Compact cold episodes (older than `consolidate_after_days`) for `user_id`.
    No-op unless at least `consolidate_min_batch` cold episodes exist."""
    now = now or utcnow()
    cutoff = (now.date() - _timedelta_days(config.consolidate_after_days))
    episodes = store.episodes(user_id)
    # outcome episodes are structured records (source of truth for edge
    # counters), not prose history — the LLM compactor never sees them.
    # TODO(v4): count-summary compaction for cold unreviewed/concurred events;
    # confirmed/corrected keep first occurrences per the compaction-loss guard.
    cold = [e for e in episodes if e.kind != "outcome"
            and _safe_date(e.date) and _safe_date(e.date) < cutoff]
    if len(cold) < config.consolidate_min_batch:
        return {"consolidated": 0, "into": 0}
    listing = "\n".join(f"[{e.date}] {e.summary}" for e in cold)
    data = extract_json(llm(CONSOLIDATE_PROMPT.format(episodes=listing),
                            system=CONSOLIDATE_SYSTEM, role="compile"))
    new = [r for r in data.get("records", [])
           if isinstance(r, dict) and r.get("date") and r.get("summary")]
    if not new or len(new) >= len(cold):
        return {"consolidated": 0, "into": 0}  # no compression achieved
    # provenance: consolidation is a system-authored derivation of the cold set.
    import uuid
    prov = cold[0].provenance.model_copy(update={
        "author_of_evidence": cold[0].provenance.author_of_evidence, "confidence": 0.9})
    for e in cold:
        store.delete_episode(e.id)
    for r in new:
        store.add_episode(Episode(id=f"epc-{uuid.uuid4().hex[:12]}", user_id=user_id,
                                  date=str(r["date"]), summary=str(r["summary"]),
                                  provenance=prov))
    return {"consolidated": len(cold), "into": len(new)}


def _timedelta_days(n: int):
    from datetime import timedelta
    return timedelta(days=n)


def _safe_date(s: str) -> Optional[date]:
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None
