"""Configuration for a `Memory` instance. See `docs/api.md` for the field table."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .schema import DEFAULT_RELATIONS, Relation, Volatility


def _default_lifetimes() -> dict[Volatility, Optional[int]]:
    """Expected lifetime in days per volatility class (None = never expires)."""
    return {Volatility.PERMANENT: None, Volatility.DURABLE: 730,
            Volatility.SLOW: 120, Volatility.TRANSIENT: 7, Volatility.EPHEMERAL: 1}


@dataclass
class MemoryConfig:
    db_path: str = "veracium.db"
    relations: dict[str, Relation] = field(default_factory=lambda: dict(DEFAULT_RELATIONS))
    # recall assembly (these caps bound read cost as history grows — finding 22)
    max_subgraph_edges: int = 40
    # Fraction of the subgraph budget reserved for time coverage when the store
    # is larger than the budget. Pure top-k has no coverage term, so facts that
    # share vocabulary can collapse the selection onto one period.
    # DEFAULT 0.0 (off): the mechanism is implemented and tested, but the
    # measurement that motivated it was retracted — the benchmark sample it was
    # diagnosed from turned out to be unrepresentative on exactly the dimension
    # involved, so coverage has never been tested on data that could exercise
    # it. Set >0 to enable; it will become the default if and when a balanced
    # measurement supports it.
    subgraph_coverage_share: float = 0.0
    max_recent_episodes: int = 12
    # proactive recall (recall with no query): how far ahead a dated commitment
    # counts as "coming due", and how far back "recent history" reaches.
    proactive_deadline_window_days: int = 7
    proactive_recent_days: int = 7
    # compiled-wiki cache: recompile when this many writes have landed since the
    # last compile (0 disables the wiki layer → recall renders the subgraph only).
    wiki_recompile_after_writes: int = 8
    # lifecycle (findings 9/11/19) — applied by mem.maintain()
    volatility_lifetime_days: dict[Volatility, Optional[int]] = field(default_factory=_default_lifetimes)
    decay_factor: float = 0.5          # confidence multiplier when a DECAY fact expires
    confidence_floor: float = 0.3      # below this, a decayed fact is invalidated
    consolidate_after_days: int = 30   # episodes older than this are consolidation candidates
    consolidate_min_batch: int = 8     # don't consolidate fewer than this many cold episodes
