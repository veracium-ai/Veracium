"""Seam model — the 0030 RAW ADAPTER, executable.

Round-3 F3 asked for a construction rather than a description, because the
description was wrong in a way only running it shows: `quarantined` and
`use_only` are `@property` on `Edge` and are NOT serialized, so round-2's rule
"a missing flag must never default -- missing => MALFORMED" would have refused
EVERY payload at implementation.

RULE ZERO (this model's, agreed both seats): every assertion here ships with a
NEGATIVE CONTROL that makes it fail, in this same file. A check that cannot
fail is worse than no check -- it manufactures confidence. Each `control_*`
function below demonstrates the corresponding assertion is capable of failing.
"""
from __future__ import annotations

import json
import typing as _typing
from dataclasses import dataclass
from typing import Any, Optional

from veracium.scope import IDENTITY_MAX
from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance,
                             QUARANTINE_RELATION)

#: exactly the keys the adapter requires. Verified by EXECUTION against
#: `Edge.model_dump_json` -- not recalled, and notably WITHOUT `quarantined`
#: or `use_only`, which no payload carries.
REQUIRED_KEYS = frozenset({
    "id", "user_id", "subject", "relation", "object", "note",
    "provenance", "valid_from", "invalidated_at", "invalidation_reason",
})

#: the provenance keys the REAL `ScopeView` consumes. Read from
#: `MembershipResolver._record_shape` (scope_read.py:170-176), not from the
#: verdict's summary: author_of_evidence.value, origin, source_id,
#: evidence_ref -- plus `record.id` and an OPTIONAL `lineage` (`Edge` has no
#: such field, so `getattr(record, "lineage", None)` is always None for edges).
#: Presence is required even where the VALUE may be None: dev's 0029 v9 finding
#: established by execution that `model_dump_json` SERIALIZES Nones rather than
#: omitting them, so a real payload always carries these keys.
SCOPE_PROVENANCE_KEYS = frozenset({
    "author_of_evidence", "origin", "source_id", "evidence_ref", "disclosure",
})


def _strict_pairs(pairs):
    """Reject DUPLICATE KEYS at the evidence boundary.

    Plain `json.loads` is last-wins on duplicates, and for THIS adapter that is
    a trust bypass rather than a curiosity. EXECUTED against the shipped model:
    a payload carrying `"disclosure":"quarantined","disclosure":"mentionable"`
    parses to MENTIONABLE, so a QUARANTINED third-party claim reads as
    MENTIONABLE and the adapter declassifies it. The adapter is precisely an
    evidence boundary -- untrusted text becoming a trust decision -- which is
    why 0026's shipped gate refuses plain loads here, and why an allowlist
    entry would have been the wrong disposition when the strict decoder is one
    hook away. The hook runs PER OBJECT, so the nested `provenance` dict is
    covered without a second mechanism.
    """
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate key: {k!r}")
        d[k] = v
    return d


@dataclass(frozen=True)
class AdaptedProvenance:
    """Exactly what `ScopeView` reads. `author_of_evidence` is the REAL
    `EvidenceAuthor` enum because `_record_shape` accesses `.value` on it --
    a plain string would raise there, which is the sort of thing only running
    it against the real ScopeView reveals."""
    author_of_evidence: EvidenceAuthor
    origin: Optional[str]
    source_id: Optional[str]
    evidence_ref: str
    disclosure: str


@dataclass(frozen=True)
class Adapted:
    """A payload validated and with its trust flags DERIVED.

    Shaped to be consumable by the REAL `ScopeView`: it exposes `id` and a
    `provenance` object, and carries no `lineage` (edges have none).
    """
    provenance: AdaptedProvenance
    id: str
    user_id: str
    subject: str
    relation: str
    object: str
    note: str
    valid_from: Any
    invalidated_at: Any
    invalidation_reason: Optional[str]
    disclosure: str
    quarantined: bool          # DERIVED -- never read from the payload
    use_only: bool             # DERIVED -- never read from the payload


def derive_quarantined(relation: str, disclosure: str) -> bool:
    """schema.py:482, read directly rather than recalled.

    TWO DISJUNCTS. A one-disjunct derivation (disclosure alone) lets a
    third-party CLAIM through whenever its own disclosure is not itself
    QUARANTINED -- see `control_one_disjunct_lets_a_claim_through`.
    """
    return (relation == QUARANTINE_RELATION
            or disclosure == Disclosure.QUARANTINED.value)


def derive_use_only(disclosure: str) -> bool:
    """schema.py:491 -- one disjunct, deliberately unlike `quarantined`."""
    return disclosure == Disclosure.USE_ONLY.value


# --------------------------------------------------------------------------
# THE CONTRACT IS DERIVED FROM THE SHIPPED MODEL, NEVER RESTATED (round-5 F4)
# --------------------------------------------------------------------------
# Round-5 found the adapter STRICTER than production: it demanded non-empty
# strings for `id`, `user_id`, `subject`, `relation`, `object` and
# `evidence_ref`, all of which the shipped model declares as plain `str` with
# NO minimum length. So it would have refused SIX classes of legitimate record.
# The reviewer probed ONE field and the class was six.
#
# Adding six allowances would leave the seventh field wrong the same way.
# RESTATED CONTRACTS DRIFT IN BOTH DIRECTIONS -- too permissive was rounds 1-4,
# too strict was round 5 -- so the cure for both is to stop restating. These
# rules are introspected from `Edge`/`Provenance` themselves: annotation for the
# type, `metadata` for MinLen/MaxLen, and the annotation again for None-accept.
# Only `source_id`/`origin` carry 1..512, which is where the intuition belonged.
#
# ROUND-6 F4, RETRACTION: this comment used to claim `is_required()` supplied
# presence. It never did -- the code has never called it -- and it is also the
# WRONG TOOL: `is_required()` reports whether a field has a DEFAULT, while the
# question here is whether the model accepts None. Two different properties, and
# a field can differ on them. The claim is withdrawn rather than implemented.
#
# WHICH DERIVATION, settled by execution over the fields ACTUALLY CHECKED.
# `_check_derived` runs on twelve fields only (nine on `Edge`, three on
# `Provenance` -- see the call sites). Over those twelve, `type(None) in
# get_args(ann)` and sniffing `str(ann)` AGREE, in both a cold model and a warm
# one. So the presence rule below uses BOTH: `get_args` is the principled form
# and handles PEP-604 `X | None`; the string test survives an UNRESOLVED
# `ForwardRef`, where `get_args` returns `()`. Neither alone is correct in every
# state and together they are, so the disjunction is the derivation, not a hedge.
#
# A CORRECTION THIS AUTHOR OWES, because the reasoning nearly shipped: the first
# version of this note argued the string test must STAY because `get_args`
# breaks `Edge.last_outcome`, an unresolved `ForwardRef('Optional[Outcome]')`.
# Both halves were wrong. `last_outcome` is NOT among the twelve fields
# `_check_derived` ever sees, so it could not have broken anything; and the
# ForwardRef RESOLVES the moment any `Edge` is instantiated, so the cold state
# it was measured in does not occur in a real run. A narrow executed fact
# (`get_args` returns `()` on an unresolved ForwardRef -- true) was generalised
# into a claim about the adapter -- the scope-widening shape again, caught here
# only because the control built to defend it answered differently depending on
# whether anything had constructed an `Edge` first. A control whose value moves
# with import order is not a control; that is what exposed it.

# NOTE the deliberate asymmetry with the CONSUMER side: this half derives what
# production EMITS; the campaign asserts we refuse what ScopeView RAISES on.
# Both halves are needed and neither implies the other.


def _field_rule(model, name):
    """`(is_optional, min_len, max_len)` from the shipped field.

    ROUND-6: this docstring said `(is_optional, is_str_like, min_len, max_len)`
    -- four elements for a three-element return, an is_str_like that does not
    exist. A wrong signature in a docstring is the same defect class as the
    `is_required()` claim above, one scale smaller.
    """
    f = model.model_fields[name]
    ann = f.annotation
    optional = (type(None) in _typing.get_args(ann)
                or "Optional" in str(ann) or "NoneType" in str(ann))
    mn = mx = None
    for m in f.metadata:
        mn = getattr(m, "min_length", mn)
        mx = getattr(m, "max_length", mx)
    return optional, mn, mx


def _check_derived(model, name, value) -> bool:
    """Validate ONE raw (JSON-decoded) value against the model's own rule.

    Datetimes arrive as TEXT here -- the payload is JSON and the classifier
    normalises later -- so a datetime-annotated field is checked as a string,
    not as a `datetime`. That is a property of the carrier being raw, and it is
    why this cannot simply call the model's validator.
    """
    optional, mn, mx = _field_rule(model, name)
    if value is None:
        return optional
    if not isinstance(value, str):
        return False
    if mn is not None and len(value) < mn:
        return False
    if mx is not None and len(value) > mx:
        return False
    return True


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and v != ""


def _identity_field(v) -> bool:
    """`origin`/`source_id`: None, or a 1..IDENTITY_MAX-char string.

    The bound is SHIPPED, not invented: `IDENTITY_MAX = 512` (scope.py:96) and
    `Provenance.source_id/origin: Optional[str], min_length=1, max_length=512`
    (schema.py:134-135). Round-4 F2: the reviewer fed `source_id=[]`, the
    PRESENCE-only schema check accepted it, and the real `ScopeView` raised
    `ScopeError: identity field must be a 1..512-char string or None`.
    THE ADAPTER MUST NOT PASS ANYTHING ITS CONSUMER WILL RAISE ON -- a
    presence check asks whether a key exists and never what it holds.
    """
    return v is None or (isinstance(v, str) and 1 <= len(v) <= IDENTITY_MAX)


def _optional_str(v) -> bool:
    return v is None or isinstance(v, str)


def adapt(state_text: str, *, expect_id: str, expect_user: str) -> Optional[Adapted]:
    """TEXT -> Adapted, or None. `None` is the single failure value; the caller
    maps it to MALFORMED, or to SCOPE_HIDDEN on the current leg before
    visibility is established (V-FAILHIDDEN)."""
    # 1. PARSE (C-1: the consumer's step)
    try:
        m = json.loads(state_text, object_pairs_hook=_strict_pairs)
    except (ValueError, TypeError):
        return None
    if not isinstance(m, dict):
        return None
    # 2. IDENTITY against the ROW-sourced values (C-4)
    if m.get("id") != expect_id or m.get("user_id") != expect_user:
        return None
    # 3. SCHEMA -- missing is never defaulted
    if not REQUIRED_KEYS.issubset(m):
        return None
    # 3b. TYPES AND BOUNDS, per field (round-4 F2). Presence is not validity.
    if not all(_check_derived(Edge, k, m[k]) for k in
               ("id", "user_id", "subject", "relation", "object", "note",
                "valid_from", "invalidated_at", "invalidation_reason")):
        return None
    # 4. ENUMS: reason TYPE is required (an unknown STRING is coherent and
    #    fences later, F8b); disclosure must be a real member.
    r = m["invalidation_reason"]
    if r is not None and not isinstance(r, str):
        return None
    prov = m.get("provenance")
    if not isinstance(prov, dict):
        return None
    # INCOMPLETE PROVENANCE is a real shape, and it is not merely a schema
    # nicety: these fields FEED THE SCOPE DECISION. Defaulting a missing
    # `author_of_evidence` would have ScopeView classify on a FABRICATED
    # author -- see `control_defaulting_author_fabricates_a_scope_decision`.
    if not SCOPE_PROVENANCE_KEYS.issubset(prov):
        return None
    disc = prov["disclosure"]
    # TYPE BEFORE MEMBERSHIP. Round-4 F2's campaign found this: an unhashable
    # `disclosure` (list/dict) RAISED `TypeError: unhashable type` at the `in`
    # test instead of refusing. That is 0030's OWN V-NORMALIZE rule -- "a
    # non-string (incl. unhashable) value must never reach `in`/`dict.get`" --
    # which this author wrote for the classifier's `invalidation_reason` and
    # then violated here. A spec rule is not confined to the field that
    # motivated it.
    if not isinstance(disc, str) or disc not in {d.value for d in Disclosure}:
        return None
    if not isinstance(prov["author_of_evidence"], str):
        return None                       # type before construction, as above
    try:
        author = EvidenceAuthor(prov["author_of_evidence"])
    except ValueError:
        return None                       # unknown author is not defaulted
    if not all(_check_derived(Provenance, k, prov[k]) for k in
               ("evidence_ref", "origin", "source_id")):
        return None                       # derived: 1..512 on the identity
                                          # fields, plain str on evidence_ref
    # 5. DERIVE the flags
    return Adapted(
        provenance=AdaptedProvenance(
            author_of_evidence=author, origin=prov["origin"],
            source_id=prov["source_id"], evidence_ref=prov["evidence_ref"],
            disclosure=disc),
        id=m["id"], user_id=m["user_id"], subject=m["subject"],
        relation=m["relation"], object=m["object"], note=m["note"] or "",
        valid_from=m["valid_from"], invalidated_at=m["invalidated_at"],
        invalidation_reason=r, disclosure=disc,
        quarantined=derive_quarantined(m["relation"], disc),
        use_only=derive_use_only(disc),
    )


# --------------------------------------------------------------------------
# NEGATIVE CONTROLS -- each proves the assertion above CAN fail.
# --------------------------------------------------------------------------

def control_flags_are_not_serialized(payload: dict) -> bool:
    """The F3 control: reading the flags AS FIELDS finds nothing.

    True means "a field-reading adapter would have refused this payload",
    which is what makes the DERIVATION necessary rather than stylistic.
    """
    return "quarantined" not in payload and "use_only" not in payload


def control_one_disjunct_lets_a_claim_through() -> bool:
    """THE control this model exists for.

    A third-party CLAIM (`relation == third_party_claim`) whose disclosure is
    NOT itself QUARANTINED is quarantined by the real two-disjunct rule and
    NOT by the one-disjunct mistake. True means the shortcut is unsafe.
    """
    relation, disclosure = QUARANTINE_RELATION, Disclosure.MENTIONABLE.value
    real = derive_quarantined(relation, disclosure)          # True
    one_disjunct = (disclosure == Disclosure.QUARANTINED.value)  # False
    return real and not one_disjunct


def control_defaulting_a_missing_field_would_grant(state_text: str) -> bool:
    """A payload with no `disclosure` must REFUSE, not default.

    True means: the adapter refused, AND a defaulting variant would have
    produced use_only=False -- i.e. defaulting GRANTS.
    """
    refused = adapt(state_text, expect_id="e1", expect_user="u") is None
    m = json.loads(state_text, object_pairs_hook=_strict_pairs)
    defaulted_use_only = derive_use_only(m.get("provenance", {}).get("disclosure", ""))
    return refused and defaulted_use_only is False


def control_defaulting_author_fabricates_a_scope_decision(state_text: str,
                                                          view) -> bool:
    """A payload whose provenance lacks `author_of_evidence` must REFUSE.

    True means: the adapter refused, AND a DEFAULTING variant produces a
    record the real `ScopeView` happily classifies -- i.e. the default does
    not fail loudly, it silently manufactures a scope decision from a field
    that was never there. That is why incomplete provenance is a refusal and
    not a tolerance.
    """
    refused = adapt(state_text, expect_id="e1", expect_user="u") is None
    m = json.loads(state_text, object_pairs_hook=_strict_pairs)
    prov = m["provenance"]
    fabricated = Adapted(
        provenance=AdaptedProvenance(
            author_of_evidence=EvidenceAuthor.USER,      # THE FABRICATION
            origin=prov.get("origin"), source_id=prov.get("source_id"),
            evidence_ref=prov.get("evidence_ref") or "x",
            disclosure=prov.get("disclosure", Disclosure.MENTIONABLE.value)),
        id=m["id"], user_id=m["user_id"], subject=m["subject"],
        relation=m["relation"], object=m["object"], note=m["note"] or "",
        valid_from=m["valid_from"], invalidated_at=m["invalidated_at"],
        invalidation_reason=m["invalidation_reason"], disclosure="mentionable",
        quarantined=False, use_only=False)
    classified = view.decision(fabricated) is not None
    return refused and classified


def craft_duplicate_key_payload(honest_text: str) -> str:
    """Build the duplicate-key attack: TWO `disclosure` keys, quarantined then
    mentionable. Returns the honest text unchanged if the fixture was not what
    we assumed, which the driver asserts against so the control cannot go
    vacuous by fixture drift."""
    return honest_text.replace('"disclosure":"quarantined"',
                               '"disclosure":"quarantined","disclosure":"mentionable"')


def strict_refuses_duplicate_keys(attack_text: str) -> bool:
    """Half the control that can live in the evidence tree: the strict decoder
    REFUSES the crafted payload.

    The OTHER half -- demonstrating that plain last-wins parsing declassifies
    it -- necessarily performs a plain parse, which 0026's gate forbids HERE
    and permits in `tests/`. So the control is split across that boundary
    rather than allowlisted: the control proving a gate necessary would
    otherwise have to violate the gate. See the driver's
    `test_duplicate_key_would_flip_trust_under_plain_loads`.
    """
    return adapt(attack_text, expect_id="e1", expect_user="u") is None


def control_presence_derivation_agrees() -> bool:
    """ROUND-6 F4: the two presence derivations must agree on the fields
    `_check_derived` ACTUALLY sees -- in BOTH a cold and a warm model.

    The first version of this control compared ALL model fields and asserted
    the sole disagreement was `Edge.last_outcome`. It was measuring a field the
    adapter never checks, in a cold state that no real run is in, and its answer
    FLIPPED depending on whether anything had constructed an `Edge` first. This
    version is state-independent by construction: it warms the model itself and
    asserts agreement before and after.

    True means the disjunction in `_field_rule` is belt-and-braces rather than
    load-bearing on either half. If a future field is added whose annotation
    form breaks one derivation, this FAILS and names it -- which is the whole
    point, and is what the previous version could not do.
    """
    checked = ((Edge, ("id", "user_id", "subject", "relation", "object", "note",
                       "valid_from", "invalidated_at", "invalidation_reason")),
               (Provenance, ("evidence_ref", "origin", "source_id")))

    def disagreements():
        out = []
        for model, names in checked:
            for n in names:
                ann = model.model_fields[n].annotation
                sniff = ("Optional" in str(ann)) or ("NoneType" in str(ann))
                args = type(None) in _typing.get_args(ann)
                if sniff != args:
                    out.append((model.__name__, n))
        return out

    cold = disagreements()
    Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="e",
               disclosure=Disclosure.MENTIONABLE)          # warms both models
    warm = disagreements()
    return cold == [] and warm == []
