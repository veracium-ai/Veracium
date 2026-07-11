"""Graph operations: functional supersession and entity-matched subgraph render.

Pure logic over the store — no LLM, no I/O beyond the store handle — so this is
the offline-testable heart of memory correctness (supersession-with-history is
the category the research found the industry worst at, and where veracium's design
scored best).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from .schema import DEFAULT_RELATIONS, Edge, Relation


def apply_supersession(store, edge: Edge, relations: dict[str, Relation]) -> None:
    """Persist a new edge with supersession and reinforcement:

    - Reinforcement: if an active edge already asserts the same
      (subject, relation, object), refresh its validity to the new date instead
      of adding a duplicate — so re-stating a fact keeps it alive (a re-mentioned
      transient state won't lapse) and clears any stale-confirmation flag.
    - Supersession: for a *functional* relation, a new value invalidates the
      prior active value (retained, reason 'superseded'), so history stays queryable.
    - Non-functional relations otherwise accumulate.
    """
    same = edge.object.strip().lower()
    for prior in store.edges(edge.user_id, subject=edge.subject, relation=edge.relation):
        if prior.id == edge.id:
            continue
        if prior.object.strip().lower() == same:  # reinforcement
            prior.valid_from = edge.valid_from
            prior.provenance.observed_at = edge.provenance.observed_at
            prior.provenance.confidence = max(prior.provenance.confidence,
                                              edge.provenance.confidence)
            prior.needs_confirmation = False
            store.add_edge(prior)
            return
    rel = relations.get(edge.relation)
    if rel and rel.functional:
        for prior in store.edges(edge.user_id, subject=edge.subject, relation=edge.relation):
            if prior.id != edge.id and prior.object.strip().lower() != same:
                store.invalidate_edge(prior.id, edge.valid_from, "superseded")
                edge.supersedes = prior.id
    store.add_edge(edge)


_STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on",
         "for", "and", "or", "s", "does", "did", "what", "who", "when", "where",
         "how", "which", "with", "her", "his", "their", "they", "do", "have"}


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP and len(w) > 2}


def subgraph_for_query(store, user_id: str, query: str, *, max_edges: int = 40) -> list[Edge]:
    """Entity-matched neighborhood: every edge off the user node, plus edges whose
    subject/object tokens appear in the query. This is veracium's primary retrieval
    (the research found it beat similarity search on every question type). Includes
    superseded edges (rendered as history) and quarantined edges (rendered flagged)
    so the caller can show provenance."""
    q = _tokens(query)
    scored: list[tuple[int, Edge]] = []
    for e in store.edges(user_id, active_only=False):
        if e.subject == "user":
            base = 2
        else:
            overlap = _tokens(e.subject + " " + e.object + " " + e.note) & q
            base = len(overlap)
        if base:
            # prefer active over superseded, and closer matches
            scored.append((base + (1 if e.active else 0), e))
    scored.sort(key=lambda t: -t[0])
    return [e for _, e in scored[:max_edges]]


def render_edges(edges: list[Edge]) -> str:
    """Render edges as provenance-carrying lines for a prompt. Quarantined claims
    are fenced with an explicit never-assert marker; superseded edges show their
    validity range so history is visible without polluting the current value."""
    lines = []
    for e in edges:
        who = "" if e.subject == "user" else f"{e.subject} "
        note = f" — {e.note}" if e.note else ""
        if e.quarantined:
            lines.append(f"[UNVERIFIED third-party claim, never assert as fact] "
                         f"{e.subject} claims: {e.relation} {e.object}{note} ({e.valid_from.date()})")
        elif not e.active:
            lines.append(f"{who}{e.relation}: {e.object}{note} "
                         f"(SUPERSEDED {e.valid_from.date()}→{e.invalidated_at.date() if e.invalidated_at else '?'})")
        else:
            stale = " [possibly stale — confirm before relying on it]" if e.needs_confirmation else ""
            lines.append(f"{who}{e.relation}: {e.object}{note} (since {e.valid_from.date()}){stale}")
    return "\n".join(lines)
