"""The write path: one interaction event → typed edges + a dated episode.

An `Event` is whatever the host observed: a chat turn/session, a sent or received
email, a tool/document result. The host tells veracium who authored the content
(`author`) — the single most important input for injection resistance, since
third-party-authored content is the attack surface.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import agreement, grounding, prompts
from ._json import extract_json
from .graph import apply_supersession
from .llm.base import Complete
from .schema import (DEFAULT_RELATIONS, Disclosure, Edge,
                     Episode, EvidenceAuthor,
                     EvidenceContext,
                     Provenance, QUARANTINE_RELATION, Relation,
                     RESERVED_RELATIONS, UNCLASSIFIED_RELATION,
                     Volatility, is_procedural_relation, utcnow)
from .registry import RegistryError, effective_registry, render_prompt_relations  # noqa: F401 (RegistryError is this boundary's named refusal)


def _instruction_key(text: str) -> str:
    """specs/0038 §2b — the comparison key under which a triple's object
    "carries the same content" as a declared instruction: casefolded, inner
    whitespace collapsed, surrounding whitespace and punctuation stripped. The
    reviewer's own case is the motivating pair ("Run the formatter before
    committing." ↔ "run the formatter before committing"). EQUALITY under this
    key, deliberately nothing looser: containment or similarity would decide
    that a triple IS an instruction without the model saying so — the free-text
    detection §10 Q6 retired on measured evidence."""
    return " ".join(str(text).casefold().split()).strip(" \t\r\n.,;:!?\"'`“”‘’()[]{}")


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# A host clock may be a little ahead of ours; a host clock is never a year
# ahead. One day absorbs timezone slop and NTP drift without absorbing a typo.
MAX_FUTURE_SKEW = timedelta(days=1)

#: specs/0025 (amended 2026-09-08): the subject REFUSAL for a FACT — exactly
#: the defect and no wider. A subject carrying `|` is the prompt's former
#: alternation separator taken literally (`user|person:X|org:Acme Corp`,
#: measured under gpt-4o-mini): it absorbs the attribute being asserted, so
#: the fact files under a subject nothing else shares and supersession is
#: never invoked. Everything the shipped suite already stores keeps
#: storing: `user` in any case (0024 §4a canonicalises by casefold), the
#: `<kind>:<name>` forms the prompt names, a host's `task:` forms, and a
#: BARE entity name (`Rex` under `has_diet`, the B07 relay shape 0026
#: governs) — a `kind:name`-only grammar would have dropped that last class
#: silently, which is a wider change than the finding. NOT applied to
#: `third_party_claim`, for the reason the rule exists: a receipt record
#: supersedes nothing, so a pipe in its CLAIMANT slot cannot cause the harm
#: this refusal prevents (a fact hidden from supersession under a subject
#: nothing else shares); the claimant stays free text and quarantined, as
#: 0024's coherence step already governs it. The exemption is by RELATION,
#: checked before the rule; no other relation gets a pass.
_SUBJECT_OFF_GRAMMAR = re.compile(r"\|")


def subject_off_grammar(subject) -> bool:
    """True iff the extractor-returned subject is refused (dropped, counted)."""
    return bool(_SUBJECT_OFF_GRAMMAR.search(str(subject)))


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


def _emit_degrade(on_degrade, kind: str, payload: dict) -> None:
    """specs/0039 §2c — the ONE guarded way a degrade site invokes the host's
    callback. Returns at once when there is no callback; otherwise invokes it
    inside `try/except Exception: pass` — never re-raises, never logs, never
    retries. A `BaseException` (KeyboardInterrupt, SystemExit) is deliberately
    NOT caught. No site calls `on_degrade` directly (V-CALLBACK-CONTAINED)."""
    if on_degrade is None:
        return
    try:
        on_degrade(kind, payload)
    except Exception:
        pass


def _len_sha16(text: str) -> tuple[int, str]:
    """specs/0039 §2a: the UTF-8 BYTE length of `text` and the first sixteen hex
    digits of SHA-256 over exactly those bytes — never the text."""
    b = text.encode("utf-8")
    return len(b), hashlib.sha256(b).hexdigest()[:16]


def _answer_fields(raw) -> dict:
    """§2a `answer_len`/`answer_sha16` over the provider's raw answer exactly as the
    `Complete` callable returned it (a non-str return is measured as its str form)."""
    n, h = _len_sha16(raw if isinstance(raw, str) else str(raw))
    return {"answer_len": n, "answer_sha16": h}


def ingest_event(store, llm: Complete, user_id: str, *, event_text: str,
                 author: EvidenceAuthor, date: str, event_type: str = "chat",
                 evidence_ref: Optional[str] = None,
                 derived_from: Optional[EvidenceAuthor] = None,
                 context: Optional[EvidenceContext] = None,
                 source_id: Optional[str] = None,
                 relations: dict[str, Relation] = DEFAULT_RELATIONS,
                 on_degrade=None) -> dict:
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
    # specs/0037 §4b (V-BASIS-SCOPE): the extractor path cannot produce a
    # procedural record, so a basis on its context is a caller error —
    # REFUSED, nothing written; accepting it silently would ship declarative
    # basis as a hidden feature. `Memory.record_procedure` is the surface.
    if context is not None and getattr(context, "basis", None) is not None:
        raise ValueError(
            f"basis={context.basis!r} is not applicable to a declarative event — "
            "the extractor path writes no procedural record; record a procedure "
            "through Memory.record_procedure (specs/0037 §4b, V-BASIS-SCOPE)")
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
    # specs/0039 §2a: which check the unparseable branch was reached from —
    # the extractor finding no JSON (`no_json`) or 0038's instructions-type
    # rule (`instructions_type`); the record carries the cause, never the text.
    unparseable_cause = "no_json"
    try:
        data = extract_json(raw)
        if isinstance(data, list):
            # a bare array is the triples payload with its wrapper omitted
            data = {"triples": data}
        # specs/0038 §2c row 2: `instructions` PRESENT but not a list (a string,
        # a dict, null) is a malformed response, not a malformed member — the
        # unparseable branch below, with every counter present at zero. Row 1
        # (absent) is NOT this: an omitting provider is processed as today.
        if "instructions" in data and not isinstance(data["instructions"], list):
            unparseable_cause = "instructions_type"
            raise ValueError("instructions: expected a list")
    except ValueError:
        # specs/0039 §2c: the unparseable site — ONE record from the handler,
        # content-free (the extractor's own message embeds text[:200] of the
        # answer, which is exactly why only length and digest travel).
        _emit_degrade(on_degrade, "unparseable",
                      {"cause": unparseable_cause, **_answer_fields(raw)})
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
                # specs/0038 §2c row 8: the refusal counter on the one path
                # that never parsed a response — present, zero.
                "instructions_dropped": 0,
                "subject_refused": 0,          # specs/0025 (amended 2026-09-08): present, zero
                "quarantined_at_birth": (1 if revoked_at_birth else 0),
                "birth_revocation_digest": (_birth_digest if revoked_at_birth
                                            else None),
                "agreement_floored": 0, "agreement_recorded": 0}

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
    # ---- specs/0038 §2b: a DECLARED instruction is filed, never stored ----
    # The extractor files instructions in `instructions`; a triple whose
    # object carries the same content is REFUSED here, at the pass-1 filter
    # and before any Edge exists, and the REFUSAL is counted. Well-formedness
    # (§2c rows 3–4): non-string and empty/whitespace members are dropped and
    # never counted; the set de-duplicates declarations, so the count is of
    # refusals, never of things the model said. The rule reaches only what
    # the model DECLARED — a provider that coerces without declaring is
    # today's behaviour, measured by research's harness, not caught here.
    declared = {_instruction_key(m) for m in (data.get("instructions") or [])
                if isinstance(m, str) and m.strip()}
    declared.discard("")
    n_instructions_dropped = 0
    n_subject_refused = 0
    # specs/0039 §2c, the PRIMARY site (matrix rows 3–7, 10): once the answer is a
    # dict (a bare array having been wrapped above), a missing `triples` key or a
    # non-list value is RECORDED — and only recorded. The loop below then does
    # exactly what it did: a string or dict is iterated and every member skipped;
    # `null`, a number or a boolean raise TypeError in the loop AFTER this record
    # (record plus error, §2a; V-RECORD-ORDER-ON-ERROR). Outcomes unchanged.
    # specs/0025 §4c, AMENDED 2026-09-10 (the narrow fix, on the owner's word after
    # research's finding): a primary answer that yielded NO USABLE `triples` list is
    # marked in the RESULT, the one carrier every host has. Without it, a host passing
    # `diagnostics=None` — the documented default — got a dict byte-identical to a
    # legitimately empty extraction, so a broken provider was indistinguishable from a
    # model that found nothing. That is `0039` §1a's founding complaint, on the primary
    # path, and after the wider normalization rule it covered `null`, a number and a
    # boolean too. The two branches below are the whole class; a good or empty LIST is
    # a legitimate answer and is not marked.
    primary_unusable = False
    if "triples" not in data:
        _emit_degrade(on_degrade, "primary_failed",
                      {"cause": "no_triples_key", **_answer_fields(raw)})
        primary_unusable = True
    elif not isinstance(data["triples"], list):
        _emit_degrade(on_degrade, "primary_failed",
                      {"cause": "shape", **_answer_fields(raw)})
        primary_unusable = True
    n_members_skipped = 0        # specs/0039 §2a `member_skipped`: SHAPE-GUARD failures only
    # specs/0025 §4b(1), AMENDED 2026-09-10 (the WIDER normalization rule of `0039`
    # §10's fourth and sixth questions, on the owner's word): EVERY non-list `triples`
    # is the `shape` record written above and yields NO triples. One rule, both
    # callers, no exception — the retry has always applied it to `reps`. Before the
    # amendment a string or a dict was ITERATED here (every member skipped, zero facts,
    # silently) while `null`, a number or a boolean raised `TypeError` out of the loop:
    # a difference in iterability, not a property anyone chose. The outcome for a
    # string or a dict is unchanged; the three raising shapes now return zero facts
    # with their record, as their siblings always did.
    triples_in = data.get("triples")
    if not isinstance(triples_in, list):
        triples_in = []
    parsed = []
    for t in triples_in:
        if not (isinstance(t, dict) and t.get("subject") and t.get("relation") and t.get("object")):
            # every value reaching here IS a list member now (the normalization above),
            # so the list-ness guard this counter carried is gone with the amendment
            n_members_skipped += 1
            continue
        # specs/0025 (amended 2026-09-08 on the 0.20.0 selfcheck finding): the
        # SUBJECT GRAMMAR is enforced here, not only stated in the prompt. The
        # prompt's placeholder read `user|person:<name>|org:<name>` and one
        # documented provider took the pipes literally, storing
        # `user|person:X|org:Acme` as a subject — so "I changed jobs" filed
        # under two subjects and supersession was never invoked while the
        # selfcheck said PASS. A pipe-carrying subject cannot be re-filed the
        # way a relation is re-dispositioned (there is no truthful placeholder
        # for WHO a fact is about), and the retry re-emits the same subject,
        # so the triple is DROPPED and counted (`subject_refused`).
        if (str(t["relation"]).strip() != QUARANTINE_RELATION
                and subject_off_grammar(t["subject"])):
            n_subject_refused += 1
            continue
        # V-THIRD-PARTY-UNTOUCHED: a `third_party_claim` is a RECEIPT record
        # (0001/0023 — "received an unverified notice that …"), never a speech
        # act attributed to the user; refusing one because the extractor also
        # filed the notice's wording under `instructions` would erase the
        # received-claim history the trust gate depends on. The refusal
        # reaches every relation but that one — the mechanism the spec's own
        # invariant requires, named here because §2b does not name it.
        if (declared and str(t["relation"]).strip() != QUARANTINE_RELATION
                and _instruction_key(str(t["object"])) in declared):
            n_instructions_dropped += 1
            continue
        original = str(t["relation"]).strip()
        # specs/0024 §4a: the canonical subject is computed ONCE and used for
        # both the coherence test and the stored Edge, so the test can never
        # disagree with the subject the record carries.
        parsed.append({"t": t, "relation": original, "original": original,
                       "subject": str(t["subject"]).strip(),
                       # specs/0037 (V-EXTRACTOR-BLIND): a PROCEDURAL name the
                       # model emitted anyway (a prompt-injected name, a model
                       # that has seen the docs) is OFF-vocabulary exactly like
                       # any name the prompt did not carry — the registry holds
                       # it, the extractor's vocabulary never did
                       "off": (original not in reg or original == UNCLASSIFIED_RELATION
                               or is_procedural_relation(reg, original))})

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
    retry_degrade = None          # specs/0039 §2c: (cause, fields) or None — emitted ONCE below
    if failing and llm is not None:
        n_retried = len(failing)
        retry_raw = None
        try:
            retry_raw = raw = llm(prompts.RETRY_PROMPT.format(
                relations=rel_names,
                failing=json.dumps([{"subject": str(r["t"]["subject"]).strip(),
                                     "relation": r["original"],
                                     "object": str(r["t"]["object"]).strip()}
                                    for r in failing], ensure_ascii=False)),
                      system=prompts.EXTRACT_SYSTEM, role="distill-retry")
            retry_data = extract_json(raw)
            # specs/0025 §4b(1), AMENDED 2026-09-10 (drafted as specs/0039 §2e): the
            # extractor returns a bare JSON array "as a fallback for the caller to
            # normalize" (its docstring). The first extraction normalizes it; this
            # caller did not, so one of the function's two callers did not honour the
            # documented obligation of the function it calls — a contract-conformance
            # defect, not a symmetry preference. A bare-array retry answer is now a
            # recovery attempt, exactly as on the first extraction.
            if isinstance(retry_data, list):
                retry_data = {"triples": retry_data}
            # §2c: the key test runs STRICTLY AFTER dict-ness is established — on
            # a list `in` is a membership test, and a bare array must reach the
            # `.get` below and stay matrix row 8/9 (`bare_array`), never row 3.
            if isinstance(retry_data, dict) and "triples" not in retry_data:
                retry_degrade = ("no_triples_key", _answer_fields(raw))
            reps = retry_data.get("triples", [])
            if not isinstance(reps, list):
                # the shape branch: raises nothing (matrix rows 4–7 on the retry)
                if retry_degrade is None:
                    retry_degrade = ("shape", _answer_fields(raw))
                reps = []
        except Exception as e:
            reps = []          # malformed output / provider failure: a no-op,
                               # visible as retried > 0, recovered = 0 — never
                               # re-raised, never a second call (§4b(1))
            # specs/0039 §2c: which line raised decides the cause — the provider
            # call (`provider_error`, the message's length and digest only, the
            # class name never read), the extractor (`no_json`), or `.get` on a
            # bare array (`bare_array`, the CURRENT state the matrix asserts
            # until §2e's 0025 amendment lands)
            if retry_raw is None:
                n, h = _len_sha16(str(e))
                retry_degrade = ("provider_error", {"msg_len": n, "msg_sha16": h})
            elif isinstance(e, ValueError):
                retry_degrade = ("no_json", _answer_fields(retry_raw))
            else:
                retry_degrade = ("bare_array", _answer_fields(retry_raw))
        if retry_degrade is not None:
            cause, fields = retry_degrade
            _emit_degrade(on_degrade, "retry_failed", {"cause": cause, **fields})
        def _norm(x):
            return str(x).strip().casefold()
        # one-to-one multiset consumption in occurrence order; a repair must
        # be an ORDINARY member (reserved answers are not recoveries)
        pool = []
        for rep in reps:
            if not isinstance(rep, dict):
                n_members_skipped += 1       # specs/0039 §2a: the retry's shape guard
            if isinstance(rep, dict):
                rrel = str(rep.get("relation", "")).strip()
                # specs/0037: a repair can never land on a procedural
                # relation either — the retry vocabulary is the same
                # filtered one, and the pool enforces it (V-EXTRACTOR-BLIND)
                if (rrel in reg and rrel not in RESERVED_RELATIONS
                        and not is_procedural_relation(reg, rrel)):
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

    n_agreement_floored = n_agreement_recorded = 0
    n_volatility_defaulted = 0
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
            n_volatility_defaulted += 1      # specs/0039 §2b: counted per call, one record
        obj = str(t["object"]).strip()
        # specs/0019 §4a: between extraction and storage, the object's
        # specifics are checked against the event text (the §4b predicate;
        # the event's own date is the session date — the remember contract).
        # A failing edge is STORED with the flag — never refused, never
        # demoted, never re-derived (§4d: immutable for the record's life).
        flagged = grounding.ungrounded(obj, event_text, date)
        # specs/0026 §3b/§3c (ACCEPTED): the relay-marker scan over this
        # triple's note+object — pure, lexicon-closed, directional by
        # grammar. RESTRICT-ONLY: a restricting match (inbound or
        # ambiguous) FLOORS disclosure MENTIONABLE -> USE_ONLY and never
        # raises (QUARANTINED stays QUARANTINED, USE_ONLY stays); an
        # outbound (user-as-source) reading on a triple the extractor
        # DEMOTED to a third-party claim is §3c's demotion-direction
        # DISAGREEMENT — recorded as direction="user_source" with NO
        # disposition change. Marker absence is absence of evidence:
        # no record, no floor, byte-identical edge (V2/V7).
        note_str = str(t.get("note", "")).strip()
        # the FLOOR first (restrict-only: MENTIONABLE -> USE_ONLY, never
        # raise), keyed on whether a restricting match exists; then THE
        # one derivation site builds the record from the FINAL
        # disclosure (agreement.derive_record — shared with default-mode
        # import recomputation, so the boundaries cannot drift)
        if (agreement.relay_markers(note_str, obj)
                and disclosure == Disclosure.MENTIONABLE):
            disclosure = Disclosure.USE_ONLY
            n_agreement_floored += 1
        agr = agreement.derive_record(note_str, obj, disclosure,
                                      relation=relation)
        if agr is not None:
            n_agreement_recorded += 1
        edge = Edge(
            id=_uid("e"), user_id=user_id, subject=row["subject"],
            relation=relation, object=obj,
            original_relation=(row["original"] if relation != row["original"]
                               else None),
            note=note_str, volatility=vol,
            ungrounded=flagged, agreement=agr,
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
    # specs/0039 §2b/§2c: the two COUNTED kinds, one record per call each, only when
    # non-zero; the counters never reach the result (0025 X12 keeps the set closed)
    if n_volatility_defaulted:
        _emit_degrade(on_degrade, "volatility_defaulted", {"count": n_volatility_defaulted})
    if n_members_skipped:
        _emit_degrade(on_degrade, "member_skipped", {"count": n_members_skipped})
    result = {"episode": episode_text, "facts": n_facts, "quarantined": n_quarantined,
            "supersessions": n_supersessions, "reinforcements": n_reinforcements,
            # specs/0025 §4c — THE counter inventory, present on every path;
            # `redispositioned` is 0024's counter (U7): live on this path,
            # 0 on the unparseable path — an absent key is not a zero.
            "invalid": n_invalid, "retried": n_retried,
            "recovered": n_recovered, "residual": n_residual,
            "redispositioned": n_redispositioned,
            # specs/0038 §2b: REFUSALS of triples that restate a declared
            # instruction — never declarations, never malformed members.
            "instructions_dropped": n_instructions_dropped,
            # specs/0025 (amended 2026-09-08): triples whose SUBJECT is off the
            # closed grammar — dropped, never written under any subject.
            "subject_refused": n_subject_refused,
            # specs/0023 Q4 (RESOLVED 2026-08-22, per the recorded leaning):
            # the quarantine-at-birth AUDIT facts — the content-free identity
            # digest answers "which source is still writing" from the audit
            # sink alone. ALWAYS present (an absent key is not a zero); the
            # audit sink is the consumer, telemetry's whitelist drops them,
            # the MCP surface strips them.
            "quarantined_at_birth": (n_quarantined if revoked_at_birth else 0),
            "birth_revocation_digest": (_birth_digest if revoked_at_birth
                                        else None),
            # specs/0026 §3d — present on EVERY path (an absent key is
            # not a zero); the MCP surface strips them with the other
            # operator counters; telemetry consumption DEFERRED (R1-3)
            "agreement_floored": n_agreement_floored,
            "agreement_recorded": n_agreement_recorded}
    # specs/0025 §4c as amended: the key is ADDED, never a new one — `unparseable`
    # already rides the no-JSON path with this exact meaning ("the extraction yielded
    # no usable `triples`"), so the pinned key set of a SUCCESSFUL ingest (X12) is
    # untouched and no host learns a new name. It appears only on the paths that
    # produced nothing usable, exactly as it does on the no-JSON path today.
    if primary_unusable:
        result["unparseable"] = True
    return result
