"""specs/0030 §4a-iii — the RAW ADAPTER: journal/row TEXT → a validated,
flag-DERIVED record the classifier and the real `ScopeView` can consume, or
None. Lifted from the seam model's `raw_adapter.py` (round-3 F3's executable
construction; round-4 F2's type-and-bounds campaign; round-5 F4's rule that
the CONTRACT IS DERIVED FROM THE SHIPPED MODEL, never restated). The model's
negative controls live on as tests.

Why an adapter and not `Edge.model_validate_json`: `quarantined`/`use_only`
are @property on `Edge` and are NOT serialized (F3) — a payload never carries
them, so they are DERIVED here from relation + disclosure by the shipped
two-disjunct rule; and the shipped deserializer REJECTS malformed reasons and
timestamps before any classifier could run, while 0030 must CLASSIFY them
(V-RAW). `None` is the single failure value: the caller maps it to MALFORMED,
or to SCOPE_HIDDEN on the current leg under a view (V-FAILHIDDEN).
"""
from __future__ import annotations

import json
import typing as _typing
from dataclasses import dataclass
from typing import Any, Optional

from ..schema import (QUARANTINE_RELATION, Disclosure, Edge, EvidenceAuthor,
                      Provenance)
from ..scope import IDENTITY_MAX

#: exactly the keys the adapter requires — verified by EXECUTION against
#: `Edge.model_dump_json` (which SERIALIZES Nones rather than omitting them,
#: 0029 v9's executed finding), and WITHOUT the two derived flags.
REQUIRED_KEYS = frozenset({
    "id", "user_id", "subject", "relation", "object", "note",
    "provenance", "valid_from", "invalidated_at", "invalidation_reason",
})

#: the provenance keys the REAL `ScopeView` consumes
#: (`MembershipResolver._record_shape`): presence required even where the
#: value may be None — defaulting a missing author would have ScopeView
#: classify on a FABRICATED author.
SCOPE_PROVENANCE_KEYS = frozenset({
    "author_of_evidence", "origin", "source_id", "evidence_ref", "disclosure",
})


def _strict_pairs(pairs):
    """Reject DUPLICATE KEYS at the evidence boundary (0026's rule): plain
    `json.loads` is last-wins, and here that is a trust bypass — a payload
    carrying `"disclosure":"quarantined","disclosure":"mentionable"` would
    declassify a quarantined claim. Runs PER OBJECT, so nested `provenance`
    is covered by the same hook."""
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate key: {k!r}")
        d[k] = v
    return d


@dataclass(frozen=True)
class AdaptedProvenance:
    """Exactly what `ScopeView` reads; `author_of_evidence` is the REAL enum
    because `_record_shape` accesses `.value` on it."""
    author_of_evidence: EvidenceAuthor
    origin: Optional[str]
    source_id: Optional[str]
    evidence_ref: str
    disclosure: str


@dataclass(frozen=True)
class Adapted:
    """A payload validated, with its trust flags DERIVED. Consumable by the
    real `ScopeView` (exposes `id` and a `provenance` object; carries no
    `lineage` — edges have none) and by `semantic.content_digest`."""
    provenance: AdaptedProvenance
    id: str
    user_id: str
    subject: str
    relation: str
    object: str
    note: str
    valid_from: Any            # TEXT — the classifier normalises (as_utc_required)
    invalidated_at: Any        # TEXT or None — as_utc_optional
    invalidation_reason: Optional[str]
    disclosure: str
    quarantined: bool          # DERIVED — never read from the payload
    use_only: bool             # DERIVED — never read from the payload


def derive_quarantined(relation: str, disclosure: str) -> bool:
    """schema.py's `Edge.quarantined`: TWO disjuncts. A one-disjunct
    derivation lets a third-party CLAIM through whenever its own disclosure
    is not itself QUARANTINED."""
    return (relation == QUARANTINE_RELATION
            or disclosure == Disclosure.QUARANTINED.value)


def derive_use_only(disclosure: str) -> bool:
    """schema.py's `Edge.use_only`: one disjunct, deliberately unlike
    `quarantined`."""
    return disclosure == Disclosure.USE_ONLY.value


def _field_rule(model, name):
    """`(is_optional, min_len, max_len)` introspected from the shipped field —
    the contract is DERIVED, never restated (round-5 F4: a restated adapter
    was stricter than production on six fields at once). `get_args` is the
    principled None-test and handles PEP-604; the string test survives an
    unresolved ForwardRef where `get_args` returns `()`. Together they are the
    derivation over the twelve fields checked below."""
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
    Datetimes arrive as TEXT — the carrier is raw and the classifier
    normalises later — so a datetime-annotated field is checked as a string."""
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


def _identity_field(v) -> bool:
    """`origin`/`source_id`: None, or a 1..IDENTITY_MAX-char string — the
    bound the real `ScopeView` RAISES on (round-4 F2: `source_id=[]` passed a
    presence check and raised `ScopeError` downstream). THE ADAPTER MUST NOT
    PASS ANYTHING ITS CONSUMER WILL RAISE ON."""
    return v is None or (isinstance(v, str) and 1 <= len(v) <= IDENTITY_MAX)


def adapt(state_text: str, *, expect_id: str, expect_user: str) -> Optional[Adapted]:
    """TEXT → Adapted, or None (the single failure value)."""
    # 1. PARSE (C-1: the consumer's step), duplicate keys refused
    try:
        m = json.loads(state_text, object_pairs_hook=_strict_pairs)
    except (ValueError, TypeError, RecursionError):
        return None
    if not isinstance(m, dict):
        return None
    # 2. IDENTITY against the ROW-sourced values (C-4 / V-CARRIER-AGREES)
    if m.get("id") != expect_id or m.get("user_id") != expect_user:
        return None
    # 3. SCHEMA — missing is never defaulted (V-EXTRACT)
    if not REQUIRED_KEYS.issubset(m):
        return None
    # 3b. TYPES AND BOUNDS, per field, derived from the model (presence is not validity)
    if not all(_check_derived(Edge, k, m[k]) for k in
               ("id", "user_id", "subject", "relation", "object", "note",
                "valid_from", "invalidated_at", "invalidation_reason")):
        return None
    # 4. ENUMS: the reason's TYPE is required (an unknown STRING is coherent
    #    and fences later, F8b); disclosure must be a real member — TYPE
    #    BEFORE MEMBERSHIP (an unhashable value must never reach `in`).
    r = m["invalidation_reason"]
    if r is not None and not isinstance(r, str):
        return None
    prov = m.get("provenance")
    if not isinstance(prov, dict):
        return None
    if not SCOPE_PROVENANCE_KEYS.issubset(prov):
        return None
    disc = prov["disclosure"]
    if not isinstance(disc, str) or disc not in {d.value for d in Disclosure}:
        return None
    if not isinstance(prov["author_of_evidence"], str):
        return None
    try:
        author = EvidenceAuthor(prov["author_of_evidence"])
    except ValueError:
        return None                       # an unknown author is not defaulted
    if not all(_check_derived(Provenance, k, prov[k]) for k in
               ("evidence_ref", "origin", "source_id")):
        return None
    if not (_identity_field(prov["origin"]) and _identity_field(prov["source_id"])):
        return None
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
