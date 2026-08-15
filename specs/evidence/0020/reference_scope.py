"""specs/0020 §4a-ii — the NORMATIVE reference for the scope surface (v9).

PORTABLE AND PURE: no I/O, no store dependency. Two conforming
implementations must agree with this module on every input; the pinned
vectors live beside it in `vectors.json`, the SHIPPED HARNESS
(`vector_harness.py`) executes them, and 0020 V10 binds implementations to
both.

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


def close_absorption_rows(survivor_id: str, direct_rows: dict,
                          absorbed_links: dict) -> Optional[list]:
    """0020 §4a-iii v9 (external R7-1) — the TRANSITIVE CLOSURE of
    absorption evidence. A survivor's direct rows carry only its DIRECT
    contributors' digests; when an absorbed prior was itself a
    survivor-with-contributors (the reviewer's A → B → C chain), the
    ancestor digests live on the PRIOR's rows, and a single-level read
    misclassifies the survivor as own-scope. Membership for absorption
    survivors is therefore defined over the CLOSED set this function
    computes.

    `direct_rows`: {record_id: [ContributionRecord-shaped rows]} — each
    known record's OWN rows (an empty list is a known record with no rows;
    a MISSING key is an unknown record). `absorbed_links`:
    {absorber_id: (absorbed_record_id, ...)} — the absorbed-prior links
    (from absorption events, `absorbed_by` linkage, or import
    reconstruction).

    Returns the closed row list, or **None — and None MUST be read as
    UNRESOLVED** — when the chain is unwalkable: a linked prior absent
    from `direct_rows` (evidence incomplete), or a repeated node (a record
    is absorbed at most once, so any revisit is corrupt linkage; both fail
    closed). Idempotent over write-time-flattened stores (0021 §4c): the
    union re-adds digests already present.

    The stated residual is UNCHANGED: absorptions predating the 0014
    ledger left no rows AND no links — their survivors resolve by own
    identity (0021 §4d)."""
    if survivor_id not in direct_rows:
        return None
    out, seen = [], {survivor_id}
    stack = [survivor_id]
    while stack:
        rid = stack.pop()
        out.extend(direct_rows[rid])
        for prior in absorbed_links.get(rid, ()):
            if prior in seen:
                return None            # cycle / duplicate link — corrupt
            seen.add(prior)
            if prior not in direct_rows:
                return None            # unwalkable — evidence incomplete
            stack.append(prior)
    return out


def membership(record: dict, rows: Optional[list], op_state: str,
               local_origin: str, *, expected_contributors: Optional[int] = None):
    """record + REAL ledger rows + operation state → membership evidence:
    a DIGEST (str), SHARED, or UNRESOLVED (fail-closed).

    `record`: {"author", "origin", "source_id", "evidence_ref",
    "lineage": bool} — the provenance-shape fields. `rows`: the record's
    `ContributionRecord`s AS SHIPPED — [{"site": "absorption" |
    "consolidation", "identity_digest": str|None, "op_key": str|None}] —
    keyed by survivor_id (None/[] = no rows). **For absorption survivors
    this MUST be the transitively CLOSED set (R7-1): either the write path
    flattened ancestors onto the survivor (0021 §4c, post-0021 stores) or
    the caller assembled it via `close_absorption_rows`; a None closure is
    UNRESOLVED before this function is ever called.** `expected_contributors`: the
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
              if r.get("site") in ("absorption", "imported-absorption")]
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


def reconstruct_absorption_rows(export_records: list, local_origin: str,
                                *, id_remap: Optional[dict] = None,
                                op_key: str):
    """The 0020 §4a-iii import-time RECONSTRUCTION rule (v9 — external
    R7-1/R7-2/R7-3 folded).

    PRE-COMMIT (R7-2): `export_records` are the records AS PARSED FROM THE
    EXPORT FILE — original ids, before any destination write. Winner
    resolution happens in the file's own id universe (`_resolve_winner`);
    `id_remap` (the importer's old→new table when a `user_id=` remap runs)
    translates the OUTPUT keys only. A raised `ImportLinkageError` means
    the importer never writes — destination unchanged.

    TRANSITIVE (R7-1): each absorbed record's identity digest propagates
    to its direct winner AND every transitive absorber (A → B → C leaves
    C carrying both B's and A's digests) — the reconstructed sets are
    BORN CLOSED, matching the write-time flattening rule (0021 §4c). A
    cyclic winner chain refuses (corrupt linkage).

    FULLY POPULATED ROWS (R7-3): the import operation mints ONE
    `op-<12hex>` operation key and passes it here; every emitted row
    carries it (the 0009 amendment's deterministic row identity keys on
    it). Returns {post-remap survivor_id: [rows]}.

    These rows are ATTRIBUTION evidence for scope membership ONLY — they
    are NOT 0014 §4a absorption payloads and provide NO reversal (the
    pre-inheritance base image is not in the export and cannot be
    inferred; stated as the imported-absorption site's honest limit —
    R6-2)."""
    if not _OP_ID.match(op_key or ""):
        raise PolicyError(f"op_key must be the minted op-<12hex> operation "
                          f"key (R7-3), got {op_key!r}")
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
        row = {"site": "imported-absorption", "identity_digest": d,
               "op_key": op_key}
        # propagate to the direct winner and every transitive absorber
        hop, visited = winner_of[rid], {rid}
        while True:
            if hop in visited:
                raise ImportLinkageError(
                    f"absorption linkage from {rid!r} is CYCLIC at "
                    f"{hop!r} — corrupt history; the import REFUSES (R7-1)")
            visited.add(hop)
            out.setdefault(id_remap.get(hop, hop), []).append(dict(row))
            if hop not in winner_of:
                break
            hop = winner_of[hop]
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
