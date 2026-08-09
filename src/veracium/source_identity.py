"""specs/0006 §4 rules 7–8 — the ONE canonical source-identity digest primitive.

Source identity is the pair `(origin, source_id)` (0006 R5). This module is the
single shared construction every consumer MUST call — `0014`'s contribution
ledger and a future `revoke_source` — so they re-derive a byte-identical key.
That is the whole point of the pair being a *shared* join key: two independently
coded consumers that pick different framing would silently stop joining, and a
silent join miss in revocation is under-revocation, the failure `specs/0002` A3
exists to prevent (F2/I12).

Construction (frozen, 0006 §4 rule 7): domain-separated, length-framed SHA-256 —
`SHA-256(DOMAIN ‖ u32be(len(origin)) ‖ origin ‖ u32be(len(source_id)) ‖ source_id)`,
components UTF-8, lengths fixed-width big-endian. Length-framing is what stops the
bare-concatenation collision `("ab","c") == ("a","bc")`.

Absent `source_id` ⇒ no source identity ⇒ NO digest (F1/I13): the digest is
defined only when `source_id` is present, and a consumer that stores it must write
NULL for an unknown source — never a `(resolved_origin, NULL)` pseudo-source.

Deterministic and UNSALTED — therefore enumerable for predictable ids. Claimed as
hygiene, never confidentiality (I5 keeps it off every trust decision).
"""
from __future__ import annotations

import hashlib
from typing import Optional

# Domain separation — this digest is never confusable with any other in the store.
_DOMAIN = b"veracium.source-id.v1"


def _framed(b: bytes) -> bytes:
    """Length-prefix a component with a fixed-width 4-byte big-endian length, so no
    two distinct component pairs share an encoding (0006 §4 rule 7)."""
    return len(b).to_bytes(4, "big") + b


def resolve_origin(stored_origin: Optional[str], local_origin: str) -> str:
    """0006 §4 rule 6 — the ONE resolve-at-read chokepoint. An absent (locally
    stored) `origin` resolves to THIS store's `store_identity` singleton BEFORE any
    comparison, grouping, digest or export; a present `origin` is returned as-is (a
    foreign/imported record keeps its own — I2b). Every consumer resolves here and
    nowhere else, so a local record and its own export round-trip group as one (I9).
    """
    return local_origin if stored_origin is None else stored_origin


def source_identity_digest(origin: Optional[str], source_id: Optional[str]) -> Optional[str]:
    """The canonical digest of a **resolved** `(origin, source_id)` pair, or `None`
    when `source_id` is absent (I13 — unknown source, no groupable identity).

    `origin` MUST already be resolved (0006 §4 rule 6): pass a present foreign
    origin unchanged, or `resolve_origin(...)`'s output for a local record. A `None`
    `origin` alongside a present `source_id` is a programming error — resolve first —
    and raises, rather than silently digesting a half-identity."""
    if source_id is None:
        return None
    if origin is None:
        raise ValueError(
            "origin must be RESOLVED before digesting (0006 §4 rule 6) — pass the "
            "store_identity singleton via resolve_origin() for a local record")
    payload = _DOMAIN + _framed(origin.encode("utf-8")) + _framed(source_id.encode("utf-8"))
    return hashlib.sha256(payload).hexdigest()
