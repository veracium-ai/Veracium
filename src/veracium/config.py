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
    max_recent_episodes: int = 12
    # compiled-wiki cache: recompile when this many writes have landed since the
    # last compile (0 disables the wiki layer → recall renders the subgraph only).
    wiki_recompile_after_writes: int = 8
    # lifecycle (findings 9/11/19) — applied by mem.maintain()
    volatility_lifetime_days: dict[Volatility, Optional[int]] = field(default_factory=_default_lifetimes)
    decay_factor: float = 0.5          # confidence multiplier when a DECAY fact expires
    confidence_floor: float = 0.3      # below this, a decayed fact is invalidated
    consolidate_after_days: int = 30   # episodes older than this are consolidation candidates
    consolidate_min_batch: int = 8     # don't consolidate fewer than this many cold episodes
