"""specs/0020 §4a-ii — the NORMATIVE reference for the scope surface (v4).

PORTABLE AND PURE: no I/O, no external paths, no store dependency. Two
conforming implementations must agree with this module on every input; the
pinned vectors live beside it in `vectors.json` and 0020 V10 binds the
shipped implementation to both.

v4 (external round 2): (R2-1) identity semantics are ACCEPTED 0006's,
verbatim — **an absent `source_id` means NO groupable identity, regardless
of origin (I13); absence never relaxes a rule (I3)** — so "unidentified"
is `source_id is None`, not `(None, None)`; principals and group members
REQUIRE a source_id; validation is strict-typed (the 0019 F7 posture:
`cross_scope_visible` must be a real bool — "false" REFUSES) and policies
are RECURSIVELY FROZEN at validation (the returned canonical policy admits
no post-validation mutation; the mutation oracle is vectored). (R2-2) a
principal WITHOUT a configured policy REFUSES — feature-disabled and
configured-empty are distinct states. (R2-3) the record→membership
RESOLVER is normative here: `membership()` converts a record's raw
identity + ledger evidence + operation/import state into the evidence
`classify()` consumes — the 0020↔0021 seam, mechanical.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional

VALID_FILTER_FIELDS = ("subject", "relation", "author_of_evidence",
                       "source_id", "volatility")

#: 0021's operation states at recovery time (accepted 0010's vocabulary) —
#: the resolver is TOTAL over these (R2-3)
OP_STATES = ("none", "generating", "outputs_durable", "finalized",
             "abandoned")


class PolicyError(ValueError):
    """Raised at CONFIG LOAD or by the resolver's own validation — never
    silently widened past."""


# ---- Identity --------------------------------------------------------------

@dataclass(frozen=True)
class Identity:
    """The (origin, source_id) pair — 0006's namespacing identity, verbatim.
    NOT authenticated (0006 R7)."""
    origin: Optional[str]
    source_id: Optional[str]

    def __post_init__(self):
        for f in (self.origin, self.source_id):
            if f is not None and (not isinstance(f, str) or not f):
                raise PolicyError(f"identity field {f!r} must be a non-empty "
                                  f"string or None (strict types, R2-1)")

    @property
    def groupable(self) -> bool:
        """0006 I13: an absent source_id yields NO groupable identity —
        REGARDLESS of origin. (origin-only identities are exactly the
        pseudo-source I13 forbids.)"""
        return self.source_id is not None


def resolve(identity: Identity, local_origin: str) -> Identity:
    """0006 I9: an absent origin resolves to the local store's singleton —
    uniformly, including for source_id-less identities (R2-1: the v3
    special case contradicted I9). Groupability is judged AFTER resolution
    and is source_id's alone (I13)."""
    if not isinstance(local_origin, str) or not local_origin:
        raise PolicyError("local_origin must be a non-empty string")
    if identity.origin is None:
        return Identity(local_origin, identity.source_id)
    return identity


def same_identity(a: Identity, b: Identity, local_origin: str) -> bool:
    """Resolved equality — defined ONLY over groupable identities: a
    source_id-less identity equals nothing, including itself (I13/I3;
    absent==absent is never SAME)."""
    ra, rb = resolve(a, local_origin), resolve(b, local_origin)
    if not ra.groupable or not rb.groupable:
        return False
    return ra == rb


# ---- ScopePolicy -----------------------------------------------------------

@dataclass(frozen=True)
class ScopePolicy:
    """Canonical FROZEN form: `groups` is a MappingProxy of name -> tuple of
    Identity (frozen dataclasses). Construct via `validate_policy` — direct
    construction with mutable state is refused there; the returned object
    admits no post-validation mutation (R2-1's oracle)."""
    groups: object
    cross_scope_visible: bool = False


def validate_policy(groups: dict, cross_scope_visible: bool = False,
                    *, local_origin: str) -> ScopePolicy:
    """The load-time validator — returns the CANONICAL FROZEN policy or
    raises. Refusals, enumerated (R2-1 extends v3's set):
    (a) non-Identity rule shapes / non-string names;
    (b) a NON-GROUPABLE identity in any group (source_id absent — I13; the
        v3 rule refused only (None, None));
    (c) an identity (resolved) in more than one group — no precedence
        order exists;
    (d) `cross_scope_visible` not a REAL bool ("false"/0/1 REFUSE — the
        0019 F7 strict posture; a truthy string silently widened v3);
    (e) non-mapping groups / non-sequence members."""
    if not isinstance(cross_scope_visible, bool):
        raise PolicyError(
            f"cross_scope_visible must be a real bool, got "
            f"{cross_scope_visible!r} (strict — a truthy string would "
            f"silently widen visibility; R2-1 (d))")
    if not isinstance(groups, dict):
        raise PolicyError("groups must be a mapping (R2-1 (e))")
    seen: dict = {}
    frozen_groups = {}
    for name, members in groups.items():
        if not isinstance(name, str) or not name:
            raise PolicyError(f"group name {name!r} is not a non-empty string")
        if isinstance(members, (str, bytes)) or not hasattr(members, "__iter__"):
            raise PolicyError(f"group {name!r} members must be a sequence")
        out = []
        for m in members:
            if not isinstance(m, Identity):
                raise PolicyError(f"group {name!r} carries a non-Identity "
                                  f"rule shape {m!r} (R2-1 (a))")
            if not m.groupable:
                raise PolicyError(
                    f"group {name!r} contains a source_id-less identity — "
                    f"an absent source_id yields NO groupable identity, "
                    f"regardless of origin (0006 I13; R2-1 (b))")
            r = resolve(m, local_origin)
            if r in seen and seen[r] != name:
                raise PolicyError(
                    f"identity {r!r} appears in groups {seen[r]!r} and "
                    f"{name!r} — overlap is REFUSED at load (c)")
            seen[r] = name
            out.append(m)
        frozen_groups[name] = tuple(out)
    return ScopePolicy(groups=MappingProxyType(frozen_groups),
                       cross_scope_visible=cross_scope_visible)


def _group_of(identity: Identity, policy: ScopePolicy,
              local_origin: str) -> Optional[str]:
    if not identity.groupable:
        return None
    r = resolve(identity, local_origin)
    for name, members in policy.groups.items():
        for m in members:
            if resolve(m, local_origin) == r:
                return name
    return None


# ---- the record→membership RESOLVER (R2-3 — the 0020↔0021 seam) -----------

UNRESOLVED = "UNRESOLVED"
SHARED = "SHARED_POOL"

#: the normative LEGACY-DERIVATIVE predicate (R2-3: "described, not given"
#: in v3): a record is legacy-derivative-shaped iff it is SYSTEM-authored
#: AND its evidence_ref carries the consolidation operation-id shape AND it
#: still carries a groupable identity (the pre-fix copied identity). Such
#: an identity is NEVER trusted as membership evidence.
def is_legacy_derivative(record: dict) -> bool:
    return (record.get("author") == "system"
            and str(record.get("evidence_ref", "")).startswith("consolidate:")
            and record.get("source_id") is not None)


def membership(record: dict, ledger: Optional[dict], op_state: str,
               local_origin: str):
    """record + ledger + operation state → membership evidence (R2-3).

    `record`: {"author": "user"|"system"|..., "origin", "source_id",
    "evidence_ref", "lineage": bool} — the provenance-shape fields the
    resolver consumes. `ledger`: None (no rows — legacy/imported/absent) or
    {"complete": bool, "contributor_identities": [Identity…]} — the 0014
    join, with the exact-set completeness verdict the store computes.
    `op_state`: the 0010 state that produced the record ("none" for
    ordinary host records). Returns an Identity (groupable membership),
    SHARED (the host-produced pool), or UNRESOLVED (fail-closed).

    The table, total:
    - ordinary host record, groupable identity → that identity (resolved).
    - ordinary host record, no groupable identity → SHARED (C3's floor —
      host-produced only).
    - legacy-derivative-shaped (the predicate above) → UNRESOLVED — its
      copied identity is never membership evidence, whatever it claims.
      This INCLUDES pre-feature OUTPUTS_DURABLE operations finalized by
      recovery: recovery cannot clear an already-written output (the
      reviewer's executed trace), so those outputs keep their stale copied
      identity and are caught HERE, by shape, not by recovery.
    - store-authored derivative (lineage/system-authored, identity cleared):
      ledger present AND complete AND all contributor identities groupable
      AND same resolved scope → that scope's Identity;
      contributors all non-groupable → SHARED (the pool's derivatives stay
      in the pool);
      mixed scopes / partial / absent ledger → UNRESOLVED.
    - op_state "generating" (an in-flight claim at read time) → the record
      is not yet a settled output; its membership is UNRESOLVED until
      finalization re-resolves it.
    - "abandoned" outputs do not exist (0010 rolls them back) — the state
      is listed for totality; a record claiming it is malformed → refuse.
    """
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
    own = Identity(record.get("origin"), record.get("source_id"))
    is_derivative = bool(record.get("lineage"))
    if not is_derivative:
        if own.groupable:
            return resolve(own, local_origin)
        return SHARED
    # store-authored derivative: membership travels through the ledger only
    if ledger is None or not ledger.get("complete"):
        return UNRESOLVED
    contribs = ledger.get("contributor_identities", [])
    if not contribs:
        return UNRESOLVED
    if all(not c.groupable for c in contribs):
        return SHARED
    if any(not c.groupable for c in contribs):
        return UNRESOLVED                      # mixed identified/unidentified
    scopes = {resolve(c, local_origin) for c in contribs}
    if len(scopes) == 1:
        return next(iter(scopes))
    return UNRESOLVED


# ---- the visibility decision ----------------------------------------------

DECISION_TABLE = {
    "OWN": (True, "own"),
    "SHARED": (True, "shared"),
    "CROSS_VISIBLE": (True, "third-party-shaped"),
    "CROSS_HIDDEN": (False, None),
    "UNRESOLVED": (False, None),
}


def classify(record_evidence, principal: Optional[Identity],
             policy: Optional[ScopePolicy], local_origin: str) -> str:
    """The §4a-ii decision function over the RESOLVER's output.

    `principal=None` is the UNSCOPED surface: everything is OWN —
    byte-identical to today, the migration invariant. **A principal WITHOUT
    a policy REFUSES (R2-2): feature-disabled (policy None) cannot honour a
    principal-bearing call and never silently becomes unscoped.** A
    CONFIGURED-EMPTY policy (no groups) is a valid state: the principal is
    ungrouped — own-identity records are OWN, the pool is SHARED, every
    other identified record is CROSS."""
    if principal is None:
        return "OWN"
    if policy is None:
        raise PolicyError(
            "a principal was supplied but no scope policy is configured — "
            "feature-disabled cannot honour a principal-bearing call; "
            "configure a policy (possibly empty) or call unscoped (R2-2)")
    if not principal.groupable:
        raise PolicyError(
            "a principal must carry a source_id — an absent source_id "
            "yields no groupable identity (0006 I13; R2-1)")
    if record_evidence == UNRESOLVED:
        return "UNRESOLVED"
    if record_evidence == SHARED:
        return "SHARED"
    if not isinstance(record_evidence, Identity):
        raise PolicyError(f"record evidence {record_evidence!r} is not an "
                          f"Identity / SHARED_POOL / UNRESOLVED")
    if not record_evidence.groupable:
        # the resolver never emits these for records; defensive totality
        return "SHARED"
    pg = _group_of(principal, policy, local_origin)
    rg = _group_of(record_evidence, policy, local_origin)
    if rg is None:
        if same_identity(record_evidence, principal, local_origin):
            return "OWN"
        return "CROSS_VISIBLE" if policy.cross_scope_visible else "CROSS_HIDDEN"
    if pg is not None and pg == rg:
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
    """M-2: after scope, within the visible set; narrow only. NOTE (R2-3):
    a `source_id` filter never matches a store-authored derivative — its
    identity is CLEARED and the ledger retains only a one-way digest; the
    filter operates on the record's own field, which is None."""
    out = records
    for k, v in filters.items():
        out = [r for r in out if r.get(k) is not None and str(r.get(k)) == v]
    return out
