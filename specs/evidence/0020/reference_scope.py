"""specs/0020 §4a-ii — the NORMATIVE reference for the scope surface (v5).

PORTABLE AND PURE: no I/O, no store dependency. Two conforming
implementations must agree with this module on every input; the pinned
vectors live beside it in `vectors.json`, the SHIPPED HARNESS
(`vector_harness.py`) executes them, and 0020 V10 binds implementations to
both.

v6 (round 4: the SEALED policy — see ScopePolicy). v5 (external round 3): **membership lives in DIGEST SPACE** (R3-2 — the
0014 ledger carries only nullable one-way `identity_digest` values;
deleted inputs cannot supply original pairs, so a resolver demanding
Identity pairs was unimplementable). This module MIRRORS the shipped
digest construction byte-for-byte (`veracium.source-id.v1`, 4-byte BE
framing — 0006 §4 rules 6/7) so policy-side digests equal store-side
digests. The resolver consumes REAL `ContributionRecord` shapes; the
legacy predicate matches the REAL op-id form (`op-<12 hex>` — the
reviewer's store probe); ABSORPTION survivors are resolved through their
ledger rows (R3-3 — a cross-digest absorption contributor marks the
survivor UNRESOLVED, closing the legacy-absorption read leak).
`ScopePolicy` cannot be constructed unvalidated (R3-1 — `__post_init__`
enforces the canonical frozen shapes, `classify` revalidates at
consumption); identity fields carry the shipped 512-char bounds.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional

VALID_FILTER_FIELDS = ("subject", "relation", "author_of_evidence",
                       "source_id", "volatility")
OP_STATES = ("none", "generating", "outputs_durable", "finalized",
             "abandoned")
IDENTITY_MAX = 512                     # the shipped Provenance field bounds

#: the shipped digest construction, mirrored EXACTLY (0006 §4 rules 6/7)
_DOMAIN = b"veracium.source-id.v1"

#: the REAL consolidation operation-id shape (store/sqlite.py:
#: f"op-{uuid4().hex[:12]}") — the round-3 store probe's form
_OP_ID = re.compile(r"^op-[0-9a-f]{12}$")

#: the reserved SHARED-POOL key (R3-4): digests are 64 hex chars, so a
#: colon-bearing literal can never collide with one
SHARED_POOL_KEY = "pool:unidentified"


class PolicyError(ValueError):
    """Raised at CONFIG LOAD, at consumption revalidation, or by the
    resolver's own validation — never silently widened past."""


def _framed(b: bytes) -> bytes:
    return len(b).to_bytes(4, "big") + b


# ---- Identity --------------------------------------------------------------

@dataclass(frozen=True)
class Identity:
    """The (origin, source_id) pair — 0006's namespacing identity, verbatim;
    strict-typed with the SHIPPED bounds (non-empty, ≤512 chars — R3-1)."""
    origin: Optional[str]
    source_id: Optional[str]

    def __post_init__(self):
        for f in (self.origin, self.source_id):
            if f is not None and (not isinstance(f, str)
                                  or not 1 <= len(f) <= IDENTITY_MAX):
                raise PolicyError(
                    f"identity field must be a 1..{IDENTITY_MAX}-char string "
                    f"or None (the shipped Provenance bounds), got {f!r}")

    @property
    def groupable(self) -> bool:
        """0006 I13: an absent source_id yields NO groupable identity —
        regardless of origin."""
        return self.source_id is not None


def resolve(identity: Identity, local_origin: str) -> Identity:
    """0006 I9: absent origin → the local singleton, uniformly."""
    if not isinstance(local_origin, str) or not local_origin:
        raise PolicyError("local_origin must be a non-empty string")
    if identity.origin is None:
        return Identity(local_origin, identity.source_id)
    return identity


def digest_of(identity: Identity, local_origin: str) -> Optional[str]:
    """The SHIPPED `source_identity_digest`, mirrored byte-for-byte over the
    RESOLVED pair: None when source_id is absent (I13 — and therefore the
    shared pool has NO digest key; see SHARED_POOL_KEY, R3-4)."""
    r = resolve(identity, local_origin)
    if r.source_id is None:
        return None
    payload = (_DOMAIN + _framed(r.origin.encode("utf-8"))
               + _framed(r.source_id.encode("utf-8")))
    return hashlib.sha256(payload).hexdigest()


def same_identity(a: Identity, b: Identity, local_origin: str) -> bool:
    """Resolved-digest equality; a non-groupable identity equals nothing,
    including itself (I13/I3)."""
    da, db = digest_of(a, local_origin), digest_of(b, local_origin)
    return da is not None and da == db


# ---- ScopePolicy — unconstructable unvalidated (R3-1) ----------------------

#: module-private sealing nonce, minted at import (R4-1): the seal binds
#: the ENTIRE canonical projection (groups, digests, the bool) so a
#: direct construction with an inconsistent digest map, a mutated backing
#: mapping, or an object.__setattr__ flip all fail the consumption check —
#: none can recompute the seal without this module's nonce.
import secrets as _secrets
_SEAL_NONCE = _secrets.token_bytes(32)


def _canonical_projection(groups, cross_scope_visible, local_origin) -> bytes:
    parts = [b"veracium.scope-policy.v1",
             b"1" if cross_scope_visible else b"0"]
    for name in sorted(groups):
        parts.append(_framed(name.encode("utf-8")))
        for m in sorted(groups[name],
                        key=lambda i: (i.origin or "", i.source_id or "")):
            parts.append(_framed((m.origin or "").encode("utf-8")))
            parts.append(_framed((m.source_id or "").encode("utf-8")))
            parts.append(_framed(digest_of(m, local_origin).encode("utf-8")))
    return b"".join(parts)


def _seal(groups, cross_scope_visible, local_origin) -> str:
    return hashlib.sha256(
        _SEAL_NONCE + _canonical_projection(groups, cross_scope_visible,
                                            local_origin)).hexdigest()


def _canonical_groups_ok(groups) -> bool:
    if not isinstance(groups, MappingProxyType):
        return False
    for name, members in groups.items():
        if not isinstance(name, str) or not isinstance(members, tuple):
            return False
        if not all(isinstance(m, Identity) and m.groupable for m in members):
            return False
    return True


@dataclass(frozen=True)
class ScopePolicy:
    """SEALED canonical form (R4-1): `validate_policy` computes `seal` over
    the ENTIRE canonical projection (groups + digests + the bool) with a
    module-private nonce. `classify` RECOMPUTES the seal at every
    consumption — a direct construction with an inconsistent
    `group_digests` map, a mutated backing mapping, or an
    `object.__setattr__` flip cannot reproduce it and REFUSES. Shape
    checks remain as the first, cheaper line."""
    groups: object
    cross_scope_visible: bool
    group_digests: object              # MappingProxy name -> frozenset[str]
    seal: str = ""

    def __post_init__(self):
        if not isinstance(self.cross_scope_visible, bool):
            raise PolicyError(
                f"cross_scope_visible must be a real bool, got "
                f"{self.cross_scope_visible!r}")
        if not _canonical_groups_ok(self.groups):
            raise PolicyError(
                "ScopePolicy must be constructed via validate_policy — "
                "groups must be the canonical frozen form")
        if not isinstance(self.group_digests, MappingProxyType):
            raise PolicyError("group_digests must be the validator's frozen "
                              "map — construct via validate_policy")


def validate_policy(groups, cross_scope_visible=False,
                    *, local_origin: str) -> ScopePolicy:
    """The factory. Refusals: non-mapping groups; members not a LIST or
    TUPLE (sets/other iterables REFUSED — unordered inputs are not a rule
    grammar, R3-1); non-Identity members; non-groupable members (I13);
    resolved-digest overlap across groups; non-bool cross_scope_visible.
    The input is never retained — canonical frozen copies only."""
    if not isinstance(cross_scope_visible, bool):
        raise PolicyError(
            f"cross_scope_visible must be a real bool, got "
            f"{cross_scope_visible!r}")
    if not isinstance(groups, dict):
        raise PolicyError("groups must be a mapping")
    seen: dict = {}
    frozen_groups, frozen_digests = {}, {}
    for name, members in groups.items():
        if not isinstance(name, str) or not name:
            raise PolicyError(f"group name {name!r} is not a non-empty string")
        if not isinstance(members, (list, tuple)):
            raise PolicyError(
                f"group {name!r} members must be a list or tuple, got "
                f"{type(members).__name__} (sets and other iterables are "
                f"REFUSED — R3-1)")
        out, digs = [], set()
        for m in members:
            if not isinstance(m, Identity):
                raise PolicyError(f"group {name!r} carries a non-Identity "
                                  f"rule shape {m!r}")
            if not m.groupable:
                raise PolicyError(
                    f"group {name!r} contains a source_id-less identity "
                    f"(0006 I13 — no groupable identity)")
            d = digest_of(m, local_origin)
            if d in seen and seen[d] != name:
                raise PolicyError(
                    f"identity digest {d[:12]}… appears in groups "
                    f"{seen[d]!r} and {name!r} — overlap is REFUSED at load")
            seen[d] = name
            out.append(m); digs.add(d)
        frozen_groups[name] = tuple(out)
        frozen_digests[name] = frozenset(digs)
    proxy = MappingProxyType(frozen_groups)   # backing dict is LOCAL —
    pol = ScopePolicy(groups=proxy,           # no caller ever held it
                      cross_scope_visible=cross_scope_visible,
                      group_digests=MappingProxyType(frozen_digests),
                      seal=_seal(frozen_groups, cross_scope_visible,
                                 local_origin))
    return pol


def _revalidate(policy: ScopePolicy, local_origin: str) -> None:
    """Consumption-time revalidation (R3-1/R4-1): shape checks, then the
    SEAL recomputed over the policy's CURRENT state — the entire canonical
    projection including the digest map's backing content and the bool. An
    inconsistent digest map, a mutated backing dict, or a post-hoc
    attribute flip yields a different projection and refuses; the
    digest-map consistency is checked by recomputation, not trust."""
    if not isinstance(policy, ScopePolicy):
        raise PolicyError("policy must be a ScopePolicy")
    if not isinstance(policy.cross_scope_visible, bool) \
            or not _canonical_groups_ok(policy.groups):
        raise PolicyError("policy failed consumption revalidation")
    expected_digs = {name: frozenset(digest_of(m, local_origin)
                                     for m in members)
                     for name, members in policy.groups.items()}
    if dict(policy.group_digests) != expected_digs:
        raise PolicyError(
            "group_digests is not the canonical projection of groups — "
            "a direct construction or a mutated backing map (R4-1)")
    if policy.seal != _seal(dict(policy.groups),
                            policy.cross_scope_visible, local_origin):
        raise PolicyError(
            "the policy seal does not verify — constructed outside "
            "validate_policy or mutated after validation (R4-1)")


# ---- the record→membership RESOLVER — DIGEST SPACE (R3-2 / R3-3) -----------

UNRESOLVED = "UNRESOLVED"
SHARED = "SHARED_POOL"


def is_legacy_derivative(record: dict) -> bool:
    """The REAL shape (R3-2 — the store probe): a consolidation output's
    `evidence_ref` is its operation id, `op-<12 hex>`; a legacy (pre-0021)
    output still carries the copied groupable identity."""
    return (record.get("author") == "system"
            and bool(_OP_ID.match(str(record.get("evidence_ref", ""))))
            and record.get("source_id") is not None)


def membership(record: dict, rows: Optional[list], op_state: str,
               local_origin: str, *, expected_contributors: Optional[int] = None):
    """record + REAL ledger rows + operation state → membership evidence:
    a DIGEST (str), SHARED, or UNRESOLVED (fail-closed).

    `record`: {"author", "origin", "source_id", "evidence_ref",
    "lineage": bool} — the provenance-shape fields. `rows`: the record's
    `ContributionRecord`s AS SHIPPED — [{"site": "absorption" |
    "consolidation", "identity_digest": str|None, "op_key": str|None}] —
    keyed by survivor_id (None/[] = no rows). `expected_contributors`: the
    completeness denominator the store derives (lineage length for
    consolidation outputs; None = unknown → incomplete).

    The table, total:
    - legacy-shaped (the predicate) → UNRESOLVED, whatever it claims.
    - "generating" → UNRESOLVED until finalization; "abandoned" → refuse
      (no output exists, 0010).
    - ABSORPTION SURVIVOR (a non-lineage record WITH absorption rows —
      R3-3): any row's identity_digest differing from the record's own
      digest (None counts as differing from a digest, and a digest from
      None) → UNRESOLVED — a pre-0021 absorption moved another identity's
      testimony into this record and the ledger says so. All rows matching
      the own digest → the own digest.
    - consolidation output (lineage): rows None/empty or
      expected_contributors unknown/mismatched → UNRESOLVED (incomplete).
      All identity_digest one non-null value → that digest. All None →
      SHARED (the pool's derivatives stay pooled). Mixed → UNRESOLVED.
    - ordinary host record, no rows: own digest, or SHARED when
      non-groupable (C3's floor — host-produced only)."""
    if op_state not in OP_STATES:
        raise PolicyError(f"unknown operation state {op_state!r} — the set "
                          f"is closed: {OP_STATES}")
    if op_state == "abandoned":
        raise PolicyError("an abandoned operation has no surviving output "
                          "(0010) — a record claiming one is malformed")
    if is_legacy_derivative(record):
        return UNRESOLVED
    if op_state == "generating":
        return UNRESOLVED
    own = digest_of(Identity(record.get("origin"), record.get("source_id")),
                    local_origin)
    is_lineage = bool(record.get("lineage"))
    rows = rows or []
    if not is_lineage:
        ab = [r for r in rows if r.get("site") == "absorption"]
        if ab:                                            # R3-3
            for r in ab:
                if r.get("identity_digest") != own:
                    return UNRESOLVED
        return own if own is not None else SHARED
    # consolidation output
    cons = [r for r in rows if r.get("site") == "consolidation"]
    if (not cons or expected_contributors is None
            or len(cons) != expected_contributors):
        return UNRESOLVED
    digs = {r.get("identity_digest") for r in cons}
    if digs == {None}:
        return SHARED
    if None in digs or len(digs) != 1:
        return UNRESOLVED
    return next(iter(digs))


# ---- the visibility decision (DIGEST space) --------------------------------

DECISION_TABLE = {
    "OWN": (True, "own"),
    "SHARED": (True, "shared"),
    "CROSS_VISIBLE": (True, "third-party-shaped"),
    "CROSS_HIDDEN": (False, None),
    "UNRESOLVED": (False, None),
}


def _group_of_digest(d: str, policy: ScopePolicy) -> Optional[str]:
    for name, digs in policy.group_digests.items():
        if d in digs:
            return name
    return None


def classify(record_evidence, principal: Optional[Identity],
             policy: Optional[ScopePolicy], local_origin: str) -> str:
    """`record_evidence` is the RESOLVER's output: a digest string, SHARED,
    or UNRESOLVED. `principal=None` → unscoped, everything OWN. A principal
    WITHOUT a policy REFUSES (R2-2); a source_id-less principal REFUSES
    (I13). The policy is REVALIDATED at consumption (R3-1)."""
    if principal is None:
        return "OWN"
    if policy is None:
        raise PolicyError(
            "a principal was supplied but no scope policy is configured — "
            "feature-disabled cannot honour a principal-bearing call (R2-2)")
    _revalidate(policy, local_origin)
    if not principal.groupable:
        raise PolicyError("a principal must carry a source_id (0006 I13)")
    if record_evidence == UNRESOLVED:
        return "UNRESOLVED"
    if record_evidence == SHARED:
        return "SHARED"
    if not (isinstance(record_evidence, str)
            and re.fullmatch(r"[0-9a-f]{64}", record_evidence)):
        raise PolicyError(f"record evidence {record_evidence!r} is not a "
                          f"digest / SHARED_POOL / UNRESOLVED")
    pd = digest_of(principal, local_origin)
    if record_evidence == pd:
        return "OWN"
    pg = _group_of_digest(pd, policy)
    rg = _group_of_digest(record_evidence, policy)
    if rg is not None and pg is not None and pg == rg:
        return "OWN"
    return "CROSS_VISIBLE" if policy.cross_scope_visible else "CROSS_HIDDEN"


def decide(record_evidence, principal, policy, local_origin):
    return DECISION_TABLE[classify(record_evidence, principal, policy,
                                   local_origin)]


# ---- the filter grammar ----------------------------------------------------

def validate_filters(filters: Optional[dict]) -> dict:
    if filters is None:
        return {}
    if not isinstance(filters, dict):
        raise PolicyError("filters must be a mapping of field -> value")
    for k, v in filters.items():
        if k not in VALID_FILTER_FIELDS:
            raise PolicyError(f"unknown filter field {k!r} — the field set "
                              f"is CLOSED: {VALID_FILTER_FIELDS}")
        if not isinstance(v, str) or not v:
            raise PolicyError(f"filter {k!r} value must be a non-empty "
                              f"string (eq is the only v1 operator)")
    return dict(filters)


def apply_filters(records: list, filters: dict) -> list:
    """M-2: after scope, within the visible set; narrow only. A `source_id`
    filter never matches a cleared derivative (its field is None; the
    ledger holds only a one-way digest)."""
    out = records
    for k, v in filters.items():
        out = [r for r in out if r.get(k) is not None and str(r.get(k)) == v]
    return out
