"""specs/0020 §4a-ii / §4a-iii / §4e — THE NORMATIVE SCOPE CORE, in
production.

This module is the PRODUCTION PORT of the normative reference
(`specs/evidence/0020/reference_scope.py` — production never imports
specs/). Semantics are IDENTICAL to the reference on every input, and
0020 V10 binds that claim MECHANICALLY: the 128 pinned vectors in
`specs/evidence/0020/vectors.json` are executed against THIS module by
`tests/test_0020_scope_vectors.py`, reproducing the shipped harness's
per-kind dispatch (the harness itself executes them against the
reference; both must pass, on the same file).

The pieces the D2 train already ported live in `scope_linkage` — the
write/linkage half (sites, payload vocabulary, `plan_row_id`,
`row_op_key`/`native_row_op_key`, `construct_plan_row`,
`reconstruct_absorption_rows`, `derive_absorbed_by`, `_is_canonical`,
`identity_digest_of`, `evidence_digest_of`, `canonical_payload`). They
are IMPORTED here, never re-derived; this module re-exports them so
`veracium.scope` is the one scope surface a consumer needs.

What this module adds (the READ half):

- `Identity` — the `(origin, source_id)` pair with the SHIPPED 512-char
  Provenance bounds and 0006 I13's groupability rule (an absent
  `source_id` yields NO groupable identity, REGARDLESS of origin);
  `resolve` (0006 I9: absent origin → the local singleton, uniformly);
  `digest_of` / `same_identity` in DIGEST SPACE. The digest is the
  SHIPPED `source_identity_digest` reached through
  `scope_linkage.identity_digest_of` — ONE function, not a mirror, so
  policy-side and store-side digests are equal by sharing code.
- `ScopePolicy` + `validate_policy` — REGISTRY-AUTHORITATIVE (0020
  §4a-ii, external R5-2/R7-4): the validator deposits a recursively
  immutable snapshot whose LEAVES ARE PRIMITIVE `(origin, source_id)`
  strings in a validator-owned `WeakKeyDictionary`, and `_revalidate`
  refuses on ANY divergence between the policy's visible state and that
  snapshot. The `seal` is retained as tamper-evidence and is COMPARED
  against the registered value — never recomputed at consumption, and
  never the authority, so RE-SIGNING A FLIPPED FIELD DOES NOT HELP.
  THE THREAT CLAIM, NARROWED HONESTLY: in-process Python cannot defend
  against a caller that rewrites THIS MODULE's own state (the registry,
  the nonce, the functions); the construction is accidental-misuse-proof
  and forgery-evident, not adversarial-caller-proof (0020 C2; S3 owns
  the adversarial boundary).
- `close_absorption_rows` — the TRANSITIVE CLOSURE of absorption
  evidence (§4a-iii), layered: typed `contributor_ref` rows are closed
  by the write invariant with OPPORTUNISTIC verification where the
  contributor's own rows are still present; ref-less LEGACY rows must be
  accounted by the note-derived links' digest MULTISET. **None means
  UNRESOLVED** — unwalkable, cyclic, mismatched, or two-absorber linkage
  all land there, and the caller MUST fail closed before `membership`
  runs.
- `prune_absorbed_record` — the retention contract's prune step,
  modelled INSERT-ONLY (a new reparented scope-attribution row, or the
  closure-incompleteness marker where the absorber lacks even the
  flattened copy; then the 0014 A10 row-drop).
- `membership` — the TOTAL record→evidence table over REAL
  `ContributionRecord` shapes and the 0010 operation states.
- `classify` / `decide` / `DECISION_TABLE` — the visibility decision,
  in digest space.
- `validate_filters` / `apply_filters` — the CLOSED §4e grammar.

Errors are ONE class: `ScopeError` (the production name), re-exported
here as `PolicyError` too so a consumer written against the reference's
name catches the same object.
"""

from __future__ import annotations

import hashlib
import secrets as _secrets
import weakref as _weakref
from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional

from .scope_linkage import (SITE_ATTRIBUTION, ExportLinkageError,
                            ImportLinkageError, ScopeError, _framed,
                            _HEX64, _is_canonical, _OP_ID, canonical_payload,
                            construct_plan_row, derive_absorbed_by,
                            evidence_digest_of, identity_digest_of,
                            import_row_op_key, native_row_op_key,
                            plan_row_id, reconstruct_absorption_rows,
                            row_op_key, validate_row_plan,
                            MEMBERSHIP_SITES)

#: the reference's error name, bound to THE SAME class (see module doc)
PolicyError = ScopeError

#: the CLOSED §4e filter field set
VALID_FILTER_FIELDS = ("subject", "relation", "author_of_evidence",
                       "source_id", "volatility")
#: the closed 0010 operation-state set the resolver is total over
OP_STATES = ("none", "generating", "outputs_durable", "finalized",
             "abandoned")
#: the shipped Provenance field bounds
IDENTITY_MAX = 512

#: the reserved SHARED-POOL result key: digests are 64 hex chars, so a
#: colon-bearing literal can never collide with one (R3-4)
SHARED_POOL_KEY = "pool:unidentified"

UNRESOLVED = "UNRESOLVED"
SHARED = "SHARED_POOL"

__all__ = [
    "DECISION_TABLE", "ExportLinkageError", "IDENTITY_MAX", "Identity",
    "ImportLinkageError", "OP_STATES", "PolicyError", "SHARED",
    "SHARED_POOL_KEY", "SITE_ATTRIBUTION", "ScopeError", "ScopePolicy",
    "UNRESOLVED", "VALID_FILTER_FIELDS", "apply_filters",
    "canonical_payload", "classify", "close_absorption_rows",
    "construct_plan_row", "decide", "derive_absorbed_by", "digest_of",
    "evidence_digest_of", "identity_digest_of", "import_row_op_key",
    "is_legacy_derivative", "membership", "native_row_op_key",
    "plan_row_id", "prune_absorbed_record", "reconstruct_absorption_rows",
    "resolve", "row_op_key", "same_identity", "validate_filters",
    "validate_policy", "validate_row_plan",
]


# ---- Identity --------------------------------------------------------------

@dataclass(frozen=True)
class Identity:
    """The `(origin, source_id)` pair — 0006's namespacing identity,
    verbatim; strict-typed with the SHIPPED bounds (non-empty, ≤512
    chars — the Provenance field caps)."""

    origin: Optional[str]
    source_id: Optional[str]

    def __post_init__(self):
        for f in (self.origin, self.source_id):
            if f is not None and (not isinstance(f, str)
                                  or not 1 <= len(f) <= IDENTITY_MAX):
                raise ScopeError(
                    f"identity field must be a 1..{IDENTITY_MAX}-char string "
                    f"or None (the shipped Provenance bounds), got {f!r}")

    @property
    def groupable(self) -> bool:
        """0006 I13: an absent `source_id` yields NO groupable identity —
        REGARDLESS of origin."""
        return self.source_id is not None


def resolve(identity: Identity, local_origin: str) -> Identity:
    """0006 I9: absent origin → the local singleton, UNIFORMLY."""
    if not isinstance(local_origin, str) or not local_origin:
        raise ScopeError("local_origin must be a non-empty string")
    if identity.origin is None:
        return Identity(local_origin, identity.source_id)
    return identity


def digest_of(identity: Identity, local_origin: str) -> Optional[str]:
    """The SHIPPED `source_identity_digest` over the RESOLVED pair (via
    `scope_linkage.identity_digest_of` — the SAME function the store
    calls, never a second implementation): None when `source_id` is
    absent (I13 — so the shared pool has NO digest key; see
    `SHARED_POOL_KEY`)."""
    r = resolve(identity, local_origin)
    return identity_digest_of(r.origin, r.source_id, local_origin)


def same_identity(a: Identity, b: Identity, local_origin: str) -> bool:
    """Resolved-digest equality; a non-groupable identity equals nothing,
    INCLUDING ITSELF (I13/I3)."""
    da, db = digest_of(a, local_origin), digest_of(b, local_origin)
    return da is not None and da == db


# ---- ScopePolicy — unconstructable unvalidated -----------------------------

#: THE VALIDATOR-OWNED REGISTRY is the authority, not fields on the
#: object: `validate_policy` deposits an immutable canonical snapshot
#: here, keyed by the policy instance; `_revalidate` consults the
#: REGISTERED snapshot and refuses on any divergence from the object's
#: current visible state. Re-signing the caller-visible `seal` after an
#: `object.__setattr__` flip therefore achieves nothing.
_SEAL_NONCE = _secrets.token_bytes(32)
_REGISTRY: "_weakref.WeakKeyDictionary" = _weakref.WeakKeyDictionary()


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
    """The tamper-evidence seal. NOT the authority (see `_revalidate`):
    it is compared against the registered value, never recomputed at
    consumption, so a caller who re-signs a flipped field gains
    nothing."""
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
    """REGISTRY-AUTHORITATIVE canonical form: `validate_policy` deposits
    a recursively-immutable snapshot — immutable down to PRIMITIVE string
    leaves, not merely immutable containers around shared `Identity`
    instances — in the validator-owned registry, and `_revalidate`
    refuses on ANY divergence between this object's visible state and
    that snapshot. The `seal` field is retained as tamper-evidence but is
    NOT the authority and is NOT recomputed at consumption. Direct
    construction with raw shapes RAISES here; everything deeper is the
    registry's job."""

    groups: object                     # MappingProxy name -> tuple[Identity]
    cross_scope_visible: bool
    group_digests: object              # MappingProxy name -> frozenset[str]
    seal: str = ""

    def __post_init__(self):
        if not isinstance(self.cross_scope_visible, bool):
            raise ScopeError(
                f"cross_scope_visible must be a real bool, got "
                f"{self.cross_scope_visible!r}")
        if not _canonical_groups_ok(self.groups):
            raise ScopeError(
                "ScopePolicy must be constructed via validate_policy — "
                "groups must be the canonical frozen form")
        if not isinstance(self.group_digests, MappingProxyType):
            raise ScopeError("group_digests must be the validator's frozen "
                             "map — construct via validate_policy")


def validate_policy(groups, cross_scope_visible=False,
                    *, local_origin: str) -> ScopePolicy:
    """THE FACTORY (0020 §4a-ii). Refusals, enumerated: non-mapping
    groups; members not a LIST or TUPLE (SETS and other iterables
    REFUSED — unordered inputs are not a rule grammar); non-Identity
    members; non-groupable members (I13); resolved-DIGEST overlap across
    groups; `cross_scope_visible` not a REAL bool. The caller's input is
    never retained — canonical frozen copies only."""
    if not isinstance(cross_scope_visible, bool):
        raise ScopeError(
            f"cross_scope_visible must be a real bool, got "
            f"{cross_scope_visible!r}")
    if not isinstance(groups, dict):
        raise ScopeError("groups must be a mapping")
    seen: dict = {}
    frozen_groups, frozen_digests = {}, {}
    for name, members in groups.items():
        if not isinstance(name, str) or not name:
            raise ScopeError(f"group name {name!r} is not a non-empty string")
        if not isinstance(members, (list, tuple)):
            raise ScopeError(
                f"group {name!r} members must be a list or tuple, got "
                f"{type(members).__name__} (sets and other iterables are "
                f"REFUSED — unordered inputs are not a rule grammar)")
        out, digs = [], set()
        for m in members:
            if not isinstance(m, Identity):
                raise ScopeError(f"group {name!r} carries a non-Identity "
                                 f"rule shape {m!r}")
            if not m.groupable:
                raise ScopeError(
                    f"group {name!r} contains a source_id-less identity "
                    f"(0006 I13 — no groupable identity)")
            d = digest_of(m, local_origin)
            if d in seen and seen[d] != name:
                raise ScopeError(
                    f"identity digest {d[:12]}… appears in groups "
                    f"{seen[d]!r} and {name!r} — overlap is REFUSED at load")
            seen[d] = name
            out.append(m)
            digs.add(d)
        frozen_groups[name] = tuple(out)
        frozen_digests[name] = frozenset(digs)
    proxy = MappingProxyType(frozen_groups)   # backing dict is LOCAL —
    pol = ScopePolicy(groups=proxy,           # no caller ever held it
                      cross_scope_visible=cross_scope_visible,
                      group_digests=MappingProxyType(frozen_digests),
                      seal=_seal(frozen_groups, cross_scope_visible,
                                 local_origin))
    # the validator-owned snapshot, RECURSIVELY IMMUTABLE — LITERALLY:
    # it holds only PRIMITIVE strings/bools/frozensets from here down, so
    # no leaf is shared with the policy and `object.__setattr__` on a
    # member cannot mutate both references (R7-4)
    _REGISTRY[pol] = (_prim_groups(frozen_groups),
                      cross_scope_visible,
                      tuple(sorted((k, frozenset(v))
                                   for k, v in frozen_digests.items())),
                      pol.seal)
    return pol


def _prim_groups(groups) -> tuple:
    """The snapshot projection of a groups mapping: every `Identity` leaf
    decomposed to its `(origin, source_id)` PRIMITIVE strings."""
    return tuple(sorted(
        (name, tuple((m.origin, m.source_id) for m in members))
        for name, members in groups.items()))


def _revalidate(policy: ScopePolicy, local_origin: str) -> None:
    """Consumption-time revalidation: shape checks, then the DIGEST MAP
    is recomputed from the policy's CURRENT groups (an inconsistent map
    or a mutated backing dict yields a mismatch and refuses), then the
    policy's visible state — PRIMITIVE-projected, so a mutated `Identity`
    leaf projects differently — is compared field-for-field against the
    validator-owned registry snapshot. The registry, not the seal, is the
    authority; the seal is COMPARED against the registered value as
    tamper-evidence and never recomputed here."""
    if not isinstance(policy, ScopePolicy):
        raise ScopeError("policy must be a ScopePolicy")
    if not isinstance(policy.cross_scope_visible, bool) \
            or not _canonical_groups_ok(policy.groups):
        raise ScopeError("policy failed consumption revalidation")
    expected_digs = {name: frozenset(digest_of(m, local_origin)
                                     for m in members)
                     for name, members in policy.groups.items()}
    if dict(policy.group_digests) != expected_digs:
        raise ScopeError(
            "group_digests is not the canonical projection of groups — "
            "a direct construction or a mutated backing map")
    reg = _REGISTRY.get(policy)
    if reg is None:
        raise ScopeError(
            "the policy is not in the validator's registry — constructed "
            "outside validate_policy")
    reg_groups, reg_xv, reg_digs, reg_seal = reg
    if (policy.cross_scope_visible is not reg_xv
            or _prim_groups(policy.groups) != reg_groups
            or tuple(sorted((k, frozenset(v))
                            for k, v in policy.group_digests.items()))
            != reg_digs
            or policy.seal != reg_seal):
        raise ScopeError(
            "the policy's visible state diverges from the validator-owned "
            "snapshot — mutated after validation; RE-SIGNING DOES NOT HELP: "
            "the registry, not the seal, is the authority")


# ---- the record→membership RESOLVER — DIGEST SPACE -------------------------

def is_legacy_derivative(record: dict) -> bool:
    """The REAL shape: a consolidation output's `evidence_ref` is its
    operation id, `op-<12 hex>`; a legacy (pre-0021) output still carries
    the copied groupable identity."""
    return (record.get("author") == "system"
            and bool(_OP_ID.fullmatch(str(record.get("evidence_ref", ""))))
            and record.get("source_id") is not None)


def close_absorption_rows(survivor_id: str, ledger_rows: dict,
                          legacy_links: Optional[dict] = None,
                          legacy_digests: Optional[dict] = None
                          ) -> Optional[list]:
    """0020 §4a-iii — the TRANSITIVE CLOSURE of absorption evidence,
    resident in the LEDGER.

    THE DURABILITY MODEL: accepted 0014 A10 makes the ledger
    SURVIVOR-LIFETIME-KEYED, not append-only (a record's rows drop with
    it), so "absence in the ledger = leaf" is UNSOUND. The durable object
    is the SURVIVOR'S OWN ROW SET, which lives exactly as long as the
    survivor does. Post-amendment writes are BORN CLOSED (0021 §4c
    flattening + the typed `contributor_ref`, one rider), so pruning an
    intermediate touches only rows keyed to IT. The closure is BY
    CONSTRUCTION, not by walk.

    `ledger_rows`: `{survivor_id: [rows]}` — the ledger projection; a row
    may carry `contributor_ref` (typed, post-amendment) and the payload
    marker `flattened`. `legacy_links` / `legacy_digests`: the
    note-derived fallback for PRE-AMENDMENT rows — `{absorber: (absorbed
    ids)}` and `{record_id: identity digest or None}`, both derivable
    only while the absorbed RECORDS still exist.

    The layered rule, per node:

    - Rows WITH a typed ref are closed by the write invariant (0021 W14).
      Where the contributor's own rows are STILL PRESENT they are
      opportunistically VERIFIED: its digests must appear among the
      node's row digests — a mismatch is corrupt (None). Where its rows
      are absent (the A10 prune), no verification is possible and NONE IS
      CLAIMED. THE DISCLOSED RESIDUAL: a writer that violated W14 *and* a
      subsequent prune is undetectable read-side — W14 is the write-side
      gate.
    - Ref-less rows are LEGACY: the note-derived links must account for
      them — the linked absorbed records' digest MULTISET must exactly
      match the unattributed row digests, and each linked prior is
      walked. A pruned legacy contributor, an unknown linked digest, a
      mismatched multiset, one absorbed id under two absorbers, or a
      cyclic path returns **None — and None MUST be read as
      UNRESOLVED**. THE DISCLOSED BEHAVIOUR DELTA: legacy absorption
      survivors whose contributors are unavailable are UNRESOLVED where
      the single-hop read called them own-scope — a fail-closed
      widening, remediable by re-derivation.

    THE STATED RESIDUAL: absorptions predating the 0014 ledger left no
    rows AND no links — their survivors resolve by own identity."""
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
                     if r.get("site") in MEMBERSHIP_SITES}
        if not verify_only:
            out.extend(rows)
        unattributed = []
        for r in rows:
            if r.get("site") not in MEMBERSHIP_SITES:
                continue
            ref = r.get("contributor_ref")
            payload = r.get("payload") or {}
            if payload == {"closure": "incomplete"}:
                continue                   # the marker's None digest fails
                                           # membership closed; it is never
                                           # a link and never walked
            if payload.get("flattened"):
                if ref is None:
                    return False           # a marker-only row would bypass
                                           # BOTH accounting paths
                continue                   # digest counted; subtree covered
            if ref is not None:
                # direct rows and REPARENTED links (reparenting is an
                # INSERTED scope-attribution row, never a mutation).
                # Closed by the write invariant (0021 W14/§4c: flattening
                # and the ref land together). OPPORTUNISTIC verification
                # only — under accepted 0014 A10 a pruned contributor's
                # rows are legitimately GONE, so absence proves nothing
                # and fails nothing; presence is checked.
                if absorber_of.setdefault(ref, node) != node:
                    return False           # two absorbers — corrupt
                for cr in ledger_rows.get(ref, []):
                    if cr.get("site") in MEMBERSHIP_SITES \
                            and cr.get("identity_digest") not in node_digs:
                        return False       # flattening incomplete — corrupt
                if not walk(ref, path | {node}, verify_only=True):
                    return False
            else:
                unattributed.append(r.get("identity_digest"))
        if unattributed:
            linked = legacy_links.get(node)
            if not linked:
                return False               # the pruned-legacy cell
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


def prune_absorbed_record(record_id: str, ledger_rows: dict,
                          *, prune_op: str) -> dict:
    """The RETENTION CONTRACT's prune step, modelled — INSERT-ONLY
    (accepted 0014 says a ledger row is inserted and never updated or
    replaced).

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
    `{"closure": "incomplete"}` — never canonical, never exported; the
    resolver fails it closed). Then the pruned record's own row set drops
    (A10).

    Pruning a record with NO canonical absorber just drops its rows.
    Returns the new `ledger_rows` mapping; inputs are never mutated.

    NOTE: no shipped path prunes today — `apply_retention_prune_plan` is
    named in the writer matrix as a FUTURE primitive. This function is
    the normative model the vectors execute, so the read side's
    prune-time behaviour is pinned before the writer exists.

    THE ONE DELIBERATE DIVERGENCE FROM THE NORMATIVE REFERENCE, and its
    justification: a record that is its OWN canonical absorber (a
    canonical row on X naming contributor X) makes the reference
    NON-TERMINATING — it appends reparented rows to the very list it is
    iterating, and a reparented row is itself canonical, so the loop
    grows without bound and never returns. Production REFUSES that input
    instead: a record cannot absorb itself, so the state is corrupt, and
    the honest answer to corrupt ledger state is a named refusal (the
    posture `derive_absorbed_by` already takes on >1 canonical row). The
    divergence is confined to an input on which the reference has NO
    behaviour to agree with; on every input the reference terminates on,
    this function returns exactly what it returns (checked
    differentially, and by the pinned vectors)."""
    if not _OP_ID.fullmatch(prune_op or ""):
        raise ScopeError(f"prune_op must be op-<12hex>, got {prune_op!r}")
    out = {k: [dict(r, payload=dict(r.get("payload") or {}))
               for r in v] for k, v in ledger_rows.items()}
    absorber = derive_absorbed_by(record_id, out)
    if absorber == record_id:
        raise ExportLinkageError(
            f"record {record_id!r} is its OWN canonical absorber — corrupt "
            f"ledger state (a record cannot absorb itself); the prune "
            f"REFUSES rather than reparenting into the row set it is "
            f"walking. The class is ExportLinkageError, matching the "
            f"reference exactly: corrupt linkage on the derivation path is "
            f"what that error names, and V10 requires the SAME class.")
    if absorber is not None:
        # the iteration is over a SNAPSHOT and the appends land on a
        # DIFFERENT survivor's list (guaranteed by the refusal above) —
        # the loop can never observe a row it just wrote
        for r in list(out.get(record_id, [])):
            if not _is_canonical(r):
                continue
            x = r.get("contributor_ref")
            if x is None:
                continue                        # legacy row — nothing typed
            has_copy = any(
                t.get("contributor_ref") == x
                and (t.get("payload") or {}).get("flattened")
                for t in out.get(absorber, []))
            new = construct_plan_row(
                "prune", prune_op, absorber, site=SITE_ATTRIBUTION,
                identity_digest=(r.get("identity_digest") if has_copy
                                 else None),
                evidence_ref_digest=(r.get("evidence_ref_digest")
                                     if has_copy else None),
                contributor_ref=x,
                payload=({"reparented_from": record_id} if has_copy
                         else {"closure": "incomplete"}))
            out.setdefault(absorber, []).append(new)
    out.pop(record_id, None)                    # the A10 drop
    return out


def membership(record: dict, rows: Optional[list], op_state: str,
               local_origin: str, *,
               expected_contributors: Optional[int] = None):
    """record + REAL ledger rows + operation state → membership evidence:
    a DIGEST (str), `SHARED`, or `UNRESOLVED` (fail-closed).

    `record`: `{"author", "origin", "source_id", "evidence_ref",
    "lineage": bool}` — the provenance-shape fields. `rows`: the record's
    `ContributionRecord`s AS SHIPPED — `[{"site": "absorption" |
    "imported-absorption" | "scope-attribution" | "consolidation",
    "identity_digest": str|None, "op_key": str|None, and optionally the
    0014-amendment fields "contributor_ref"/"evidence_ref_digest"/
    "payload"}]` — keyed by survivor_id (None/[] = no rows). **For
    absorption survivors this MUST be the transitively CLOSED set:
    either the write path flattened ancestors onto the survivor (0021
    §4c, post-0021 stores) or the caller assembled it via
    `close_absorption_rows`; a None closure is UNRESOLVED before this
    function is ever called.** `expected_contributors`: the completeness
    denominator the store derives (lineage length for consolidation
    outputs; None = unknown → incomplete).

    The table, TOTAL:

    - legacy-shaped (the predicate) → UNRESOLVED, whatever it claims.
    - `"generating"` → UNRESOLVED until finalization; `"abandoned"` →
      REFUSE (no output exists, 0010).
    - ABSORPTION SURVIVOR (a non-lineage record WITH absorption rows):
      any row's `identity_digest` differing from the record's own digest
      (None counts as differing from a digest, and a digest from None) →
      UNRESOLVED — a pre-0021 absorption moved another identity's
      testimony into this record and the ledger says so. All rows
      matching the own digest → the own digest.
    - consolidation output (lineage): rows None/empty or
      `expected_contributors` unknown/mismatched → UNRESOLVED
      (incomplete). All `identity_digest` one non-null value → that
      digest. All None → SHARED (the pool's derivatives stay pooled).
      Mixed → UNRESOLVED.
    - ordinary host record, no rows: own digest, or SHARED when
      non-groupable (C3's floor — HOST-produced only)."""
    if op_state not in OP_STATES:
        raise ScopeError(f"unknown operation state {op_state!r} — the set "
                         f"is closed: {OP_STATES}")
    if op_state == "abandoned":
        raise ScopeError("an abandoned operation has no surviving output "
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
        ab = [r for r in rows if r.get("site") in MEMBERSHIP_SITES]
        if ab:
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

#: classification → (visible?, rendering shape)
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
    """`record_evidence` is the RESOLVER's output: a digest string,
    `SHARED`, or `UNRESOLVED`. `principal=None` → unscoped, everything
    OWN. A principal WITHOUT a policy REFUSES (feature-disabled cannot
    honour a principal-bearing call and never silently degrades to an
    unscoped, fully-assertable view); a source_id-less principal REFUSES
    (I13). The policy is REVALIDATED at consumption."""
    if principal is None:
        return "OWN"
    if policy is None:
        raise ScopeError(
            "a principal was supplied but no scope policy is configured — "
            "feature-disabled cannot honour a principal-bearing call")
    _revalidate(policy, local_origin)
    if not principal.groupable:
        raise ScopeError("a principal must carry a source_id (0006 I13)")
    if record_evidence == UNRESOLVED:
        return "UNRESOLVED"
    if record_evidence == SHARED:
        return "SHARED"
    if not (isinstance(record_evidence, str)
            and _HEX64.fullmatch(record_evidence)):
        raise ScopeError(f"record evidence {record_evidence!r} is not a "
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
    """`classify` composed with the FIXED decision table."""
    return DECISION_TABLE[classify(record_evidence, principal, policy,
                                   local_origin)]


# ---- the filter grammar (§4e) ----------------------------------------------

def validate_filters(filters: Optional[dict]) -> dict:
    """The CLOSED §4e grammar: the field set is closed, eq is the only v1
    operator, at most one term per field (a mapping cannot carry two)."""
    if filters is None:
        return {}
    if not isinstance(filters, dict):
        raise ScopeError("filters must be a mapping of field -> value")
    for k, v in filters.items():
        if k not in VALID_FILTER_FIELDS:
            raise ScopeError(f"unknown filter field {k!r} — the field set "
                             f"is CLOSED: {VALID_FILTER_FIELDS}")
        if not isinstance(v, str) or not v:
            raise ScopeError(f"filter {k!r} value must be a non-empty "
                             f"string (eq is the only v1 operator)")
    return dict(filters)


def apply_filters(records: list, filters: dict) -> list:
    """M-2: after scope, within the visible set; NARROW ONLY. A
    `source_id` filter never matches a cleared derivative (its field is
    None; the ledger holds only a one-way digest)."""
    out = records
    for k, v in filters.items():
        out = [r for r in out if r.get(k) is not None and str(r.get(k)) == v]
    return out
