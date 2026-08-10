"""The write path: one interaction event → typed edges + a dated episode.

An `Event` is whatever the host observed: a chat turn/session, a sent or received
email, a tool/document result. The host tells veracium who authored the content
(`author`) — the single most important input for injection resistance, since
third-party-authored content is the attack surface.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
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


# A host clock may be a little ahead of ours; a host clock is never a year
# ahead. One day absorbs timezone slop and NTP drift without absorbing a typo.
MAX_FUTURE_SKEW = timedelta(days=1)


def _event_dt(date_str: str) -> datetime:
    """The event's own date drives valid_from / observed_at — memory timestamps
    must reflect when facts held, not wall-clock ingest time.

    A future date is REJECTED (beyond `MAX_FUTURE_SKEW`). It has no legitimate
    meaning — the event date is when a statement was made, not what it is about,
    so "expires in 2027" is an object value and never an event date — and it was
    unrecoverable in both fields it reaches:

      valid_from  → renders "(since 2099)" into answer context, a false
                    statement about the future.
      observed_at → `confirm()` advances it with max() (reinforcement no longer
                    touches the prior — accepted `specs/0012` Design 1), which
                    is what correctly defeats BACK-dating and is therefore
                    exactly what makes forward-dating permanent. One host date
                    removed an edge from lapse, decay and staleness flagging
                    for 73 years, with no API to undo it.

    A malformed date is REJECTED for the same reason. This used to fall back to
    `utcnow()`, which is the same manufacture in a quieter form: **a malformed
    statement about when an event happened is not evidence that it happened
    now.** The fallback could refresh a stale fact, relieve lifecycle pressure
    through a later `observed_at`, and write an audit record attributing an
    invented time to the caller — while the caller believed it had supplied one.

    Fails closed and loudly rather than clamping or defaulting: a bad event date
    is unambiguously a caller bug, and silently rewriting it hides that. Callers
    that genuinely mean *now* omit `date=` entirely; absence is the only thing
    that means now."""
    try:
        dt = datetime.fromisoformat(date_str)
        # An offset-bearing timestamp is CONVERTED, never relabelled. `.replace(
        # tzinfo=utc)` discarded the offset, so `...T20:00-12:00` was checked as
        # if it were 20:00 UTC when the instant is 08:00 the next day —
        # measured at 12 hours of skew-limit bypass, and up to 26 across the
        # legal offset range. A naive value still means UTC, which is the
        # documented contract for a bare date.
        dt = (dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None
              else dt.astimezone(timezone.utc))
    except (ValueError, TypeError):
        raise ValueError(
            f"event date {date_str!r} is not an ISO date. Memory timestamps "
            f"record when a statement was made; falling back to the current "
            f"time would manufacture an observation date the caller never "
            f"supplied. Omit `date=` if you mean now.") from None
    if dt > utcnow() + MAX_FUTURE_SKEW:
        raise ValueError(
            f"event date {date_str!r} is in the future. Memory timestamps record "
            f"when a statement was made; a future date makes a fact permanently "
            f"fresh (observed_at only ever advances) and renders a false "
            f"'(since …)' into answer context. If the future date is what the "
            f"fact is ABOUT, it belongs in the value, not in `date=`.")
    return dt


def _disclosure_for(author: EvidenceAuthor, relation: str,
                    derived_from: Optional[EvidenceAuthor] = None) -> Disclosure:
    """Structural quarantine (defense in depth over the extractor's routing):
    a third-party CLAIM is quarantined; a third-party inference is use-only;
    user/system content is mentionable. Trust is capped at the MINIMUM of the
    event's author and its declared content source (`derived_from`) — a
    system-authored event whose text embeds third-party material never yields
    mentionable edges, whatever the extractor thinks."""
    if relation == QUARANTINE_RELATION:
        return Disclosure.QUARANTINED
    if (author == EvidenceAuthor.THIRD_PARTY
            or derived_from == EvidenceAuthor.THIRD_PARTY):
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
                 derived_from: Optional[EvidenceAuthor] = None,
                 source_id: Optional[str] = None,
                 relations: dict[str, Relation] = DEFAULT_RELATIONS) -> dict:
    """Extract and persist memory from one event. Returns a small summary dict
    (counts + the episode) for logging/telemetry. `derived_from` declares that
    the event's content embeds material from a lower-trust source; disclosure
    and episode routing are capped accordingly (see _disclosure_for).

    `source_id` (specs/0006) is an OPAQUE, HOST-supplied source identifier — a
    mailbox, a connector instance, a device. It is set on the provenance of every
    record this event produces and is NEVER read from the extractor output (I1):
    the model does not see it and cannot name it, so it is settled by the host
    entry point, not by content. `origin` is deliberately NOT a parameter — a
    LOCAL caller can never supply it (I2a); it stays absent and resolves to the
    store's `store_identity` singleton at read (§4 rule 6)."""
    evidence_ref = evidence_ref or _uid("ev")
    rel_names = "\n".join(
        f"- {name}: {rel.desc}" if rel.desc else f"- {name}"
        for name, rel in relations.items())
    # Normalise ONCE, then pass the normalised value to every consumer.
    # Validating here and then handing the RAW string to date_context still left
    # two parsers: `date_context` calls `date.fromisoformat`, which rejects an
    # offset-bearing timestamp, so `remember(date="...T12:00:00+05:30")` raised
    # `Invalid isoformat string` after _event_dt had already accepted it. The
    # single-contract claim was true of the helper and false of the entry point.
    # Normalise ONCE and reuse `when` everywhere. Re-deriving from the reduced
    # `date` string loses the time of day: the unparseable-extraction branch did
    # `_event_dt(date)` after `date` had already become a bare date, so an input
    # of 12:30+05:30 stored observed_at as midnight instead of 07:00 UTC.
    # "One input, two parsers" became "one input, two normalisations" -- the
    # same failure the normalisation was added to fix.
    when = _event_dt(date)
    date = when.date().isoformat()
    prompt = prompts.EXTRACT_PROMPT.format(
        date_context=prompts.date_context(date), author=author.value,
        event_text=event_text, relations=rel_names)
    raw = llm(prompt, system=prompts.EXTRACT_SYSTEM, role="distill",
              json_schema=prompts.EXTRACT_SCHEMA)
    try:
        data = extract_json(raw)
        if isinstance(data, list):
            # a bare array is the triples payload with its wrapper omitted
            data = {"triples": data}
    except ValueError:
        # The distiller sometimes answers in prose instead of JSON — typically a
        # refusal on jailbreak-shaped or degenerate input. That's an input
        # condition (the BYO contract tolerates schema-ignoring providers), not
        # a veracium defect: no facts, but the turn still leaves history — a
        # content-free placeholder episode (never the raw event text: that would
        # feed unmediated, possibly adversarial input straight into recall
        # prompts). evidence_ref lets the host audit what the event was.
        summary = (f"(unprocessed {event_type} event — extraction returned no "
                   f"parseable JSON; content not retained)")
        store.add_episode(Episode(
            id=_uid("ep"), user_id=user_id, date=date, summary=summary,
            provenance=Provenance(source_type=_source_type(author, event_type),
                                  author_of_evidence=author, evidence_ref=evidence_ref,
                                  derived_from=derived_from, source_id=source_id, observed_at=when)))
        return {"episode": summary, "facts": 0, "quarantined": 0, "unparseable": True}

    # episode — always recorded; carries author so the gate knows a third-party
    # episode records receipt, not truth.
    episode_text = str(data.get("episode", "")).strip()
    if episode_text:
        store.add_episode(Episode(
            id=_uid("ep"), user_id=user_id, date=date, summary=episode_text,
            provenance=Provenance(source_type=_source_type(author, event_type),
                                  author_of_evidence=author, evidence_ref=evidence_ref,
                                  derived_from=derived_from, source_id=source_id, observed_at=when)))

    n_facts = n_quarantined = 0
    for t in data.get("triples", []):
        if not (isinstance(t, dict) and t.get("subject") and t.get("relation") and t.get("object")):
            continue
        relation = str(t["relation"]).strip()
        disclosure = _disclosure_for(author, relation, derived_from)
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
                                  disclosure=disclosure, derived_from=derived_from,
                                  source_id=source_id, observed_at=when),
            valid_from=when)
        apply_supersession(store, edge, relations)
        if edge.quarantined:
            n_quarantined += 1
        else:
            n_facts += 1
    return {"episode": episode_text, "facts": n_facts, "quarantined": n_quarantined}
