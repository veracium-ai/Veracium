"""specs/0031 §4f (amendment `0031/trust-tools-direct`): the trust tools' shared vocabulary.

The closed refusal reasons the seven agent tools serialize (§4a), and `TrustRefused`, the one exception the library
verbs raise for the scope gates of §3b. A refusal is a VALUE: the tools return it as
`{"ok": false, "refusal": <reason>, "detail": <=200 chars>}` and never raise it to the transport (INV-TT11).
"""
from __future__ import annotations

from .census import declare_site

# specs/0031 §4f §4e: research's 0042 stage-1 classification (2026-11-15) — enforcement points (INV-TT8, INV-TT21)
_SITE_TOKEN_PARSE = declare_site("trust.token.parse")     # the single exit where every malformed token is refused
_SITE_TOKEN_VERIFY = declare_site("trust.token.verify")   # context, MAC-or-user, a future t, expiry

#: §4a's refusal vocabulary, closed. The order is the gate order of §4a where a gate owns the reason.
REFUSALS = (
    "attempted_elevation",     # 1. capability: anything but `direct`
    "erasure_disabled",        # 2. the erasure switch (the three forget tools)
    "principal_scoped",        # 3. the whole-user erase under any principal
    "invalid_target",          # 4. input: exactly one of edge_id / episode_id
    "reason_too_long",         # 4. input: dispute's reason over 1,024 code points
    "preview_unknown",         # 4. / §4e: a token that does not parse, or is not this issuer's
    "scope_unconfigured",      # 5. a principal with no scope policy configured
    "principal_ungroupable",   # 5. a principal with no source_id
    "source_unbound",          # 6. a writing verb under a principal whose binding has no source
    "source_out_of_scope",     # 6. a binding source the principal's view does not class OWN
    "not_found_in_scope",      # 7. CROSS_HIDDEN, UNRESOLVED, another user's id, an unknown id: one response
    "out_of_scope",            # 7. SHARED or CROSS_VISIBLE under a principal
    "correction_refused",      # 8. CorrectionRefused: a COMMITTED refusal (TT-R2-02)
    "preview_expired",         # §4e step 3
    "store_changed",           # §4e step 4
    "refused",                 # 8. any other library refusal (ValueError, TypeError, ScopeError)
)

#: the detail every `not_found_in_scope` carries, fixed so the response is identical across the four cases it
#: covers and is no existence oracle (§3b, INV-TT7, INV-TT16)
NOT_FOUND_DETAIL = "no such record in this scope"
OUT_OF_SCOPE_DETAIL = "this record is visible here but not yours to change"

_DETAILS = {
    "scope_unconfigured": "a principal was supplied but no scope policy is configured",
    "principal_ungroupable": "a principal must carry a source_id",
    "source_unbound": "this binding has no source, so a write under a principal could not be scoped",
    "source_out_of_scope": "this binding's source is not in the principal's own scope",
    "not_found_in_scope": NOT_FOUND_DETAIL,
    "out_of_scope": OUT_OF_SCOPE_DETAIL,
}


class TrustInternalError(RuntimeError):
    """specs/0031 §4a step 8, INV-TT11 (round 3, TT-R3-03): a failure inside a trust-tool call AFTER something in the
    call committed. Never a refusal and never a ValueError/TypeError, so no caller can read it as one; the original
    failure is chained as `__cause__`."""


class TrustRefused(ValueError):
    """A §3b scope refusal raised by a library verb under a principal, BEFORE anything is written. `reason` is one
    of `REFUSALS`; the detail is fixed per reason, so no refusal carries record content or an existence signal."""

    def __init__(self, reason: str):
        if reason not in REFUSALS:
            raise ValueError(f"unknown trust refusal {reason!r}")
        self.reason = reason
        self.detail = _DETAILS.get(reason, reason)
        super().__init__(f"{reason}: {self.detail}")


# --------------------------------------------------------------------------------------------------------------------
# §4e: the whole-user erase in two steps — the snapshot digest, the per-surface token issuer, the strict token parser
# --------------------------------------------------------------------------------------------------------------------
import base64 as _b64
import hashlib as _hashlib
import hmac as _hmac
import json as _json
import secrets as _secrets
import time as _time
from datetime import datetime as _dt, timezone as _tz

#: the four tables the preview shows and binds, IN THIS ORDER (§4e step 1); each keyed by `id`
ERASE_PREVIEW_TABLES = ("edges", "episodes", "confirmations", "replies")
#: the token's lifetime, in seconds (§4e step 5): valid iff t <= now < t + TOKEN_TTL
TOKEN_TTL = 600
_MAC_DOMAIN = b"veracium/0031-tt/preview/v1"
_PREFIX = "tt1"
PREVIEW_UNKNOWN_DETAIL = "issued by another server process, or not issued"
_DETAILS.update({
    "preview_unknown": PREVIEW_UNKNOWN_DETAIL,
    "preview_expired": "the preview is older than ten minutes; preview again",
    "store_changed": "the records changed since the preview; preview again",
    "principal_scoped": "the whole-user erase is not available under a principal",
})
#: §4e step 5's fixed warning, shown to the user before the second step
ERASE_WARNING = ("Irreversible: this erases everything stored for this user, the audit trail included. The counts and "
                 "the confirmation bind which records exist in the four tables shown (edges, episodes, "
                 "confirmations, replies), not their contents; other tables are erased without being counted. "
                 "Export first if a copy is wanted.")


def _sorted_keys(keys) -> list:
    """Ascending as UTF-8 byte strings (§4e step 1), never by Python's code-point order alone."""
    return sorted(keys, key=lambda k: k.encode("utf-8"))


def snapshot_digest(user_id: str, keys: dict) -> str:
    """§4e step 3: SHA-256 over the canonical UTF-8 JSON
    `{"v":1,"user":<user>,"tables":[["edges",[...]],["episodes",[...]],["confirmations",[...]],["replies",[...]]]}`
    — separators `,` and `:`, no whitespace, no ASCII escaping; table-tagged, so the same textual key in another
    table is a different set. `keys` maps each of the four tables to its key list, already in snapshot order."""
    body = {"v": 1, "user": user_id,
            "tables": [[t, list(keys[t])] for t in ERASE_PREVIEW_TABLES]}
    return _hashlib.sha256(_json.dumps(body, separators=(",", ":"), ensure_ascii=False)
                           .encode("utf-8")).hexdigest()


def _b64url(raw: bytes) -> str:
    return _b64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_strict(seg: str) -> bytes:
    """Canonical base64url with no padding: the alphabet only, and re-encoding must reproduce the segment exactly
    (this rejects non-zero pad bits and every padded form). Raises ValueError on anything else."""
    if not seg or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in seg):
        raise ValueError("alphabet")
    if len(seg) % 4 == 1:
        raise ValueError("length")
    raw = _b64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4))
    if _b64url(raw) != seg:
        raise ValueError("non-canonical")
    return raw


def _no_dup_object(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate member {k!r}")
        out[k] = v
    return out


def parse_token(token) -> tuple:
    """§4e confirm step 1, the STRICT parse (TT-R2-04). Returns `(payload_segment, u, d, t, mac)` or raises
    `TrustRefused("preview_unknown")` with its one fixed detail, for every malformed form alike."""
    with _SITE_TOKEN_PARSE.consult():
        try:
            if not isinstance(token, str):
                raise ValueError("type")
            parts = token.split(".")
            if len(parts) != 3 or parts[0] != _PREFIX:
                raise ValueError("shape")
            payload_seg, mac_seg = parts[1], parts[2]
            payload = _b64url_strict(payload_seg).decode("utf-8")          # malformed UTF-8 raises here
            obj = _json.loads(payload, object_pairs_hook=_no_dup_object)
            if not isinstance(obj, dict) or set(obj) != {"u", "d", "t"}:
                raise ValueError("keys")
            u, d, t = obj["u"], obj["d"], obj["t"]
            if not isinstance(u, str) or type(t) is not int:                 # a boolean t is refused (type, not isinstance)
                raise ValueError("types")
            if not (isinstance(d, str) and len(d) == 64 and all(c in "0123456789abcdef" for c in d)):
                raise ValueError("digest")
            mac = _b64url_strict(mac_seg)
            if len(mac) != 32:
                raise ValueError("mac length")
        except ValueError:          # binascii.Error and UnicodeDecodeError are both ValueErrors
            raise _SITE_TOKEN_PARSE.fire(TrustRefused("preview_unknown"), "malformed") from None
        return payload_seg, u, d, t, mac


class PreviewTokenIssuer:
    """§4e's issuer: one per SURFACE (the MCP server owns one; each framework-adapter binding owns one; an embedded
    host constructs its own and passes it explicitly). It holds a 32-byte key from `secrets.token_bytes(32)`,
    generated here, never written, kept for the issuer's lifetime only — there is no process-global key and nothing
    falls back to one — and its CONTEXT: the store's identity (`store_identity`) and the user. A token checked by an
    issuer for another store or user is refused. `clock` returns integer Unix seconds UTC (injectable for tests);
    `key` is injectable only so the published vectors can be reproduced (INV-TT21)."""

    def __init__(self, store_identity: str, user_id: str, *, clock=None, key: bytes = None):
        if not isinstance(store_identity, str) or not store_identity:
            raise ValueError("an issuer needs the store's identity")
        if not isinstance(user_id, str) or not user_id:
            raise ValueError("an issuer needs the user")
        self.store_identity = store_identity
        self.user_id = user_id
        self._key = _secrets.token_bytes(32) if key is None else key
        if not (isinstance(self._key, bytes) and len(self._key) == 32):
            raise ValueError("an issuer key is exactly 32 bytes")
        self._clock = clock or (lambda: int(_time.time()))

    def now(self) -> int:
        t = self._clock()
        if type(t) is not int:
            raise ValueError("the issuer clock returns integer Unix seconds")
        return t

    def _mac(self, payload_seg: str) -> bytes:
        return _hmac.new(self._key, _MAC_DOMAIN + b"\x00" + payload_seg.encode("ascii"), _hashlib.sha256).digest()

    def issue(self, digest: str, issued_at: int) -> str:
        """`tt1.<payload>.<mac>`: payload = base64url (no padding) of `{"u":<user>,"d":<digest>,"t":<issued_at>}`,
        canonical JSON; mac = base64url of HMAC-SHA-256 over `veracium/0031-tt/preview/v1` NUL <the payload
        segment's ASCII bytes as transmitted> (TT-R2-04)."""
        payload = _json.dumps({"u": self.user_id, "d": digest, "t": issued_at}, separators=(",", ":"),
                              ensure_ascii=False).encode("utf-8")
        seg = _b64url(payload)
        return f"{_PREFIX}.{seg}.{_b64url(self._mac(seg))}"

    def verify(self, token, *, store_identity: str, user_id: str) -> tuple:
        """§4e confirm steps 1–3: parse strictly, check the issuer's CONTEXT against the receiving store and user,
        verify the MAC with `hmac.compare_digest`, then the time. Returns the bound digest; raises `TrustRefused`
        (`preview_unknown` or `preview_expired`)."""
        payload_seg, u, d, t, mac = parse_token(token)
        with _SITE_TOKEN_VERIFY.consult():
            if (store_identity, user_id) != (self.store_identity, self.user_id):
                raise _SITE_TOKEN_VERIFY.fire(TrustRefused("preview_unknown"), "context")
            if not _hmac.compare_digest(mac, self._mac(payload_seg)) or u != self.user_id:
                raise _SITE_TOKEN_VERIFY.fire(TrustRefused("preview_unknown"), "mac-or-user")
            now = self.now()
            if t > now:
                raise _SITE_TOKEN_VERIFY.fire(TrustRefused("preview_unknown"), "future-t")
            if now >= t + TOKEN_TTL:
                raise _SITE_TOKEN_VERIFY.fire(TrustRefused("preview_expired"), "expired")
            return d


def expires_at(issued_at: int) -> str:
    return _dt.fromtimestamp(issued_at + TOKEN_TTL, tz=_tz.utc).isoformat()


# --------------------------------------------------------------------------------------------------------------------
# §4b: the render receipt — what the renderer ADMITTED, built as it admits each unit (TT-R1-03)
# --------------------------------------------------------------------------------------------------------------------
def edge_annotations(edge) -> list:
    """The mandatory annotations an edge's rendered line carries (graph.render_edges), as closed labels: never a raw
    field (round 2's answer 5: annotations never carry unadmitted raw fields)."""
    out = []
    if not edge.active:
        out.append("superseded")
    if edge.active and edge.needs_confirmation:
        out.append("stale")
    if edge.ungrounded:
        out.append("extraction_error")
    if edge.active and edge.use_only and not edge.quarantined:
        out.append("unconfirmed")
    return out


class RenderReceipt:
    """One recall's render receipt (§4b): a unit per record the renderer admitted, appended AT the admission point,
    in admission order, with the text exactly as admitted. Never built by matching prose, never by re-reading a
    record, never from `Recall.edges`: a record the renderer withheld is not a unit. `view` is the call's principal
    view (None unscoped); under one, each unit carries `mutable` (§3b: OWN only)."""

    def __init__(self, view=None):
        self.view = view
        self.units: list = []

    def admit(self, kind: str, record, text: str, partition: str, annotations=(), subject=None):
        """`subject` (TT-R3-02) is `(segment, anchor, offset)` from the composer that rendered it: the subject AS
        RENDERED (clamped when the line clamped it), found at `offset` in `anchor`, which is the admitted text or one
        of the unit's annotations. None when the admitted line names no subject other than the user; then the unit
        carries none. Never the record's raw field: a segment not at its place is an internal failure."""
        unit = {"kind": kind, "id": None if record is None else record.id, "text": text,
                "partition": partition, "annotations": list(annotations)}
        if subject is not None:
            seg, anchor, off = subject
            if not (anchor == text or anchor in unit["annotations"]) or anchor[off:off + len(seg)] != seg:
                raise RuntimeError("render receipt: a subject segment not at its place in the admitted text")
            unit["subject"] = seg
        if self.view is not None:
            unit["mutable"] = record is not None and self.view.classification(record) == "OWN"
        self.units.append(unit)
