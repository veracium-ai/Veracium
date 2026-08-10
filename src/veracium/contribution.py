"""specs/0014 §4a/§4b — the contribution ledger's derivations and validations.

Everything here is STORE-side: sites emit reference-only drafts (R2-1), and the
store derives identity digests and payloads from authoritative rows inside the
consuming transaction, then validates its OWN output against the closed per-site
schemas as a self-check (an invalid payload signals a derivation failure and
aborts the whole maintenance transaction — A7).
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional

# --------------------------------------------------------------------------
# The evidence-reference digest — its OWN domain-separated construction (R1-8).
# Frozen, byte-exact (R2-5): length-framed origin || evidence_ref under the
# dedicated domain, so it can never collide with 0006's source-identity digests
# even over equal inputs.

_EVIDENCE_REF_DOMAIN = b"veracium.evidence-ref.v1"


def _framed(b: bytes) -> bytes:
    return len(b).to_bytes(4, "big") + b


def evidence_ref_digest(origin: Optional[str], evidence_ref: str) -> Optional[str]:
    """NULL iff `evidence_ref == ""` — the empty string is DEFINED as absent
    (0014 §4a, stated not implied); a non-empty ref always digests. `origin`
    must already be RESOLVED (0006 §4 rule 6)."""
    if evidence_ref == "":
        return None
    if origin is None:
        raise ValueError(
            "origin must be RESOLVED before digesting (0006 §4 rule 6)")
    payload = (_EVIDENCE_REF_DOMAIN
               + _framed(origin.encode("utf-8"))
               + _framed(evidence_ref.encode("utf-8")))
    return hashlib.sha256(payload).hexdigest()


# --------------------------------------------------------------------------
# The closed per-site payload schemas (§4a) — canonical form: sorted keys,
# omitted-if-absent (`derived_from` OMITTED when None, never null). This exact
# canonical text feeds the op-key conflict comparison and the outcome digest.

_SIDE_MANDATORY = ("observed_at", "confidence", "valid_from", "disclosure")
_SIDE_OPTIONAL = ("derived_from",)
_INPUT_MANDATORY = ("observed_at", "confidence", "disclosure",
                    "author_of_evidence", "date")
_INPUT_OPTIONAL = ("derived_from",)

SITES = ("absorption", "consolidation")   # the CLOSED site set (§4a)


def canonical_payload(payload: dict) -> str:
    """Sorted keys, no whitespace — deterministic for digesting, validation,
    recomputation, and conflict comparison alike (§4a)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _validate_side(side: dict, label: str, mandatory, optional) -> None:
    if not isinstance(side, dict) or not side:
        raise ValueError(f"{label}: must be a non-empty mapping (payloads are "
                         f"TOTAL — {{}} is an integrity error, 0014 §4a)")
    keys = set(side)
    missing = set(mandatory) - keys
    if missing:
        raise ValueError(f"{label}: missing mandatory keys {sorted(missing)}")
    extra = keys - set(mandatory) - set(optional)
    if extra:
        raise ValueError(f"{label}: unknown keys {sorted(extra)} (the schema "
                         f"is CLOSED — R1-8)")
    for k, v in side.items():
        if v is None:
            raise ValueError(f"{label}.{k}: None is never encoded — optional "
                             f"keys are OMITTED when absent (§4a)")
        if not isinstance(v, (str, int, float, bool)):
            raise ValueError(f"{label}.{k}: scalar values only (content-free, "
                             f"A5) — got {type(v).__name__}")


def validate_absorption_payload(payload: dict) -> None:
    """`{"base": {...}, "contributor": {...}}` — both sides over the closed
    field set; TOTAL (the A1 no-transfer case is visible IN the values)."""
    if not isinstance(payload, dict) or set(payload) != {"base", "contributor"}:
        raise ValueError("absorption payload must be exactly "
                         "{'base': …, 'contributor': …} (0014 §4a)")
    _validate_side(payload["base"], "base", _SIDE_MANDATORY, _SIDE_OPTIONAL)
    _validate_side(payload["contributor"], "contributor",
                   _SIDE_MANDATORY, _SIDE_OPTIONAL)


def validate_consolidation_payload(payload: dict) -> None:
    """`{"input": {...}, "output_index": <int>}` — the R4-6 exact schema; an
    Episode HAS no valid_from, so the input set excludes it."""
    if not isinstance(payload, dict) or set(payload) != {"input", "output_index"}:
        raise ValueError("consolidation payload must be exactly "
                         "{'input': …, 'output_index': …} (0014 §4a)")
    idx = payload["output_index"]
    if isinstance(idx, bool) or not isinstance(idx, int) or idx < 0:
        raise ValueError("output_index must be a non-negative int (0014 §2c)")
    _validate_side(payload["input"], "input", _INPUT_MANDATORY, _INPUT_OPTIONAL)


def validate_payload(site: str, payload: dict) -> None:
    if site == "absorption":
        validate_absorption_payload(payload)
    elif site == "consolidation":
        validate_consolidation_payload(payload)
    else:
        raise ValueError(f"unknown site {site!r} — the site set is CLOSED "
                         f"({', '.join(SITES)}; 0014 §4a)")


def consolidation_op_key(operation_id: str, output_index: int,
                         contributor_type: str, contributor_id: str) -> str:
    """The consolidation retry identity (R2-2), canonical form."""
    return f"{operation_id}:{output_index}:{contributor_type}:{contributor_id}"
