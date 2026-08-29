"""The write path: one interaction event → typed edges + a dated episode.

An `Event` is whatever the host observed: a chat turn/session, a sent or received
email, a tool/document result. The host tells veracium who authored the content
(`author`) — the single most important input for injection resistance, since
third-party-authored content is the attack surface.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import grounding, prompts
from ._json import extract_json
from .graph import apply_supersession
from .llm.base import Complete
from .schema import (DEFAULT_RELATIONS, Disclosure, Edge, Episode, EvidenceAuthor,
                     EvidenceContext,
                     Provenance, QUARANTINE_RELATION, Relation,
                     RESERVED_RELATIONS, UNCLASSIFIED_RELATION,
                     Volatility, utcnow)
from .registry import RegistryError, effective_registry, render_prompt_relations  # noqa: F401 (RegistryError is this boundary's named refusal)


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


# specs/0011 §4d (E4): absence of a context declares NOTHING and gets the
# conservative floor. This constant is the floor's ONE carrier; the absence
# path reads it by name so the two ways of reaching THIRD_PARTY — floored
# absence vs an explicit derived(THIRD_PARTY) — stay distinct code paths
# a refactor cannot collapse (S5's distinctness cell monkeypatches it).
_ABSENT_CONTEXT_FLOOR = EvidenceAuthor.THIRD_PARTY


def _resolve_context(context, derived_from):
    """Resolve the host's ingress declaration to an effective derived_from
    (specs/0011 §4d, E4) — total over the grammar, run BEFORE any write.

    - context absent + legacy `derived_from=X`: X was a positive declaration
      already — honoured as derived(X), unchanged.
    - context absent + nothing declared: the floor — derived(THIRD_PARTY).
      Absence is never the trusted cell.
    - `EvidenceContext.direct()`: first-party capture attested — None.
    - `EvidenceContext.derived(X)`: as declared.
    - anything else RAISES with nothing written: a bare string, a non-context
      object, a subclass (the value object cannot be minted from a caller
      value, and a subclass could bypass construction validation), or BOTH
      carriers at once (two declarations of one fact is a host bug — loud
      beats guessing which one was meant).
    """
    if context is None:
        if derived_from is not None:
            return derived_from
        return _ABSENT_CONTEXT_FLOOR
    if type(context) is not EvidenceContext:
        raise TypeError(
            "context must be an EvidenceContext minted via "
            "EvidenceContext.direct() or EvidenceContext.derived(...); "
            f"got {type(context).__name__} {context!r} (specs/0011 §4d — "
            "the value object cannot be minted from a caller value)")
    if derived_from is not None:
        raise ValueError(
            "pass EITHER context= OR the legacy derived_from=, not both — "
            "two declarations of one fact is a host bug (specs/0011 §4d)")
    if context.kind == "direct":
        return None
    eff = context.derived_from
    if not isinstance(eff, EvidenceAuthor):   # belt over the constructor
        raise TypeError(
            f"EvidenceContext carries a non-EvidenceAuthor derived_from "
            f"{eff!r} — refused at the persistence site (specs/0011 §4d)")
    return eff


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
    # specs/0001 I11 (candidate): ASSISTANT — author or content source —
    # is use_only for EVERY subject; without this clause the enum addition
    # alone fails OPEN to mentionable.
    if (author == EvidenceAuthor.ASSISTANT
            or derived_from == EvidenceAuthor.ASSISTANT):
        return Disclosure.USE_ONLY
    return Disclosure.MENTIONABLE


def ingest_event(store, llm: Complete, user_id: str, *, event_text: str,
                 author: EvidenceAuthor, date: str, event_type: str = "chat",
                 evidence_ref: Optional[str] = None,
                 derived_from: Optional[EvidenceAuthor] = None,
                 context: Optional[EvidenceContext] = None,
                 source_id: Optional[str] = None,
                 relations: dict[str, Relation] = DEFAULT_RELATIONS) -> dict:
    """Extract and persist memory from one event. Returns a small summary dict
    (counts + the episode) for logging/telemetry.

    `context` (specs/0011 §4d, E4) is the host's POSITIVE ingress declaration:
    `EvidenceContext.direct()` attests first-party capture;
    `EvidenceContext.derived(X)` declares the content derives from class X.
    ABSENT context (and no legacy `derived_from`) floors to
    derived(THIRD_PARTY) — absence is never the trusted cell. A malformed
    context RAISES with nothing written. The legacy `derived_from=X` keyword
    remains honoured as a positive derived(X) declaration; passing both
    carriers raises. Disclosure and episode routing are capped on the
    EFFECTIVE class (see _disclosure_for).

    `source_id` (specs/0006) is an OPAQUE, HOST-supplied source identifier — a
    mailbox, a connector instance, a device. It is set on the provenance of every
    record this event produces and is NEVER read from the extractor output (I1):
    the model does not see it and cannot name it, so it is settled by the host
    entry point, not by content. `origin` is deliberately NOT a parameter — a
    LOCAL caller can never supply it (I2a); it stays absent and resolves to the
    store's `store_identity` singleton at read (§4 rule 6)."""
    # specs/0011 §4d (E4): resolve the host's ingress declaration FIRST —
    # every RAISES cell fires here, before the LLM runs or anything is
    # written. From this point on `derived_from` is the EFFECTIVE content
    # class: a declared derived(X), None for attested-direct, or the
    # THIRD_PARTY floor when the caller declared nothing.
    derived_from = _resolve_context(context, derived_from)
    evidence_ref = evidence_ref or _uid("ev")
    # specs/0025 §4b-ii: the host registry is validated AS SUPPLIED and
    # extracted into the ONE frozen per-event snapshot that feeds prompt
    # rendering, retry validation, membership, and supersession. RegistryError
    # propagates — an uninterpretable registry is the caller's error (X5/X9).
    reg = effective_registry(relations)
    # §4b-iv: the SELECTABLE set, insertion order — byte-identical to the
    # pre-0025 rendering for the default registry (X6's second carrier).
    rel_names = render_prompt_relations(reg)
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

    # 0023 §4a: ONE standing-state read per event, before any record is
    # written, so the whole event gets one verdict (an event half-quarantined
    # by a mid-ingest revocation would be worse than either whole answer).
    # Q4 (dev, resolved here): the audit line carries the DIGEST — content-
    # free, and it makes "which source is still writing" answerable from the
    # audit sink alone; a bare count answers only "how much".
    from .scope_linkage import identity_digest_of
    _birth_digest = identity_digest_of(None, source_id, store.local_origin()) \
        if source_id is not None and hasattr(store, "local_origin") else None
    revoked_at_birth = (_birth_digest is not None
                        and _birth_digest in store.standing_revocations(user_id))

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
            provenance=Provenance(author_of_evidence=author, evidence_ref=evidence_ref,
                                  # 0023 §4a (internal S3): the episode's OWN disclosure is
                                  # set at birth — third-party influence caps it at USE_ONLY
                                  # exactly as _disclosure_for caps the edges; C4 adds the
                                  # standing-revoked → QUARANTINED branch on this same field
                                  disclosure=(Disclosure.QUARANTINED if revoked_at_birth else _disclosure_for(author, "", derived_from)),
                                  derived_from=derived_from, source_id=source_id, observed_at=when)))
        return {"episode": summary, "facts": 0, "quarantined": 0, "unparseable": True,
                "supersessions": 0, "reinforcements": 0,
                # §4c: zeros PRESENT on the unparseable path — an absent key
                # is not a zero.
                "invalid": 0, "retried": 0, "recovered": 0, "residual": 0,
                "redispositioned": 0,
                "quarantined_at_birth": (1 if revoked_at_birth else 0),
                "birth_revocation_digest": (_birth_digest if revoked_at_birth
                                            else None)}

    # episode — always recorded; carries author so the gate knows a third-party
    # episode records receipt, not truth.
    episode_text = str(data.get("episode", "")).strip()
    if episode_text:
        store.add_episode(Episode(
            id=_uid("ep"), user_id=user_id, date=date, summary=episode_text,
            provenance=Provenance(author_of_evidence=author, evidence_ref=evidence_ref,
                                  # 0023 §4a (internal S3): the episode's OWN disclosure is
                                  # set at birth — third-party influence caps it at USE_ONLY
                                  # exactly as _disclosure_for caps the edges; C4 adds the
                                  # standing-revoked → QUARANTINED branch on this same field
                                  disclosure=(Disclosure.QUARANTINED if revoked_at_birth else _disclosure_for(author, "", derived_from)),
                                  derived_from=derived_from, source_id=source_id, observed_at=when)))

    n_facts = n_quarantined = n_supersessions = n_reinforcements = 0
    # ---- specs/0025 §4b(1): membership + the ONE retry per event ---------
    # Pass 1 collects the parsed triples with their ORIGINAL relation and
    # the disclosure ESTABLISHED from it (X10: the fallback below never
    # feeds _disclosure_for). Off-vocabulary triples — including an
    # extractor-emitted `unclassified`, which is not selectable (§4b-iv) —
    # queue for one retry; the residual lands on the reserved member with
    # the original in the typed field.
    parsed = []
    for t in data.get("triples", []):
        if not (isinstance(t, dict) and t.get("subject") and t.get("relation") and t.get("object")):
            continue
        original = str(t["relation"]).strip()
        # specs/0024 §4a: the canonical subject is computed ONCE and used for
        # both the coherence test and the stored Edge, so the test can never
        # disagree with the subject the record carries.
        parsed.append({"t": t, "relation": original, "original": original,
                       "subject": str(t["subject"]).strip(),
                       "off": original not in reg or original == UNCLASSIFIED_RELATION})

    # ---- specs/0024 §4a/§4b: authorship before structural quarantine -----
    # Step 1 of the combined pipeline (specs/0025 §4b-iii): the coherence
    # test runs BEFORE vocabulary enforcement — `third_party_claim` is
    # registry-resident, so enforcement alone would pass the contradiction
    # through. The predicate is mechanical: whole-string casefold equality
    # on the canonical subject; odd types fail closed (str(["user"]) is
    # "['user']", not "user"). An incoherent triple is re-dispositioned,
    # not dropped: its relation becomes the reserved NON-FUNCTIONAL member
    # (USABLE — never assertable, never superseding; A1's chosen cell),
    # the original survives in Edge.original_relation, and the rewrite
    # targets a registry-resident relation so it never enters the
    # vocabulary fallback below.
    n_redispositioned = 0
    for row in parsed:
        if (row["relation"] == QUARANTINE_RELATION
                and row["subject"].casefold() == "user"):
            row["relation"] = UNCLASSIFIED_RELATION
            row["redisposition"] = True
            n_redispositioned += 1

    failing = [row for row in parsed if row["off"]]
    n_invalid = len(failing)
    n_retried = n_recovered = 0
    if failing and llm is not None:
        n_retried = len(failing)
        try:
            raw = llm(prompts.RETRY_PROMPT.format(
                relations=rel_names,
                failing=json.dumps([{"subject": str(r["t"]["subject"]).strip(),
                                     "relation": r["original"],
                                     "object": str(r["t"]["object"]).strip()}
                                    for r in failing], ensure_ascii=False)),
                      system=prompts.EXTRACT_SYSTEM, role="distill-retry")
            reps = extract_json(raw).get("triples", [])
            if not isinstance(reps, list):
                reps = []
        except Exception:
            reps = []          # malformed output / provider failure: a no-op,
                               # visible as retried > 0, recovered = 0 — never
                               # re-raised, never a second call (§4b(1))
        def _norm(x):
            return str(x).strip().casefold()
        # one-to-one multiset consumption in occurrence order; a repair must
        # be an ORDINARY member (reserved answers are not recoveries)
        pool = []
        for rep in reps:
            if isinstance(rep, dict):
                rrel = str(rep.get("relation", "")).strip()
                if rrel in reg and rrel not in RESERVED_RELATIONS:
                    pool.append(((_norm(rep.get("subject", "")),
                                  _norm(rep.get("object", ""))), rrel))
        for row in failing:
            key = (_norm(row["t"]["subject"]), _norm(row["t"]["object"]))
            for i, (pkey, prel) in enumerate(pool):
                if pkey == key:
                    pool.pop(i)
                    row["relation"] = prel
                    row["off"] = False
                    n_recovered += 1
                    break
    n_residual = 0
    for row in parsed:
        if row["off"]:
            row["relation"] = UNCLASSIFIED_RELATION
            n_residual += 1

    for row in parsed:
        t = row["t"]
        relation = row["relation"]
        # 0025 §4b-iii step 2: disclosure is established for the POST-
        # COHERENCE semantic state — USE_ONLY for a re-dispositioned
        # triple (0024 §4b as amended by A1, ACCEPTED round 24: the
        # label's collapse licenses use, not assertion — the measured
        # population behind the label is 4 genuine relays per 1 genuine
        # self-statement), the ORIGINAL relation otherwise (X10 is
        # scoped to the VOCABULARY fallback, which never feeds this
        # call). Established once, retained; the accepted floors below
        # only lower.
        disclosure = (Disclosure.USE_ONLY if row.get("redisposition")
                      else _disclosure_for(author, row["original"],
                                           derived_from))
        if revoked_at_birth:
            # 0023 §4a QUARANTINE-AT-BIRTH: the event's source is standing-
            # revoked, so every edge of the event lands QUARANTINED whatever
            # the relation says — the FLOOR of the two verdicts, never a
            # substitute for them. Q1 (resolved, both names): no host-
            # configurable refusal mode; Q2 (ratified): a later lift does NOT
            # revisit this floor.
            disclosure = Disclosure.QUARANTINED
        try:
            vol = Volatility(str(t.get("volatility", "durable")).strip().lower())
        except ValueError:
            vol = Volatility.DURABLE
        obj = str(t["object"]).strip()
        # specs/0019 §4a: between extraction and storage, the object's
        # specifics are checked against the event text (the §4b predicate;
        # the event's own date is the session date — the remember contract).
        # A failing edge is STORED with the flag — never refused, never
        # demoted, never re-derived (§4d: immutable for the record's life).
        flagged = grounding.ungrounded(obj, event_text, date)
        edge = Edge(
            id=_uid("e"), user_id=user_id, subject=row["subject"],
            relation=relation, object=obj,
            original_relation=(row["original"] if relation != row["original"]
                               else None),
            note=str(t.get("note", "")).strip(), volatility=vol,
            ungrounded=flagged,
            provenance=Provenance(author_of_evidence=author, evidence_ref=evidence_ref,
                                  disclosure=disclosure, derived_from=derived_from,
                                  source_id=source_id, observed_at=when),
            valid_from=when)
        c = apply_supersession(store, edge, relations)
        n_supersessions += c.superseded
        n_reinforcements += c.reinforced
        if edge.quarantined:
            n_quarantined += 1
        else:
            n_facts += 1
    return {"episode": episode_text, "facts": n_facts, "quarantined": n_quarantined,
            "supersessions": n_supersessions, "reinforcements": n_reinforcements,
            # specs/0025 §4c — THE counter inventory, present on every path;
            # `redispositioned` is 0024's counter (U7): live on this path,
            # 0 on the unparseable path — an absent key is not a zero.
            "invalid": n_invalid, "retried": n_retried,
            "recovered": n_recovered, "residual": n_residual,
            "redispositioned": n_redispositioned,
            # specs/0023 Q4 (RESOLVED 2026-08-22, per the recorded leaning):
            # the quarantine-at-birth AUDIT facts — the content-free identity
            # digest answers "which source is still writing" from the audit
            # sink alone. ALWAYS present (an absent key is not a zero); the
            # audit sink is the consumer, telemetry's whitelist drops them,
            # the MCP surface strips them.
            "quarantined_at_birth": (n_quarantined if revoked_at_birth else 0),
            "birth_revocation_digest": (_birth_digest if revoked_at_birth
                                        else None)}
