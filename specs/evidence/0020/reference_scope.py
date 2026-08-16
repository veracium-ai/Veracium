"""specs/0020 §4a-ii — the NORMATIVE reference for the scope surface (v10).

PORTABLE AND PURE: no I/O, no store dependency. Two conforming
implementations must agree with this module on every input; the pinned
vectors live beside it in `vectors.json`, the SHIPPED HARNESS
(`vector_harness.py`) executes them, and 0020 V10 binds implementations to
both.

v11 (external round 9): (R9-1) `derive_absorbed_by` is the EXACT
reverse-link algorithm — canonical rows are DIRECT or REPARENTED, plain
flattened copies never; `prune_absorbed_record` models the retention
contract's prune-time reparenting; zero canonical rows → the export
omits the field (legacy path); >1 → ExportLinkageError. (R9-2) the
per-row op key is the INJECTIVE framed-digest form
(`import_row_op_key`) — the v10 colon-join collided over
delimiter-bearing ids. (R9-3) `plan_row_id` is THE ONE canonical
logical-row projection (every semantic field incl. canonical payload and
contributor type; `validate_row_plan` refuses contradictory rows —
flattened-without-ref, reparented-without-flattened); the closure walker
refuses marker-only flattened rows. (R9-5 lives in verify_package.)

v10 (external round 8): (R8-1) the closure is BY CONSTRUCTION on the
survivor's OWN row set (bin-b fixed the stale append-only phrasing this
header carried: accepted 0014 A10 makes the ledger
SURVIVOR-LIFETIME-KEYED — a record's rows drop with it, so the durable
object is the survivor's born-closed flattened set, never ledger
immortality), with the legacy note-walk as fallback and a DISCLOSED
delta (unavailable legacy contributors → UNRESOLVED where v9 read
own-scope). (R8-3) reconstruction emits COMPLETE rows (contributor
binding via the typed ref → evidence_ref_digest per the shipped
construction; the closed payload);
`plan_row_id` is the deterministic store-side identity.

v9 (external round 7): (R7-1) absorption evidence is TRANSITIVE —
`close_absorption_rows` is the normative read-side closure (a chain link
whose record is unavailable, or a cyclic linkage, yields None and the
caller MUST treat membership as UNRESOLVED); `membership`'s absorption
input contract is the CLOSED row set. (R7-2) note-grammar parsing is
REPLACED by id-set-anchored resolution: the LAST `absorbed_by:` tag
governs and is the only one that must resolve; candidates are matched
against the export's own id universe; zero or multiple candidates REFUSE
(the legacy carrier is genuinely ambiguous there — the structured
`absorbed_by_id` field is the normative carrier going forward, 0020
§4a-iii). Reconstruction runs PRE-COMMIT on the export file's records and
propagates digests transitively to every absorber. (R7-3) rows are fully
populated — the import operation mints ONE `op-<12hex>` op key and passes
it in. (R7-4) the registry snapshot stores PRIMITIVE (origin, source_id)
strings — no `Identity` instance is shared between the policy and the
snapshot, so leaf mutation cannot touch both.

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

#: R4-1/R5-2 — THE VALIDATOR-OWNED REGISTRY is the authority, not fields
#: on the object: `validate_policy` deposits an immutable canonical
#: snapshot here, keyed by the policy instance; `classify` consults the
#: REGISTERED snapshot and refuses on any divergence from the object's
#: current visible state. Re-signing the caller-visible `seal` after an
#: `object.__setattr__` flip therefore achieves nothing (the round-5
#: executed attack): the registry comparison catches the flipped field
#: regardless of the seal's value. THE THREAT CLAIM, NARROWED HONESTLY
#: (R5-2): in-process Python cannot defend against a caller that rewrites
#: THIS MODULE's own state (the registry, the nonce, the functions) — the
#: construction is accidental-misuse-proof and forgery-evident, not
#: adversarial-caller-proof, consistent with C2's honest-host posture; S3
#: owns the adversarial boundary.
import secrets as _secrets
import weakref as _weakref
_SEAL_NONCE = _secrets.token_bytes(32)
_REGISTRY: "dict" = _weakref.WeakValueDictionary() and {}
_REGISTRY = _weakref.WeakKeyDictionary()


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


@dataclass(frozen=True, eq=False)   # identity hash/eq — the registry key
class ScopePolicy:
    """REGISTRY-AUTHORITATIVE canonical form (R5-2; wording fixed R6-3;
    made LITERAL by R7-4): `validate_policy` deposits a recursively-
    immutable snapshot in the validator-owned registry — immutable down
    to PRIMITIVE string leaves, not just immutable containers around
    shared `Identity` instances (the v8 shape the reviewer mutated
    through) — and `classify` refuses on ANY divergence between this
    object's visible state and that snapshot; the `seal` field is
    retained as tamper-evidence but is NOT the authority and is NOT
    recomputed at consumption. Direct construction with raw shapes
    RAISES here; everything deeper is the registry's job."""
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
    # the validator-owned snapshot (R5-2), RECURSIVELY IMMUTABLE — NOW
    # LITERALLY (R7-4: v8 froze the CONTAINERS but retained the same
    # `Identity` instances the policy exposes, so `object.__setattr__` on a
    # member mutated both references; the snapshot holds only PRIMITIVE
    # strings/bools/frozensets from here down — no shared leaf exists)
    _REGISTRY[pol] = (_prim_groups(frozen_groups),
                      cross_scope_visible,
                      tuple(sorted((k, frozenset(v))
                                   for k, v in frozen_digests.items())),
                      pol.seal)
    return pol


def _prim_groups(groups) -> tuple:
    """The snapshot projection of a groups mapping: every Identity leaf
    decomposed to its (origin, source_id) PRIMITIVE strings (R7-4)."""
    return tuple(sorted(
        (name, tuple((m.origin, m.source_id) for m in members))
        for name, members in groups.items()))


def _revalidate(policy: ScopePolicy, local_origin: str) -> None:
    """Consumption-time revalidation (R3-1/R4-1; wording corrected R7-4 —
    the seal is COMPARED against the registered value, never RECOMPUTED
    here): shape checks, then the DIGEST MAP is recomputed from the
    policy's current groups (an inconsistent map or mutated backing dict
    yields a mismatch and refuses), then the policy's visible state —
    PRIMITIVE-projected, so a mutated Identity leaf projects differently —
    is compared field-for-field against the validator-owned registry
    snapshot. The registry, not the seal, is the authority; the seal
    comparison is retained as tamper-evidence only."""
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
    reg = _REGISTRY.get(policy)
    if reg is None:
        raise PolicyError(
            "the policy is not in the validator's registry — constructed "
            "outside validate_policy (R4-1/R5-2)")
    reg_groups, reg_xv, reg_digs, reg_seal = reg
    if (policy.cross_scope_visible is not reg_xv
            or _prim_groups(policy.groups) != reg_groups
            or tuple(sorted((k, frozenset(v))
                            for k, v in policy.group_digests.items()))
            != reg_digs
            or policy.seal != reg_seal):
        raise PolicyError(
            "the policy's visible state diverges from the validator-owned "
            "snapshot — mutated after validation; RE-SIGNING DOES NOT HELP "
            "(the round-5 executed attack): the registry, not the seal, is "
            "the authority (R5-2)")


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


def close_absorption_rows(survivor_id: str, ledger_rows: dict,
                          legacy_links: Optional[dict] = None,
                          legacy_digests: Optional[dict] = None
                          ) -> Optional[list]:
    """0020 §4a-iii v10 (external R7-1, REBUILT under R8-1) — the
    TRANSITIVE CLOSURE of absorption evidence, resident in the LEDGER.

    R8-1's executed break of the v9 form: the v9 walk chained through
    free-text `absorbed_by:` notes on the ABSORBED RECORDS — but a pruned
    intermediate takes its note (the only link) with it, and the walk then
    looked complete while an ancestor's foreign digest was gone.

    THE DURABILITY MODEL (corrected by our own found-in-fix pass before
    round 9 — accepted 0014 A10 makes the ledger SURVIVOR-LIFETIME-KEYED,
    not append-only: `_drop_contributions_for_survivor` drops a record's
    rows when the record is deleted, so "absence in the ledger = leaf"
    is UNSOUND): the durable object is the SURVIVOR'S OWN ROW SET, which
    lives exactly as long as the survivor does. Post-amendment writes are
    BORN CLOSED (0021 §4c flattening + the typed `contributor_ref`, one
    rider), so pruning an intermediate touches only rows keyed to IT —
    the survivor's flattened ancestry is untouched. The closure is BY
    CONSTRUCTION, not by walk.

    `ledger_rows`: {survivor_id: [rows]} — the ledger projection; a row
    may carry "contributor_ref" (typed, post-amendment) and the payload
    marker "flattened". `legacy_links`/`legacy_digests`: the
    note-derived fallback for PRE-AMENDMENT rows — {absorber: (absorbed
    ids)} and {record_id: identity digest or None}, both derivable only
    while the absorbed RECORDS still exist.

    The layered rule, per node:
    - Rows WITH a typed ref are closed by the write invariant (0021 W14).
      Where the contributor's own rows are STILL PRESENT, they are
      opportunistically VERIFIED: its digests must appear among the
      node's row digests — a mismatch is corrupt (None). Where its rows
      are absent (A10 prune), no verification is possible and none is
      claimed: the flattened set stands on the write invariant. (THE
      DISCLOSED RESIDUAL: a writer that violated W14 *and* a subsequent
      prune is undetectable read-side — W14 is the write-side gate.)
    - Ref-less rows are LEGACY: the note-derived links must account for
      them — the linked absorbed records' digest MULTISET must exactly
      match the unattributed row digests, and each linked prior is
      walked. A pruned legacy contributor (R8-1's cell), an unknown
      linked digest, a mismatched multiset, one absorbed id under two
      absorbers, or a cyclic path returns **None — and None MUST be read
      as UNRESOLVED**. THE DISCLOSED BEHAVIOUR DELTA: legacy absorption
      survivors whose contributors are unavailable are UNRESOLVED where
      the single-hop read called them own-scope — a fail-closed
      widening, remediable by re-derivation.

    The stated residual is UNCHANGED: absorptions predating the 0014
    ledger left no rows AND no links — their survivors resolve by own
    identity (0021 §4d)."""
    legacy_links = legacy_links or {}
    legacy_digests = legacy_digests or {}
    absorber_of: dict = {}                 # one-absorber rule, global
    out: list = []
    visited = set()

    def walk(node, path, verify_only=False):
        if node in path:
            return False                   # cyclic path — corrupt
        if node in visited:
            return True                    # DAG shortcut revisit — done
        visited.add(node)
        rows = ledger_rows.get(node, [])
        node_digs = {r.get("identity_digest") for r in rows
                     if r.get("site") in _MEMBERSHIP_SITES}
        if not verify_only:
            out.extend(rows)
        unattributed = []
        for r in rows:
            if r.get("site") not in _MEMBERSHIP_SITES:
                continue
            ref = r.get("contributor_ref")
            payload = r.get("payload") or {}
            if payload == {"closure": "incomplete"}:
                continue                   # R10-2: the marker's None digest
                                           # fails membership closed; it is
                                           # never a link and never walked
            if payload.get("flattened"):
                if ref is None:
                    return False           # R9-3: a marker-only row would
                                           # bypass BOTH accounting paths
                continue                   # digest counted; subtree covered
            if ref is not None:
                # direct rows and REPARENTED links (R10-1: reparenting is
                # an INSERTED scope-attribution row, never a mutation).
                # Closed by the write invariant (0021 W14/§4c: flattening
                # and the ref land together). OPPORTUNISTIC verification
                # only — under accepted 0014 A10 a pruned contributor's
                # rows are legitimately GONE, so absence proves nothing
                # and fails nothing; presence is checked.
                if absorber_of.setdefault(ref, node) != node:
                    return False           # two absorbers — corrupt
                for cr in ledger_rows.get(ref, []):
                    if cr.get("site") in _MEMBERSHIP_SITES \
                            and cr.get("identity_digest") not in node_digs:
                        return False       # flattening incomplete — corrupt
                if not walk(ref, path | {node}, verify_only=True):
                    return False
            else:
                unattributed.append(r.get("identity_digest"))
        if unattributed:
            linked = legacy_links.get(node)
            if not linked:
                return False               # R8-1: the pruned-legacy cell
            if any(x not in legacy_digests for x in linked):
                return False
            if sorted(legacy_digests[x] or "" for x in linked) != \
                    sorted(d or "" for d in unattributed):
                return False               # multiset mismatch — unaccounted
            for prior in linked:
                if absorber_of.setdefault(prior, node) != node:
                    return False
                if not walk(prior, path | {node}):
                    return False
        return True

    return out if walk(survivor_id, frozenset()) else None


def membership(record: dict, rows: Optional[list], op_state: str,
               local_origin: str, *, expected_contributors: Optional[int] = None):
    """record + REAL ledger rows + operation state → membership evidence:
    a DIGEST (str), SHARED, or UNRESOLVED (fail-closed).

    `record`: {"author", "origin", "source_id", "evidence_ref",
    "lineage": bool} — the provenance-shape fields. `rows`: the record's
    `ContributionRecord`s AS SHIPPED — [{"site": "absorption" |
    "imported-absorption" | "consolidation" (the round-8 bin-(b) fix:
    the imported site was missing from this enumeration),
    "identity_digest": str|None, "op_key": str|None, and optionally the
    0014-amendment fields "contributor_ref"/"evidence_ref_digest"/
    "payload"}] — keyed by survivor_id (None/[] = no rows). **For
    absorption survivors this MUST be the transitively CLOSED set (R7-1):
    either the write path flattened ancestors onto the survivor (0021
    §4c, post-0021 stores) or the caller assembled it via
    `close_absorption_rows`; a None closure is UNRESOLVED before this
    function is ever called.** `expected_contributors`: the
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
        ab = [r for r in rows
              if r.get("site") in _MEMBERSHIP_SITES]
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


# ---- import-time absorption reconstruction (R5-1; REBUILT v9 / R7-2) --------


class ImportLinkageError(PolicyError):
    """R6-1: an import whose absorption linkage cannot be reconstructed
    unambiguously REFUSES WHOLE — the 0009/0005 whole-import posture,
    and (R7-2) the refusal happens PRE-COMMIT: reconstruction runs on the
    export file's records BEFORE any destination write, so a refused
    import leaves the destination byte-identical. A file carrying an
    absorbed_duplicate record with missing, unresolvable, or AMBIGUOUS
    linkage has unreconstructable absorption history; that is an
    integrity problem, not a soft cell."""


def _resolve_winner(record: dict, file_ids: set) -> str:
    """R7-2 — the DECIDABLE linkage rule, replacing the v8 regex (which
    treated note punctuation as framing while `Edge.id` permits exactly
    those characters, rejecting valid native exports).

    1. STRUCTURED FIRST: a record carrying `absorbed_by_id` (the FORMAT-7
       carrier 0020 §4a-iii rules normative) uses it verbatim — no note
       parsing. It must name a record in the file.
    2. LEGACY NOTE: the LAST `absorbed_by:` occurrence governs and is the
       ONLY tag that must resolve (v8 demanded earlier incidental tags
       resolve too, contradicting its own last-tag rule — the reviewer's
       third executed case). The tag's value is matched against the
       export's OWN id universe: candidate winners are every file id W
       where the remainder equals W, or starts with W + " (restated as "
       or W + "; " (the shipped append framings). EXACTLY ONE candidate
       resolves; ZERO refuses (missing/unresolvable); MORE THAN ONE
       refuses (the legacy carrier is genuinely ambiguous there — ids may
       embed the framing and each other, so no grammar can decide; the
       structured field is the fix, refusal is the fallback)."""
    rid = record.get("id")
    structured = record.get("absorbed_by_id")
    if structured is not None:
        if structured not in file_ids:
            raise ImportLinkageError(
                f"absorbed_duplicate record {rid!r} carries structured "
                f"absorbed_by_id {structured!r} naming no record in the "
                f"file — unresolvable linkage; the import REFUSES")
        return structured
    note = record.get("note") or ""
    idx = note.rfind("absorbed_by:")
    if idx < 0:
        raise ImportLinkageError(
            f"absorbed_duplicate record {rid!r} carries no absorbed_by "
            f"linkage — unreconstructable absorption history; the import "
            f"REFUSES (R6-1)")
    rest = note[idx + len("absorbed_by:"):]
    candidates = [w for w in file_ids
                  if isinstance(w, str)
                  and (rest == w or rest.startswith(w + " (restated as ")
                       or rest.startswith(w + "; "))]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise ImportLinkageError(
            f"absorbed_duplicate record {rid!r} names a winner resolving "
            f"to no record in the file — unresolvable linkage; the import "
            f"REFUSES (R6-1)")
    raise ImportLinkageError(
        f"absorbed_duplicate record {rid!r}'s linkage matches "
        f"{len(candidates)} file ids — the legacy note carrier is "
        f"AMBIGUOUS here; the import REFUSES (R7-2; re-export under the "
        f"structured absorbed_by_id carrier)")


#: the shipped evidence-ref digest construction, mirrored EXACTLY
#: (contribution.py — 0014 §4a; R8-3's contributor binding needs it)
_EVID_DOMAIN = b"veracium.evidence-ref.v1"


def evidence_digest_of(origin: Optional[str], evidence_ref: Optional[str],
                       local_origin: str) -> Optional[str]:
    """NULL iff evidence_ref is empty/absent (0014 §4a); origin resolves
    to the local singleton first (0006 §4 rule 6)."""
    if not evidence_ref:
        return None
    o = resolve(Identity(origin, None), local_origin).origin
    payload = (_EVID_DOMAIN + _framed(o.encode("utf-8"))
               + _framed(evidence_ref.encode("utf-8")))
    return hashlib.sha256(payload).hexdigest()


def canonical_payload(payload: dict) -> str:
    """The ONE canonical payload form (R9-3): sorted keys, no whitespace —
    the projection the row identity digests."""
    import json as _json
    if not isinstance(payload, dict):
        raise PolicyError(f"payload must be a mapping, got {payload!r}")
    return _json.dumps(payload, sort_keys=True, separators=(",", ":"))


#: R10-1 — the DEDICATED site for every DERIVED attribution row. Accepted
#: 0014's native `absorption` payload is the closed {base, contributor}
#: schema and its rows are INSERT-ONLY; v11's flattened/reparented payload
#: classes were never legal there, and v11's prune UPDATED a row. The new
#: site keeps every accepted schema untouched: flattened ancestor copies,
#: reparented canonical links, and closure-incompleteness markers all live
#: at `scope-attribution` with their OWN closed payload vocabulary, and
#: reparenting is an INSERTION of a new row (the old flattened copy stays,
#: immutable and non-canonical) — never a mutation. The 0014 exact-set
#: partition becomes STRUCTURAL: it keys on the native site, so
#: attribution rows can never perturb it.
SITE_ATTRIBUTION = "scope-attribution"
_PLAN_SITES = ("imported-absorption", SITE_ATTRIBUTION)
_MEMBERSHIP_SITES = ("absorption", "imported-absorption", SITE_ATTRIBUTION)

#: the CLOSED payload vocabulary, per plan site (R10-3: exact shapes —
#: unknown keys refuse, marker values must be the literal True)
_PAYLOAD_SHAPES = {
    "imported-absorption": ({"reconstructed": True},),
    SITE_ATTRIBUTION: ({"flattened": True},
                       {"flattened": True, "reconstructed": True},
                       "REPARENTED",          # {"reparented_from": <id>}
                       {"closure": "incomplete"}),
}


def validate_row_plan(row: dict) -> None:
    """R9-3's cross-field validator, made TOTAL under R10-3 (the reviewer
    fed it malformed evidence digests, a missing direct ref, an alien
    contributor_type, and an undeclared payload key — all accepted).
    Governs every row the AMENDED primitive writes (plan sites); native
    `absorption` rows are the shipped store's accepted contract and are
    not written through this path. Every field, strictly:
    - site: the closed plan-site set;
    - identity_digest / evidence_ref_digest: None or 64-hex, each;
    - contributor_type: the closed set {"edge"};
    - contributor_ref: REQUIRED on every plan row (direct imported links,
      flattened copies, reparented links, and markers all NAME a
      contributor);
    - payload: EXACTLY one of the site's closed shapes — unknown keys
      refuse; boolean markers must be the literal True; reparented_from
      must be a non-empty string; a marker row's identity_digest must be
      None (it asserts missing evidence, never an identity)."""
    if row.get("site") not in _PLAN_SITES:
        raise PolicyError(f"row site {row.get('site')!r} outside the "
                          f"closed plan-site set {_PLAN_SITES}")
    for field in ("identity_digest", "evidence_ref_digest"):
        d = row.get(field)
        if d is not None and not (isinstance(d, str)
                                  and re.fullmatch(r"[0-9a-f]{64}", d)):
            raise PolicyError(f"{field} {d!r} is neither None nor a "
                              f"64-hex digest")
    if row.get("contributor_type", "edge") != "edge":
        raise PolicyError(f"contributor_type {row.get('contributor_type')!r} "
                          f"outside the closed set {{'edge'}}")
    if not (isinstance(row.get("contributor_ref"), str)
            and row.get("contributor_ref")):
        raise PolicyError("every plan row NAMES its contributor — "
                          "contributor_ref must be a non-empty string "
                          "(R10-3: the missing-direct-ref cell)")
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise PolicyError("row payload must be a mapping")
    shapes = _PAYLOAD_SHAPES[row["site"]]
    ok = False
    for shape in shapes:
        if shape == "REPARENTED":
            if (set(payload) == {"reparented_from"}
                    and isinstance(payload["reparented_from"], str)
                    and payload["reparented_from"]):
                ok = True
                break
        elif payload == shape and all(
                type(payload[k]) is type(shape[k]) for k in shape):
            # exact: keys AND literal values AND types — dict equality
            # alone admits 1 == True (R10-3's truthy-marker cell)
            ok = True
            break
    if not ok:
        raise PolicyError(
            f"payload {payload!r} is not one of site {row['site']!r}'s "
            f"closed shapes (R10-3: exact match — unknown keys, truthy "
            f"non-True markers, and undeclared classes all refuse)")
    if payload == {"closure": "incomplete"} \
            and row.get("identity_digest") is not None:
        raise PolicyError("a closure-incompleteness marker asserts MISSING "
                          "evidence — identity_digest must be None")


def plan_row_id(user_id: str, survivor_type: str, survivor_id: str,
                row: dict) -> str:
    """The 0009 amendment's DETERMINISTIC row id (R8-3; REBUILT under
    R9-3 as THE ONE canonical logical-row projection): a framed digest
    over EVERY semantic field — user, survivor coordinates, site,
    identity digest, evidence digest, contributor type AND ref, and the
    CANONICAL PAYLOAD (payload is semantic: it distinguishes a direct
    from a flattened history — the reviewer executed the drift). Excluded
    are ONLY the genuinely operational fields: the re-minted op key and
    the commit timestamp. Idempotent-equality has exactly ONE definition:
    plan_row_id set equality (the v10 three-field multiset phrasing is
    WITHDRAWN). The cross-field validator runs first — a contradictory
    row never projects."""
    validate_row_plan(row)
    parts = [b"veracium.import-contribution-row.v2"]
    for v in (user_id, survivor_type, survivor_id, row.get("site"),
              row.get("identity_digest"),
              row.get("evidence_ref_digest"),
              row.get("contributor_type", "edge"),
              row.get("contributor_ref"),
              canonical_payload(row.get("payload"))):
        parts.append(_framed(b"\x00" if v is None
                             else b"\x01" + str(v).encode("utf-8")))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def row_op_key(op: str, site: str, survivor_id: str,
               contributor_ref: str) -> str:
    """The PER-ROW op key, INJECTIVE form (R9-2 — the v10 colon-join was
    not injective over unrestricted ids: survivor 'a:b'+'c' collided with
    'a'+'b:c'; the reviewer raised the IntegrityError). The prefix fields
    are colon-free by construction (`op-<12hex>` + the site token, both
    from closed colon-free alphabets); the pair of unrestricted ids is
    FRAMED and domain-separated into one fixed-width digest — injective
    up to SHA-256, and the framing makes the pre-image encoding injective
    outright. R10-1 generalized the site token: import ops key
    imported-absorption rows AND scope-attribution copies; prune ops key
    scope-attribution reparented/marker rows."""
    if not _OP_ID.match(op or ""):
        raise PolicyError(f"op must be op-<12hex>, got {op!r}")
    if site not in _PLAN_SITES:
        raise PolicyError(f"op-key site token {site!r} outside {_PLAN_SITES}")
    h = hashlib.sha256(b"veracium.import-row-op-key.v1"
                       + _framed(survivor_id.encode("utf-8"))
                       + _framed(contributor_ref.encode("utf-8"))
                       ).hexdigest()
    return f"{op}:{site}:{h}"


def import_row_op_key(import_op: str, survivor_id: str,
                      contributor_ref: str) -> str:
    """The imported-absorption specialization of `row_op_key`."""
    return row_op_key(import_op, "imported-absorption", survivor_id,
                      contributor_ref)


class ExportLinkageError(PolicyError):
    """R9-1: a contributor with MORE THAN ONE canonical absorber row is
    corrupt ledger state — the exporter REFUSES to materialise a
    structured link from it (a corrupt store must not become a portable
    file that looks clean)."""


def _is_canonical(row: dict) -> bool:
    """R10-1/R10-2 — CANONICAL means: a DIRECT link (a native
    `absorption` or `imported-absorption` row) or a REPARENTED link (a
    scope-attribution row whose payload is the reparented class). Plain
    flattened copies are never canonical, and NEITHER is the
    closure-incompleteness marker (R10-2's executed launder: the v11
    predicate keyed only on `flattened`, so the marker — non-flattened —
    counted as canonical and materialised a clean absorbed_by_id from a
    detected W14 violation)."""
    p = row.get("payload") or {}
    site = row.get("site")
    if site in ("absorption", "imported-absorption"):
        return True
    if site == SITE_ATTRIBUTION:
        return set(p) == {"reparented_from"}
    return False


def derive_absorbed_by(contributor_id: str, ledger_rows: dict):
    """The EXACT reverse-link algorithm (R9-1; the canonical predicate
    rebuilt under R10-1/R10-2 — see `_is_canonical`).

    Returns the unique canonical absorber's survivor id; None when no
    canonical row exists (the exporter OMITS `absorbed_by_id` and the
    record travels as legacy — the import-side note rule governs,
    fail-closed on ambiguity; a contributor whose only trace is the
    incompleteness marker lands HERE, so a detected W14 violation is
    never laundered into portable linkage); raises ExportLinkageError on
    >1 (corrupt — the export refuses)."""
    hits = []
    for survivor, rows in ledger_rows.items():
        for r in rows:
            if r.get("contributor_ref") == contributor_id \
                    and _is_canonical(r):
                hits.append(survivor)
    if not hits:
        return None
    if len(hits) > 1:
        raise ExportLinkageError(
            f"contributor {contributor_id!r} has {len(hits)} canonical "
            f"absorber rows ({sorted(set(hits))}) — corrupt linkage; the "
            f"export REFUSES (R9-1)")
    return hits[0]


def prune_absorbed_record(record_id: str, ledger_rows: dict,
                          *, prune_op: str) -> dict:
    """The RETENTION CONTRACT's prune step, modelled (R8-1/R9-1; made
    INSERT-ONLY under R10-1 — accepted 0014 says a ledger row is inserted
    and never updated or replaced, and v11's payload mutation violated
    that; the v11 SQL harness even ran a raw UPDATE to demonstrate it,
    which was proof-by-bypass).

    What a compliant future prune capability MUST do BEFORE the A10
    row-drop: for every CANONICAL row on the pruned record with
    contributor X, INSERT a NEW scope-attribution row on the pruned
    record's own canonical absorber S — payload
    `{"reparented_from": <pruned id>}`, X's identity/evidence digests
    carried from the source row, the prune operation's injective per-row
    op key — making it X's new canonical reverse link. The absorber's
    existing flattened copy of X is UNTOUCHED (immutable, and
    non-canonical by class). Where the absorber lacks even the flattened
    copy (a W14 violation surfacing at prune time), the inserted row is
    the closure-incompleteness MARKER instead (identity None, payload
    {"closure": "incomplete"} — never canonical, never exported; the
    resolver fails it closed). Then the pruned record's own row set
    drops (A10). Every inserted row passes `validate_row_plan`.

    Pruning a record with NO canonical absorber just drops its rows.
    Returns the new ledger_rows mapping; inputs are never mutated."""
    if not _OP_ID.match(prune_op or ""):
        raise PolicyError(f"prune_op must be op-<12hex>, got {prune_op!r}")
    out = {k: [dict(r, payload=dict(r.get("payload") or {}))
               for r in v] for k, v in ledger_rows.items()}
    absorber = derive_absorbed_by(record_id, out)
    if absorber is not None:
        for r in out.get(record_id, []):
            if not _is_canonical(r):
                continue
            x = r.get("contributor_ref")
            if x is None:
                continue                        # legacy row — nothing typed
            has_copy = any(
                t.get("contributor_ref") == x
                and (t.get("payload") or {}).get("flattened")
                for t in out.get(absorber, []))
            new = {"site": SITE_ATTRIBUTION,
                   "identity_digest": (r.get("identity_digest")
                                       if has_copy else None),
                   "evidence_ref_digest": (r.get("evidence_ref_digest")
                                           if has_copy else None),
                   "contributor_ref": x, "contributor_type": "edge",
                   "op_key": row_op_key(prune_op, SITE_ATTRIBUTION,
                                        absorber, x),
                   "payload": ({"reparented_from": record_id} if has_copy
                               else {"closure": "incomplete"})}
            validate_row_plan(new)
            out.setdefault(absorber, []).append(new)
    out.pop(record_id, None)                    # the A10 drop
    return out


def reconstruct_absorption_rows(export_records: list, local_origin: str,
                                *, id_remap: Optional[dict] = None,
                                import_op: str):
    """The 0020 §4a-iii import-time RECONSTRUCTION rule (v10 — external
    R8-3 completed the row construction the v9 form left partial).

    PRE-COMMIT (R7-2): `export_records` are the records AS PARSED FROM THE
    EXPORT FILE — original ids, before any destination write. Winner
    resolution happens in the file's own id universe (`_resolve_winner`);
    `id_remap` (the importer's old→new table when a `user_id=` remap runs)
    translates OUTPUT keys and refs. A raised `ImportLinkageError` means
    the importer never writes — destination unchanged.

    COMPLETE ROWS (R8-3): every emitted row carries site, identity_digest,
    **contributor_ref** (the post-remap absorbed record id — the typed
    link R8-1 requires and the contributor binding that determines WHICH
    exported record supplies the evidence digest), **evidence_ref_digest**
    (the shipped construction over the absorbed record's resolved origin +
    evidence_ref), **payload** ({"reconstructed": true}; transitive copies
    add "flattened": true — counted, never re-walked), and a PER-ROW
    **op_key** in the INJECTIVE framed-digest form (`import_row_op_key`,
    R9-2 — v10's plain colon-join collided over delimiter-bearing ids;
    v9's one-key-on-every-row violated the accepted UNIQUE partial index;
    both corrected). `import_op` is the ONE `op-<12hex>` id the import
    operation mints. The store-side plan id is `plan_row_id`.

    TRANSITIVE (R7-1): each absorbed record's digest propagates to its
    direct winner AND every transitive absorber — reconstructed sets are
    BORN CLOSED; cyclic winner chains refuse.

    These rows are ATTRIBUTION evidence for scope membership ONLY — they
    are NOT 0014 §4a absorption payloads and provide NO reversal (the
    pre-inheritance base image is not in the export and cannot be
    inferred; stated as the imported-absorption site's honest limit —
    R6-2)."""
    if not _OP_ID.match(import_op or ""):
        raise PolicyError(f"import_op must be the minted op-<12hex> "
                          f"operation id (R7-3/R8-3), got {import_op!r}")
    id_remap = id_remap or {}
    file_ids = {r.get("id") for r in export_records}
    winner_of: dict = {}
    for r in export_records:
        if r.get("invalidation_reason") == "absorbed_duplicate":
            winner_of[r.get("id")] = _resolve_winner(r, file_ids)
        elif r.get("absorbed_by_id") is not None:
            raise ImportLinkageError(
                f"record {r.get('id')!r} carries absorbed_by_id but is not "
                f"absorbed_duplicate — a contradictory file; the import "
                f"REFUSES (fail-closed)")
    out: dict = {}
    for r in export_records:
        rid = r.get("id")
        if rid not in winner_of:
            continue
        d = digest_of(Identity(r.get("origin"), r.get("source_id")),
                      local_origin)
        ev = evidence_digest_of(r.get("origin"), r.get("evidence_ref"),
                                local_origin)
        cref = id_remap.get(rid, rid)
        # propagate to the direct winner and every transitive absorber —
        # DIRECT links land at imported-absorption; transitive copies at
        # scope-attribution (R10-1: the derived-row site, so the imported
        # marker vocabulary stays exactly {"reconstructed": true})
        hop, visited, direct = winner_of[rid], {rid}, True
        while True:
            if hop in visited:
                raise ImportLinkageError(
                    f"absorption linkage from {rid!r} is CYCLIC at "
                    f"{hop!r} — corrupt history; the import REFUSES (R7-1)")
            visited.add(hop)
            surv = id_remap.get(hop, hop)
            site = "imported-absorption" if direct else SITE_ATTRIBUTION
            payload = ({"reconstructed": True} if direct
                       else {"flattened": True, "reconstructed": True})
            out.setdefault(surv, []).append(
                {"site": site, "identity_digest": d,
                 "evidence_ref_digest": ev, "contributor_ref": cref,
                 "contributor_type": "edge",
                 "op_key": row_op_key(import_op, site, surv, cref),
                 "payload": payload})
            if hop not in winner_of:
                break
            hop = winner_of[hop]
            direct = False
    return out


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
