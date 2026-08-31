"""specs/0027 — the semantic lane's shared projections and vector plumbing.

Everything here is TRUST-INERT by construction (0027 §3): these helpers
select and rank candidates; no function in this module reads or writes a
trust property, and the embedding is a regenerable derived INDEX, never
evidence. The two projections are §4e's, named and frozen:

- the DIGEST projection binds a stored vector to the BYTES that were
  embedded (edge text can change under a stable id — note-append, confirm,
  recompute — so the digest, not the id, is the binding; V-FRESH);
- the EMBEDDED TEXT is the digest projection's four values joined readable.

Vector hygiene is §4d's: components must be real numbers (`bool` REJECTED
even though it subclasses `int`), finite, non-zero-vector, exactly `dim`
long; blobs are `dim` float32 little-endian; cosine runs in float64 and a
zero-norm vector is refused, never divided by (V5).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct

# §4d: one id() PERMANENTLY denotes one embedding behaviour; the shape is
# validated here, byte-equality everywhere else.
EMBEDDER_ID_RE = re.compile(r"^[A-Za-z0-9._@:+-]{1,128}$")


def content_digest(edge) -> str:
    """The §4e digest projection — the codebase's shipped canonical form
    (sqlite.py's sort_keys/compact-separators sha256 convention), keys fixed
    to exactly {subject, relation, object, note}, values verbatim."""
    payload = {"subject": edge.subject, "relation": edge.relation,
               "object": edge.object, "note": edge.note}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


def embedded_text(edge) -> str:
    """What the embedder sees — the digest projection's values, joined."""
    return f"{edge.subject} {edge.relation} {edge.object} {edge.note}"


def validate_vector(vec, dim: int):
    """Return the vector as a list of floats, or None if REFUSED (V5):
    wrong container/length, a bool component, a non-real component, a
    non-finite component, or the zero vector."""
    if isinstance(vec, (bytes, str)) or not hasattr(vec, "__len__"):
        return None
    if len(vec) != dim:
        return None
    out = []
    for x in vec:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            return None
        f = float(x)
        if not math.isfinite(f):
            return None
        out.append(f)
    if not any(out):
        return None
    return out


def pack_vec(floats) -> bytes:
    """dim × float32, little-endian (§4f serialization)."""
    return struct.pack(f"<{len(floats)}f", *floats)


def unpack_vec(blob, dim: int):
    """Inverse of pack_vec; a blob of any other length is refused (V5)."""
    if not isinstance(blob, (bytes, bytearray)) or len(blob) != 4 * dim:
        return None
    return list(struct.unpack(f"<{dim}f", bytes(blob)))


def cosine(a, b):
    """float64 cosine; None when either norm is zero (refused, V5)."""
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return None
    return dot / math.sqrt(na * nb)


def embedder_identity(embed):
    """Resolve (embedder_id, dim, status) from a host `Embed` (§4d).

    status: 'ok' — both methods present, well-formed; 'no_embedder' — the
    embedder or either method is ABSENT; 'unavailable' — a method raised or
    returned a malformed value (empty/pattern-violating id; non-int/<=0/bool
    dim). Never propagates the host's exception."""
    if embed is None:
        return None, None, "no_embedder"
    ident = getattr(embed, "id", None)
    dimf = getattr(embed, "dim", None)
    if ident is None or dimf is None:
        return None, None, "no_embedder"
    try:
        eid = ident()
        dim = dimf()
    except Exception:
        return None, None, "unavailable"
    if not isinstance(eid, str) or not EMBEDDER_ID_RE.match(eid):
        return None, None, "unavailable"
    if isinstance(dim, bool) or type(dim) is not int or dim <= 0:
        return None, None, "unavailable"
    return eid, dim, "ok"
