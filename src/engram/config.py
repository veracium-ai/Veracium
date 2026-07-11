from __future__ import annotations

from dataclasses import dataclass, field

from .schema import DEFAULT_RELATIONS, Relation


@dataclass
class MemoryConfig:
    db_path: str = "engram.db"
    relations: dict[str, Relation] = field(default_factory=lambda: dict(DEFAULT_RELATIONS))
    # recall assembly
    max_subgraph_edges: int = 40
    max_recent_episodes: int = 12
    # compiled-wiki cache: recompile when this many writes have landed since the
    # last compile (0 disables the wiki layer → recall renders the subgraph only).
    wiki_recompile_after_writes: int = 8
