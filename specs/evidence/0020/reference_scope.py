"""specs/0020 §4a-ii — the NORMATIVE reference for the scope surface.

PORTABLE AND PURE: no I/O, no external paths, no store dependency. Two
conforming implementations must agree with this module on every input; the
pinned vectors live beside it in `vectors.json` and 0020 V10 binds the
shipped implementation to both (the 0019 reference-predicate discipline,
applied to this spec's public surface — external F2).

Defines exactly: the Identity model and its resolution/equality; the
ScopePolicy model and its load-time validation (refusal cases enumerated);
the visibility decision function `classify` and its fixed decision table;
the closed filter grammar and its evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ---- Identity --------------------------------------------------------------

VALID_FILTER_FIELDS = ("subject", "relation", "author_of_evidence",
                       "source_id", "volatility")


@dataclass(frozen=True)
class Identity:
    """The (origin, source_id) pair — 0006's namespacing identity, verbatim.
    NOT authenticated (0006 R7); equality is meaningful only AFTER
    resolution."""
    origin: Optional[str]
    source_id: Optional[str]

    @property
    def unidentified(self) -> bool:
        return self.origin is None and self.source_id is None


def resolve(identity: Identity, local_origin: str) -> Identity:
    """0006 I9: an absent origin resolves to the local store's singleton —
    the same read path the identity digest uses. source_id is never
    invented. A fully-unidentified identity stays unidentified (it does not
    become (local, None) — 'the local store with no source' is the
    STORE-AUTHORED shape and reaches membership through the 0020 §4a-iii
    evidence hierarchy, never through this resolution)."""
    if identity.unidentified:
        return identity
    if identity.origin is None:
        return Identity(local_origin, identity.source_id)
    return identity


def same_identity(a: Identity, b: Identity, local_origin: str) -> bool:
    """Resolved equality. THE PINNED EXCEPTION (0020 §4a-ii): the
    unidentified never equals anything, including itself — absent==absent
    is never SAME-scope (groups-never-grants)."""
    ra, rb = resolve(a, local_origin), resolve(b, local_origin)
    if ra.unidentified or rb.unidentified:
        return False
    return ra == rb


# ---- ScopePolicy -----------------------------------------------------------

class PolicyError(ValueError):
    """Raised at CONFIG LOAD, never at recall time (0020 §2c)."""


@dataclass(frozen=True)
class ScopePolicy:
    """groups: name -> tuple of Identities. cross_scope_visible: whether
    CROSS records render at all (always third-party-shaped when they do).
    The grammar is CLOSED — no wildcards, no patterns, no precedence
    (overlap is REFUSED, so no precedence order exists to dispute)."""
    groups: dict
    cross_scope_visible: bool = False


def validate_policy(policy: ScopePolicy, local_origin: str) -> None:
    """The load-time refusal cases, enumerated (0020 §4a-ii):
    (a) a non-Identity rule shape; (b) the unidentified identity in any
    group; (c) an identity (resolved) appearing in more than one group."""
    seen: dict = {}
    if not isinstance(policy.groups, dict):
        raise PolicyError("policy.groups must be a mapping (0020 §4a-ii)")
    for name, members in policy.groups.items():
        if not isinstance(name, str) or not name:
            raise PolicyError(f"group name {name!r} is not a non-empty string")
        for m in members:
            if not isinstance(m, Identity):
                raise PolicyError(
                    f"group {name!r} carries a non-Identity rule shape "
                    f"{m!r} (0020 §4a-ii (a))")
            if m.unidentified:
                raise PolicyError(
                    f"group {name!r} contains the unidentified identity — "
                    f"the unidentified is never a principal (0020 §4a-ii (b))")
            r = resolve(m, local_origin)
            if r in seen and seen[r] != name:
                raise PolicyError(
                    f"identity {r!r} appears in groups {seen[r]!r} and "
                    f"{name!r} — overlap is REFUSED at load; no precedence "
                    f"order exists (0020 §4a-ii (c))")
            seen[r] = name


def _group_of(identity: Identity, policy: ScopePolicy,
              local_origin: str) -> Optional[str]:
    if identity.unidentified:
        return None
    r = resolve(identity, local_origin)
    for name, members in policy.groups.items():
        for m in members:
            if resolve(m, local_origin) == r:
                return name
    return None


# ---- the visibility decision ----------------------------------------------

#: record_evidence forms (0020 §4a-ii/iii): an Identity (the record's own,
#: for host-produced records), the string "UNRESOLVED" (a derivative whose
#: membership evidence failed), or an Identity carrying a derivative's
#: ledger-resolved membership.
UNRESOLVED = "UNRESOLVED"

#: the fixed decision table (0020 §4a-ii) — classification -> (visible,
#: assertability). Assertability labels: "own" = today's gate verbatim;
#: "shared" = today's gate (the C3 floor); "third-party-shaped" = the
#: non-assertable disclosure rendering; None = not visible.
DECISION_TABLE = {
    "OWN": (True, "own"),
    "SHARED": (True, "shared"),
    "CROSS_VISIBLE": (True, "third-party-shaped"),
    "CROSS_HIDDEN": (False, None),
    "UNRESOLVED": (False, None),
}


def classify(record_evidence, principal: Optional[Identity],
             policy: Optional[ScopePolicy], local_origin: str) -> str:
    """The §4a-ii decision function. `principal=None` (or no policy) is the
    UNSCOPED surface: everything is OWN — byte-identical to today, the
    migration invariant. UNRESOLVED evidence is invisible to EVERY scoped
    principal (fail-closed, external F1)."""
    if principal is None or policy is None:
        return "OWN"
    if record_evidence == UNRESOLVED:
        return "UNRESOLVED"
    if not isinstance(record_evidence, Identity):
        raise PolicyError(f"record evidence {record_evidence!r} is neither "
                          f"an Identity nor UNRESOLVED")
    if record_evidence.unidentified:
        return "SHARED"                      # C3: host-produced floor
    pg = _group_of(principal, policy, local_origin)
    rg = _group_of(record_evidence, policy, local_origin)
    if rg is None:
        # identified but in no group: its own singleton scope
        if same_identity(record_evidence, principal, local_origin):
            return "OWN"
        return "CROSS_VISIBLE" if policy.cross_scope_visible else "CROSS_HIDDEN"
    if pg is not None and pg == rg:
        return "OWN"
    return "CROSS_VISIBLE" if policy.cross_scope_visible else "CROSS_HIDDEN"


def decide(record_evidence, principal, policy, local_origin):
    """classification -> (visible, assertability) via the fixed table."""
    return DECISION_TABLE[classify(record_evidence, principal, policy,
                                   local_origin)]


# ---- the filter grammar ----------------------------------------------------

def validate_filters(filters: Optional[dict]) -> dict:
    """The CLOSED grammar (0020 §4a-ii): at most one eq-term per field,
    fields from VALID_FILTER_FIELDS only. Anything else REFUSES."""
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
    """M-2: applied AFTER scope, within the visible set; narrow only.
    `records` are mappings carrying the filterable fields; eq only."""
    out = records
    for k, v in filters.items():
        out = [r for r in out if str(r.get(k)) == v]
    return out
