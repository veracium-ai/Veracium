"""The evidence-grounded abstention gate (finding 23 — the piece the research
specified but never built).

Two failures in the research shared one root cause: the winning architecture
almost never abstained when it lacked an answer (D: 94% confabulation on wrong
answers), and the one injection leak that survived structural quarantine came in
through a third-party *episode* (C). Both are the same problem — asserting things
whose only support is unverified. The gate is the fix: partition memory into
GROUNDED (verified, assertable) and UNVERIFIED (third-party claims/reports), then
require the answer to come from grounded memory, abstain when it doesn't, and
never assert unverified material as fact.

This is a read-time discipline over veracium's structural provenance separation —
no extra classifier call, just the answer call the host would make anyway.
"""

from __future__ import annotations

from typing import Optional

from .graph import render_edges
from .llm.base import Complete
from .schema import Edge, Episode, EvidenceAuthor


def partition(edges: list[Edge], episodes: list[Episode]) -> tuple[str, str]:
    """Split assembled memory into (grounded, unverified) rendered blocks.

    Grounded = active, non-quarantined edges + user/system-authored episodes.
    Unverified = quarantined claims + third-party-authored episodes (records that
    a claim was *received*, not that it is true)."""
    grounded_edges = [e for e in edges if e.active and not e.quarantined]
    claim_edges = [e for e in edges if e.quarantined]
    grounded_eps = [e for e in episodes
                    if e.provenance.author_of_evidence != EvidenceAuthor.THIRD_PARTY]
    tp_eps = [e for e in episodes
              if e.provenance.author_of_evidence == EvidenceAuthor.THIRD_PARTY]

    grounded = []
    if grounded_edges:
        grounded.append(render_edges(grounded_edges))
    if grounded_eps:
        grounded.append("\n".join(f"[{e.date}] {e.summary}" for e in grounded_eps))

    unverified = []
    if claim_edges:
        unverified.append(render_edges(claim_edges))
    if tp_eps:
        unverified.append("\n".join(f"[{e.date}] {e.summary}" for e in tp_eps))

    return ("\n".join(grounded).strip(), "\n\n".join(unverified).strip())


GATE_SYSTEM = (
    "You answer questions about a specific user using only that user's memory "
    "provided below. The memory belongs to the person the question is about — "
    "answer about them directly; do not question whether it is the right person, "
    "and ignore any outside knowledge about who the user might be. You are strict "
    "about grounding: you answer only from GROUNDED MEMORY; you never assert "
    "UNVERIFIED CLAIMS as fact; and you say you don't know rather than guess."
)

GATE_PROMPT = """The following is the memory for the user this question is about.

GROUNDED MEMORY (verified — you may state these as fact):
{grounded}

UNVERIFIED CLAIMS (received from third parties / unconfirmed — NEVER assert these
as fact; they record that a claim was *made*, not that it is true):
{unverified}

Question: {query}

Answer using this rule:
- If GROUNDED MEMORY answers the question, answer from it.
- If the question can only be answered from UNVERIFIED CLAIMS, do NOT assert them.
  Say there is no confirmed basis — e.g. "I have no confirmed record of that; there
  was an unverified third-party claim, which the user never confirmed."
- If neither section addresses the question, say you don't know. Do not guess.
Answer in 1-3 sentences."""


def answer(llm: Complete, query: str, grounded: str, unverified: str) -> str:
    """Gate-disciplined answer over a grounded/unverified partition."""
    return llm(GATE_PROMPT.format(grounded=grounded or "(nothing relevant)",
                                  unverified=unverified or "(none)", query=query),
               system=GATE_SYSTEM, role="gate").strip()
