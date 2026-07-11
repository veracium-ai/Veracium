"""engram — a provenance-aware memory plug-in for agentic systems.

    from engram import Memory
    from engram.llm.anthropic import AnthropicComplete

    mem = Memory(llm=AnthropicComplete())          # or any Complete callable
    mem.remember("alice", "USER: I'm vegetarian and have a dog named Ollie.")
    ctx = mem.recall("alice", "what should I keep in mind for lunch?")
    print(ctx.context)   # grounded, provenance-flagged memory for your prompt

Design (validated in the `agent-memory` research repo): a typed graph + dated
episodes are the store of record; recall assembles an entity-matched subgraph
(and, when enabled, an LLM-curated wiki) with third-party claims structurally
quarantined. Memory is per-user; one user's memory never reaches another's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .config import MemoryConfig
from .graph import render_edges, subgraph_for_query
from .ingest import ingest_event
from .llm.base import Complete, Embed
from .schema import Edge, Episode, EvidenceAuthor
from .store.base import Store
from .store.sqlite import SqliteStore

__all__ = ["Memory", "MemoryConfig", "Recall", "Store", "SqliteStore",
           "Complete", "Embed", "EvidenceAuthor"]


@dataclass
class Recall:
    """The result of a recall: a ready-to-inject `context` string plus the
    structured `edges`/`episodes` it was built from (for the host to inspect
    provenance or build its own prompt)."""
    context: str
    edges: list[Edge]
    episodes: list[Episode]


class Memory:
    def __init__(self, *, llm: Complete, store: Optional[Store] = None,
                 embed: Optional[Embed] = None, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.store = store or SqliteStore(self.config.db_path)
        self.llm = llm
        self.embed = embed

    # -- write -------------------------------------------------------------
    def remember(self, user_id: str, event_text: str, *,
                 author: EvidenceAuthor = EvidenceAuthor.USER,
                 date: Optional[str] = None, event_type: str = "chat",
                 evidence_ref: Optional[str] = None) -> dict:
        """Ingest one interaction event into `user_id`'s memory.

        `author` is the trust-critical input: use EvidenceAuthor.THIRD_PARTY for
        received email / external documents so their claims are quarantined."""
        from datetime import date as _date
        date = date or _date.today().isoformat()
        return ingest_event(self.store, self.llm, user_id, event_text=event_text,
                            author=author, date=date, event_type=event_type,
                            evidence_ref=evidence_ref, relations=self.config.relations)

    # -- read --------------------------------------------------------------
    def recall(self, user_id: str, query: str) -> Recall:
        """Assemble grounded memory context for answering `query`.

        v0.1: entity-matched subgraph + recent episodes, third-party claims
        rendered under an explicit never-assert flag. The LLM-curated wiki layer
        and the evidence-grounded abstention gate land next; the seams
        (config.wiki_recompile_after_writes, provenance on every unit) are in
        place for them.
        """
        edges = subgraph_for_query(self.store, user_id, query,
                                   max_edges=self.config.max_subgraph_edges)
        episodes = self.store.episodes(user_id)[-self.config.max_recent_episodes:]
        parts = []
        if edges:
            parts.append("## KNOWN FACTS\n" + render_edges(edges))
        if episodes:
            parts.append("## RECENT HISTORY\n" + "\n".join(
                f"[{e.date}] {e.summary}"
                + ("  (third-party report — unverified)"
                   if e.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY else "")
                for e in episodes))
        context = "\n\n".join(parts) if parts else "(no memory yet for this user)"
        return Recall(context=context, edges=edges, episodes=episodes)

    def close(self) -> None:
        self.store.close()
