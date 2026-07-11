"""The write path: one interaction event → typed edges + a dated episode.

An `Event` is whatever the host observed: a chat turn/session, a sent or received
email, a tool/document result. The host tells veracium who authored the content
(`author`) — the single most important input for injection resistance, since
third-party-authored content is the attack surface.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from . import prompts
from ._json import extract_json
from .graph import apply_supersession
from .llm.base import Complete
from .schema import (DEFAULT_RELATIONS, Disclosure, Edge, Episode, EvidenceAuthor,
                     Provenance, QUARANTINE_RELATION, Relation, SourceType,
                     Volatility, utcnow)


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _event_dt(date_str: str) -> datetime:
    """The event's own date drives valid_from / observed_at — memory timestamps
    must reflect when facts held, not wall-clock ingest time."""
    try:
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except ValueError:
        return utcnow()


def _disclosure_for(author: EvidenceAuthor, relation: str) -> Disclosure:
    """Structural quarantine (defense in depth over the extractor's routing):
    a third-party CLAIM is quarantined; a third-party inference is use-only;
    user/system content is mentionable."""
    if relation == QUARANTINE_RELATION:
        return Disclosure.QUARANTINED
    if author == EvidenceAuthor.THIRD_PARTY:
        return Disclosure.USE_ONLY
    return Disclosure.MENTIONABLE


def _source_type(author: EvidenceAuthor, event_type: str) -> SourceType:
    if event_type == "chat":
        return SourceType.STATED
    if author == EvidenceAuthor.USER:
        return SourceType.STATED       # user-authored (e.g. sent mail)
    return SourceType.INFERRED         # derived from third-party/tool content


def ingest_event(store, llm: Complete, user_id: str, *, event_text: str,
                 author: EvidenceAuthor, date: str, event_type: str = "chat",
                 evidence_ref: Optional[str] = None,
                 relations: dict[str, Relation] = DEFAULT_RELATIONS) -> dict:
    """Extract and persist memory from one event. Returns a small summary dict
    (counts + the episode) for logging/telemetry."""
    evidence_ref = evidence_ref or _uid("ev")
    rel_names = ", ".join(relations)
    prompt = prompts.EXTRACT_PROMPT.format(
        date_context=prompts.date_context(date), author=author.value,
        event_text=event_text, relations=rel_names)
    raw = llm(prompt, system=prompts.EXTRACT_SYSTEM, role="distill",
              json_schema=prompts.EXTRACT_SCHEMA)
    data = extract_json(raw)
    when = _event_dt(date)

    # episode — always recorded; carries author so the gate knows a third-party
    # episode records receipt, not truth.
    episode_text = str(data.get("episode", "")).strip()
    if episode_text:
        store.add_episode(Episode(
            id=_uid("ep"), user_id=user_id, date=date, summary=episode_text,
            provenance=Provenance(source_type=_source_type(author, event_type),
                                  author_of_evidence=author, evidence_ref=evidence_ref,
                                  observed_at=when)))

    n_facts = n_quarantined = 0
    for t in data.get("triples", []):
        if not (isinstance(t, dict) and t.get("subject") and t.get("relation") and t.get("object")):
            continue
        relation = str(t["relation"]).strip()
        disclosure = _disclosure_for(author, relation)
        try:
            vol = Volatility(str(t.get("volatility", "durable")).strip().lower())
        except ValueError:
            vol = Volatility.DURABLE
        edge = Edge(
            id=_uid("e"), user_id=user_id, subject=str(t["subject"]).strip(),
            relation=relation, object=str(t["object"]).strip(),
            note=str(t.get("note", "")).strip(), volatility=vol,
            provenance=Provenance(source_type=_source_type(author, event_type),
                                  author_of_evidence=author, evidence_ref=evidence_ref,
                                  disclosure=disclosure, observed_at=when),
            valid_from=when)
        apply_supersession(store, edge, relations)
        if edge.quarantined:
            n_quarantined += 1
        else:
            n_facts += 1
    return {"episode": episode_text, "facts": n_facts, "quarantined": n_quarantined}
