"""specs/0037 — PROCEDURAL records: the host-declared content kind with a
host-declared BASIS (`stated` / `observed`), never asserted as fact, never
rendered into model context, describable through one dedicated surface.

Two things live here. `build_procedure_edge` is the validation and
construction behind `Memory.record_procedure` — the SOLE producer of a
procedural record (§4a F1/F3): every argument refuses its empty and
malformed forms BEFORE anything is written (§2c, V-ARGS-VALIDATED), the
relation must be registered `procedural` in the ACTIVE registry
(V-RELATION-VALID), the context must carry a basis (V-BASIS-POSITIVE), and
the record is stamped `record_kind="procedural"` from the registry's
declaration AT WRITE (V-KIND-STAMPED). `describe_procedures` is the
stage-3 read surface (§4a-ii): one result per VISIBLE candidate — the
edges that are procedural BY THEIR OWN RECORD (`record_kind == "procedural"
OR basis is not None`, never the registry) — each described or withheld
under the FIRST failing conjunct of the ordered predicate, never both and
never neither; the `note` is rendered in NO field; a summary matching the
frozen recognition rule is withheld as `executable_detail`
(V-NO-IMPLICIT-RECOMMEND); `withheld` is query-blind (V-WITHHELD-QUERY-
BLIND); a hidden record is in neither list (V-SCOPE-OUTERMOST).

FAILURE TAXONOMY (§4, stated once): WRITE-path failures RAISE and write
nothing — `TypeError` for a wrong type, `ValueError` for a wrong value, each
carrying `.reason`, the named refusal (e.g. `relation_not_procedural`).
READ-path outcomes are RETURNED and NAMED, never raised; the only read-path
exceptions are the existing ones (`ScopeError` for a principal without a
policy) and the caller errors on `limit`/`query` (§4a-ii).
"""
from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .schema import (Disclosure, Edge, EvidenceAuthor, EvidenceContext, Provenance,
                     is_procedural, is_procedural_relation, utcnow)

# ----------------------------------------------------------------- refusals
class ProcedureValueError(ValueError):
    """A wrong VALUE on the write path, carrying the named reason."""

    def __init__(self, reason: str, message: str):
        self.reason = reason
        super().__init__(f"{message} [{reason}]")


class ProcedureTypeError(TypeError):
    """A wrong TYPE on the write path, carrying the named reason."""

    def __init__(self, reason: str, message: str):
        self.reason = reason
        super().__init__(f"{message} [{reason}]")


#: §4b — a `when` beyond this skew refuses as ingest does (`ingest.MAX_FUTURE_SKEW`)
MAX_FUTURE_SKEW_DAYS = 1
#: §2c — the summary bound: ingest's object bound (`Edge.object` is one gloss-level line)
MAX_SUMMARY_CHARS = 512


def _norm_ws(text: str) -> str:
    return " ".join(text.split())


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ------------------------------------------------------ the write surface
def build_procedure_edge(store, relations, user_id: str, summary: str, *, author,
                         context, relation: str = "follows_procedure",
                         note: Optional[str] = None, when=None,
                         evidence_ref: Optional[str] = None,
                         source_id: Optional[str] = None,
                         require_source_id: bool = False):
    """Validate every argument (§2c) and construct the procedural Edge §4b
    specifies — RETURNS (edge, quarantined_at_birth, birth_digest); writes
    nothing (the caller persists). Every refusal raises BEFORE construction,
    so the store is byte-identical after any refusal (V-ARGS-VALIDATED)."""
    from .ingest import _disclosure_for
    # -- user_id / summary
    if not isinstance(user_id, str) or not user_id:
        raise ProcedureTypeError("user_id_invalid", "user_id must be a non-empty str")
    if isinstance(summary, bool) or not isinstance(summary, str):
        raise ProcedureTypeError("summary_not_str",
                                 f"summary must be a str, got {type(summary).__name__}")
    summary_n = _norm_ws(summary)
    if not summary_n:
        raise ProcedureValueError("summary_empty", "summary is empty or whitespace-only")
    if len(summary_n) > MAX_SUMMARY_CHARS:
        raise ProcedureValueError(
            "summary_too_long",
            f"summary is {len(summary_n)} chars; the bound is {MAX_SUMMARY_CHARS}")
    # -- the optional strings: "" is treated as None
    def _opt(name, v):
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, str):
            raise ProcedureTypeError(f"{name}_not_str",
                                     f"{name} must be a str or None, got {type(v).__name__}")
        return v if v.strip() else None
    note = _opt("note", note)
    evidence_ref = _opt("evidence_ref", evidence_ref)
    source_id = _opt("source_id", source_id)
    # -- author: the AUTHORSHIP axis exactly as `remember` takes it
    if not isinstance(author, EvidenceAuthor):
        raise ProcedureTypeError("author_not_evidence_author",
                                 f"author must be an EvidenceAuthor member, got "
                                 f"{type(author).__name__} {author!r}")
    # -- context: the DERIVATION axis and the BASIS (required)
    if type(context) is not EvidenceContext:
        raise ProcedureTypeError(
            "context_not_evidence_context",
            "context must be an EvidenceContext minted via EvidenceContext.direct(basis=) "
            f"or EvidenceContext.derived(X, basis=); got {type(context).__name__}")
    if context.basis is None:
        raise ProcedureValueError(
            "basis_required",
            "a procedural event requires a declared basis on its context — "
            "EvidenceContext.direct(basis=\"stated\"|\"observed\") or derived(X, basis=…) "
            "(specs/0037 §4b, V-BASIS-POSITIVE; absence is not a missing argument)")
    # -- when: an AWARE datetime, not beyond the skew; a str or a naive value
    #    is refused HERE (the surface's own gate — `as_utc_required` would
    #    parse ISO text and take a naive value as UTC)
    if when is not None:
        if isinstance(when, bool) or not isinstance(when, datetime):
            if isinstance(when, str):
                raise ProcedureValueError("when_not_datetime",
                                          "when must be an aware datetime, not a str")
            raise ProcedureTypeError("when_not_datetime",
                                     f"when must be an aware datetime, got {type(when).__name__}")
        if when.tzinfo is None or when.tzinfo.utcoffset(when) is None:
            raise ProcedureValueError("when_naive", "when must be timezone-aware")
        when = when.astimezone(timezone.utc)
        from datetime import timedelta
        if when > utcnow() + timedelta(days=MAX_FUTURE_SKEW_DAYS):
            raise ProcedureValueError("when_beyond_skew",
                                      f"when is more than {MAX_FUTURE_SKEW_DAYS} day(s) in the future")
    # -- relation: registered AND procedural in the ACTIVE registry (V-RELATION-VALID)
    if isinstance(relation, bool) or not isinstance(relation, str):
        raise ProcedureTypeError("relation_not_str",
                                 f"relation must be a str, got {type(relation).__name__}")
    if not is_procedural_relation(relations, relation):
        raise ProcedureValueError(
            "relation_not_procedural",
            f"relation {relation!r} is not registered as procedural in the active registry "
            "(specs/0037 §4b, V-RELATION-VALID) — nothing written")
    # -- specs/0006 §4 rule 9 (v9, 2026-09-12): the requirement reaches THIS
    #    producer too — a third-party-AUTHORED or declared third-party-DERIVED
    #    procedure with no source_id has no source identity and no revocation
    #    can reach it; refused before any write when the host's config says so
    #    (the context is always explicit here, so its derivation IS a declaration)
    if require_source_id and source_id is None and (
            author == EvidenceAuthor.THIRD_PARTY
            or context.derived_from == EvidenceAuthor.THIRD_PARTY):
        from .ingest import SourceIdRequired
        raise SourceIdRequired(
            "source_id is required for a third-party-authored or third-party-derived procedure "
            "when MemoryConfig.require_source_id is on (specs/0006 §4 rule 9, v9): a record "
            "without one has no source identity and cannot be revoked by source; nothing was written")
    # -- construction (§4b): id minted like remember's, subject "user"
    edge_id = _uid("e")
    valid_from = when or utcnow()
    # disclosure is DERIVED, never host-supplied: 0023's quarantine-at-birth
    # first (a standing-revoked source at write lands QUARANTINED whatever the
    # author — V-BIRTH-QUARANTINE-HOLDS), then the shipped three-axis rule
    from .scope_linkage import identity_digest_of
    birth_digest = (identity_digest_of(None, source_id, store.local_origin())
                    if source_id is not None and hasattr(store, "local_origin") else None)
    revoked_at_birth = (birth_digest is not None
                        and birth_digest in store.standing_revocations(user_id))
    disclosure = (Disclosure.QUARANTINED if revoked_at_birth
                  else _disclosure_for(author, relation, context.derived_from))
    edge = Edge(
        id=edge_id, user_id=user_id, subject="user", relation=relation,
        object=summary_n, note=note or "", valid_from=valid_from,
        provenance=Provenance(
            author_of_evidence=author, derived_from=context.derived_from,
            basis=context.basis, record_kind="procedural",
            evidence_ref=evidence_ref or f"procedure:{edge_id}",
            observed_at=valid_from, source_id=source_id, disclosure=disclosure))
    return edge, revoked_at_birth, birth_digest


# ----------------------------------------------------- the recognition rule
#: The imperative-opener LEXICON the product carries (the wheel ships no test
#: corpus). The frozen texts (`tests/eval/procedural_describe/FROZEN_TEXTS.json`,
#: research, 2026-09-08) are the oracle: the test DERIVES the opener and
#: step-marker sets from them and asserts this rule fires on every must-match
#: text and on none of the paraphrased, plain, or must-not-match-named texts.
#: Clause-initial NOUN/VERB HOMOGRAPHS research measured (`archive`, `email`,
#: `store`) are deliberately ABSENT; the copula guard below is the second
#: defence. A hand list, kept honest by that derivation, never by itself.
IMPERATIVE_OPENERS = frozenset("""
add adjust allow always apply ask assign avoid back backfill build bump cancel clean
clear close compile configure confirm cordon create deactivate delete deny deploy
disable do document drain enable ensure escalate fetch fix flush freeze generate ignore
install keep kill migrate move never notify open pause put quarantine re-run rebase
reboot rebuild redeploy refresh reinstall reject reload remove rename replace reproduce
restart restore retry revert review revoke roll rollback rotate run submit tag take
throttle toggle turn unfreeze uninstall unlock unpin unset update upgrade validate
verify widen
""".split())
#: opener-shaped words that are at least as often NOUNS at the head of a
#: host-authored summary ("Pull requests target main.", "Log retention is
#: 30 days.", "Archive access is granted…") — deliberately outside the lexicon;
#: the rule can only refuse, so the omission costs a missed imperative, never a
#: withheld declarative (the failure direction §7 chooses)
NOUN_HOMOGRAPHS_EXCLUDED = frozenset("""
alert archive block call check commit copy drop email export fail file format grant
hold issue launch lock log merge monitor page pin ping pull push queue record release
reset return save scale schedule set ship snapshot start stop store test track use
wait wipe write
""".split())
assert not (IMPERATIVE_OPENERS & NOUN_HOMOGRAPHS_EXCLUDED)

#: introductory subordinators: "Before running a deploy, disable the audit log."
SUBORDINATORS = frozenset("after before during if once until when whenever while".split())
#: step markers: "Step 1:", "1.", "1)", "First,", "Then,", "Next,", "Finally,"
_STEP_MARKER = re.compile(
    r"^\s*(?:step\s*\d+\s*[:.\-—–)]|\d+\s*[.)]\s|(?:first|second|third|then|next|"
    r"lastly|finally|afterwards)\s*[,:]\s)", re.I)
_COPULA = re.compile(r"\b(?:is|are|was|were|has been|have been|gets|get)\b", re.I)
_TOKEN = re.compile(r"[a-z0-9][a-z0-9'-]*")


def _first_clause_and_rest(text: str):
    parts = re.split(r"[,;:.]\s+", text.strip(), maxsplit=1)
    return parts[0], (parts[1] if len(parts) > 1 else "")


def _imperative_clause(clause: str) -> bool:
    toks = _TOKEN.findall(clause.lower())
    if not toks:
        return False
    head = toks[0]
    if head not in IMPERATIVE_OPENERS:
        return False
    # interrogatives ("Do you have any tips…?") and copular clauses ("Archive
    # access is granted…", "Store the codes … is what the team does") are
    # not imperatives even when they open on an imperative-shaped word
    if len(toks) > 1 and toks[1] in ("you", "we", "they", "i"):
        return False
    if _COPULA.search(clause):
        return False
    return True


def matches_executable_detail(summary: str) -> bool:
    """THE FROZEN RECOGNITION RULE (§6a), exact-form: fires on a step-marked
    text or on an imperative first clause (the first clause, or the clause
    after an introductory subordinate one). A paraphrase in non-imperative
    mood PASSES — the stated v1 boundary (§8), a limit and not a guarantee.
    It can only REFUSE (withhold as `executable_detail`); it is a floor."""
    text = _norm_ws(summary or "")
    if not text or text.endswith("?"):
        return False
    if _STEP_MARKER.match(text):
        return True
    first, rest = _first_clause_and_rest(text)
    toks = _TOKEN.findall(first.lower())
    if toks and toks[0] in SUBORDINATORS and rest:
        head_clause, _ = _first_clause_and_rest(rest)
        return _imperative_clause(head_clause)
    return _imperative_clause(first)


# ------------------------------------------------------- the read surface
WITHHELD_OUTCOMES = ("kind_conflict", "relation_unregistered", "inactive", "not_yet_valid",
                     "quarantined", "use_only", "basis_unknown", "executable_detail")


@dataclass(frozen=True)
class ProcedureDescription:
    """§4a-ii — NO raw stored text in any field but `summary` (the record's
    `object`, the host's gloss-level name of the procedure); the `note` is
    never rendered."""
    edge_id: str
    relation: str
    gloss: str
    summary: str
    basis: str
    attribution: str
    author: str
    observed_at: datetime
    valid_from: datetime
    disclosure: str = "mentionable"


@dataclass(frozen=True)
class Withheld:
    edge_id: str
    outcome: str


@dataclass(frozen=True)
class DescribeResult:
    descriptions: list = field(default_factory=list)
    total_describable: int = 0
    withheld: list = field(default_factory=list)
    truncated: bool = False
    query: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "descriptions": [
                {**asdict(d), "observed_at": d.observed_at.isoformat(),
                 "valid_from": d.valid_from.isoformat()} for d in self.descriptions],
            "total_describable": self.total_describable,
            "withheld": [asdict(w) for w in self.withheld],
            "truncated": self.truncated, "query": self.query,
        }


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _attribution(basis: str, summary: str) -> str:
    return (f"you said you follow {summary}" if basis == "stated"
            else f"a pattern you reported observing: {summary}")


def describe_outcome(edge, relations) -> Optional[str]:
    """§4a-ii's ORDERED predicate over one candidate: the first failing
    conjunct's named outcome, or None when every conjunct holds (described).
    Total: no default allow, no untyped outcome."""
    p = edge.provenance
    if p.record_kind != "procedural":            # 1. stamp consistent (None ∧ basis)
        return "kind_conflict"
    if edge.relation not in relations:           # 2. relation registered
        return "relation_unregistered"
    if not edge.active:                          # 3. active
        return "inactive"
    if not edge.valid_now:                       # 4. valid_now
        return "not_yet_valid"
    if edge.quarantined:                         # 5. not quarantined
        return "quarantined"
    if edge.use_only:                            # 6. not use_only
        return "use_only"
    if p.basis not in ("stated", "observed"):    # 7. basis in the closed domain
        return "basis_unknown"
    if matches_executable_detail(edge.object):   # 8. the frozen rule
        return "executable_detail"
    return None


def describe_procedures(store, relations, user_id: str, *, query=None, view=None,
                        limit: int) -> tuple:
    """The surface behind `Memory.describe_procedures` (arguments already
    validated). RETURNS (DescribeResult, kind_conflicts) — the count of
    `kind_conflict` candidates is carried to the caller's telemetry (§4a:
    counted, never a silent inference)."""
    q = _tokens(query) if query else set()
    rows = store.edges(user_id, active_only=False, include_quarantined=True)
    candidates = []
    for e in rows:
        if not is_procedural(e):                 # the candidate set, by the STAMP/BASIS
            continue
        if view is not None:
            if not view.visible(e):              # §3: visibility is OUTERMOST — neither list
                continue
            e = view.shape(e)                    # cross-scope-visible → use_only (0020)
        candidates.append(e)
    described, withheld, conflicts = [], [], 0
    for e in candidates:
        outcome = describe_outcome(e, relations)
        if outcome is None:
            described.append(e)
        else:
            withheld.append(Withheld(edge_id=e.id, outcome=outcome))
            if outcome == "kind_conflict":
                conflicts += 1
    # ordering (§4a-ii): relevance desc, valid_from desc, edge_id asc; the
    # note is NOT scored; withheld is query-blind — valid_from desc, edge_id asc
    def _rel(e) -> int:
        return len(q & _tokens(f"{e.subject} {e.relation} {e.object}")) if q else 0
    by_id = {e.id: e for e in candidates}
    described.sort(key=lambda e: (-_rel(e), -e.valid_from.timestamp(), e.id))
    withheld.sort(key=lambda w: (-by_id[w.edge_id].valid_from.timestamp(), w.edge_id))
    total = len(described)
    cut = described[:limit]
    descriptions = [
        ProcedureDescription(
            edge_id=e.id, relation=e.relation, gloss=relations[e.relation].desc,
            summary=e.object, basis=e.provenance.basis,
            attribution=_attribution(e.provenance.basis, e.object),
            author=e.provenance.author_of_evidence.value,
            observed_at=e.provenance.observed_at, valid_from=e.valid_from)
        for e in cut]
    return (DescribeResult(descriptions=descriptions, total_describable=total,
                           withheld=withheld, truncated=len(cut) < total, query=query),
            conflicts)
