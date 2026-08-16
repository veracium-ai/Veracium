"""specs/0020 §4a-iii / specs/0021 §7b — the production scope-linkage
primitives: import-time absorption reconstruction and the export
reverse-link algorithm.

This module is the PRODUCTION PORT of the normative reference
(`specs/evidence/0020/reference_scope.py` — production never imports
specs/); semantics are IDENTICAL by construction and the parity tests in
`tests/test_0021_import_linkage.py` cross-check row multisets against the
reference over real fixture files. The pinned behaviours:

- `_resolve_winner`: the DECIDABLE linkage rule (R7-2) — a structured
  `absorbed_by_id` (the FORMAT-7 rider carrier) is consumed verbatim and
  must name a record in the file; otherwise the LAST `absorbed_by:` note
  tag governs, candidates matched against the file's own id universe
  under the shipped framings; zero or multiple candidates REFUSE.
- `reconstruct_absorption_rows`: PRE-COMMIT reconstruction over the
  export file's records (original ids; `id_remap` translates outputs),
  TRANSITIVE (digests propagate to every absorber; cyclic chains
  refuse), emitting COMPLETE rows through the operation-aware
  constructor — direct links at `imported-absorption`, transitive
  copies at `scope-attribution`.
- `derive_absorbed_by`: the EXACT reverse-link algorithm (R9-1/R10-2) —
  CANONICAL rows are direct (`absorption`/`imported-absorption`) or
  reparented-class `scope-attribution` rows; plain flattened copies and
  the closure-incompleteness marker NEVER; one → the survivor, zero →
  omit (legacy travel), >1 → `ExportLinkageError` refusing the whole
  export.
- `validate_row_plan` / `construct_plan_row` / `plan_row_id` /
  `row_op_key` / `native_row_op_key`: the 0009 §4c amendment's
  context-aware validator, injective per-row op keys, and THE ONE
  canonical logical-row projection. Only the "import" writer context is
  exercised by shipped code TODAY — the native flattening and the prune
  primitive are the 0021 feature implementation, not this release; their
  table entries and constructors are ported (present, validated) but
  unused.

Digest constructions are the SHIPPED ones (`source_identity`,
`contribution.evidence_ref_digest`) — never re-derived here — so
store-side and linkage-side digests are byte-identical by sharing code.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Optional

from .contribution import evidence_ref_digest
from .source_identity import resolve_origin, source_identity_digest

#: the REAL import operation-id shape (`op-<12hex>`, minted once per import)
_OP_ID = re.compile(r"^op-[0-9a-f]{12}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

SITE_IMPORTED = "imported-absorption"
SITE_ATTRIBUTION = "scope-attribution"
#: the sites the AMENDED primitives may write (0014 amendment clause 1)
PLAN_SITES = (SITE_IMPORTED, SITE_ATTRIBUTION)
#: the sites that carry absorption membership evidence (read side)
MEMBERSHIP_SITES = ("absorption", SITE_IMPORTED, SITE_ATTRIBUTION)


class ScopeError(ValueError):
    """THE ONE scope-surface error class (the production name for the
    normative reference's `PolicyError`; `veracium.scope` re-exports it
    under BOTH names so error identity is a single class, never two).

    Raised at config load, at consumption revalidation, and by the
    linkage validators — never silently widened past. It subclasses
    `ValueError` so every pre-existing `except ValueError` caller of
    these primitives is unaffected."""


class ImportLinkageError(ScopeError):
    """An import whose absorption linkage cannot be reconstructed
    unambiguously REFUSES WHOLE, PRE-COMMIT (0020 §4a-iii R6-1/R7-2):
    reconstruction runs on the export file's records BEFORE any
    destination write, so a refused import leaves the destination
    byte-identical."""


class ExportLinkageError(ScopeError):
    """A contributor with MORE THAN ONE canonical absorber row is corrupt
    ledger state — the exporter REFUSES to materialise a structured link
    from it (R9-1: a corrupt store must not become a portable file that
    looks clean)."""


def _framed(b: bytes) -> bytes:
    return len(b).to_bytes(4, "big") + b


def canonical_payload(payload: dict) -> str:
    """The ONE canonical payload form for the row-id projection (R9-3):
    sorted keys, no whitespace — byte-identical to the normative
    reference's projection."""
    if not isinstance(payload, dict):
        raise ScopeError(f"payload must be a mapping, got {payload!r}")
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def identity_digest_of(origin: Optional[str], source_id: Optional[str],
                       local_origin: str) -> Optional[str]:
    """The SHIPPED source-identity digest over the RESOLVED pair: None
    when source_id is absent (0006 I13)."""
    if source_id is None:
        return None
    return source_identity_digest(resolve_origin(origin, local_origin),
                                  source_id)


def evidence_digest_of(origin: Optional[str], evidence_ref: Optional[str],
                       local_origin: str) -> Optional[str]:
    """The SHIPPED evidence-ref digest; None iff evidence_ref is
    empty/absent (0014 §4a); origin resolves to the local singleton
    first (0006 §4 rule 6)."""
    if not evidence_ref:
        return None
    return evidence_ref_digest(resolve_origin(origin, local_origin),
                               evidence_ref)


# ---- the closed payload vocabulary + writer matrix (R10-3 / R12-1) ---------

#: the CLOSED payload vocabulary, per plan site (exact shapes — unknown
#: keys refuse, marker values must be the literal True)
_PAYLOAD_SHAPES = {
    SITE_IMPORTED: ({"reconstructed": True},),
    SITE_ATTRIBUTION: ({"flattened": True},
                       {"flattened": True, "reconstructed": True},
                       "REPARENTED",          # {"reparented_from": <id>}
                       {"closure": "incomplete"}),
}

#: the per-context allowed (site, payload-class) cells + op-id domains —
#: each atomic writer may emit ONLY its own cells (R12-1). The "native"
#: and "prune" contexts are ported table entries whose writers are the
#: 0021 feature implementation (apply_supersession_plan flattening;
#: apply_retention_prune_plan) — present, unused by shipped code TODAY.
WRITER_CONTEXTS = {
    "native": {"op_re": r"^sup-.+$",
               "cells": {(SITE_ATTRIBUTION, "flattened")}},
    "import": {"op_re": r"^op-[0-9a-f]{12}$",
               "cells": {(SITE_IMPORTED, "reconstructed"),
                         (SITE_ATTRIBUTION, "flattened+reconstructed")}},
    "prune": {"op_re": r"^op-[0-9a-f]{12}$",
              "cells": {(SITE_ATTRIBUTION, "reparented"),
                        (SITE_ATTRIBUTION, "marker")}},
}


def payload_class(payload: dict) -> str:
    """The closed payload-class name (R12-1's cross-product axis)."""
    if payload == {"reconstructed": True}:
        return "reconstructed"
    if payload == {"flattened": True}:
        return "flattened"
    if payload == {"flattened": True, "reconstructed": True}:
        return "flattened+reconstructed"
    if set(payload) == {"reparented_from"}:
        return "reparented"
    if payload == {"closure": "incomplete"}:
        return "marker"
    return "UNKNOWN"


def validate_plan_site_payload(site: str, payload: dict) -> None:
    """The closed per-site payload shapes for the TWO plan sites (the
    0014 amendment's site-registry entries): exact match — unknown keys,
    truthy non-True markers, and undeclared classes all refuse (R10-3)."""
    if site not in PLAN_SITES:
        raise ScopeError(f"site {site!r} outside the closed plan-site set "
                         f"{PLAN_SITES} (0014 §4a as amended)")
    if not isinstance(payload, dict):
        raise ScopeError("row payload must be a mapping")
    for shape in _PAYLOAD_SHAPES[site]:
        if shape == "REPARENTED":
            if (set(payload) == {"reparented_from"}
                    and isinstance(payload["reparented_from"], str)
                    and payload["reparented_from"]):
                return
        elif payload == shape and all(
                type(payload[k]) is type(shape[k]) for k in shape):
            # exact: keys AND literal values AND types — dict equality
            # alone admits 1 == True (R10-3's truthy-marker cell)
            return
    raise ScopeError(
        f"payload {payload!r} is not one of site {site!r}'s closed shapes "
        f"(R10-3: exact match — unknown keys, truthy non-True markers, and "
        f"undeclared classes all refuse)")


def validate_row_plan(row: dict, context: str, *, op: str,
                      survivor_id: str) -> None:
    """The cross-field validator (R9-3), TOTAL (R10-3) and CONTEXT-AWARE
    (R12-1): each atomic writer may emit only ITS OWN (site,
    payload-class) cells per `WRITER_CONTEXTS`. PRESENCE of every
    semantic field is required separately from value validity (R11-2 —
    None is a value, absence is not; contributor_type is never
    defaulted). The op_key is BOUND (R13-1): the context's op-ID domain
    is consumed and the row's key must EQUAL the context's derivation
    over (op, survivor, contributor)."""
    required = ("site", "identity_digest", "evidence_ref_digest",
                "contributor_type", "contributor_ref", "payload",
                "op_key")   # R13-1: the key is part of the contract
    missing = [f for f in required if f not in row]
    if missing:
        raise ScopeError(f"plan row is missing required field(s) "
                         f"{missing} — presence is part of the contract "
                         f"(R11-2); None is a value, absence is not")
    if row["site"] not in PLAN_SITES:
        raise ScopeError(f"row site {row['site']!r} outside the closed "
                         f"plan-site set {PLAN_SITES}")
    for field in ("identity_digest", "evidence_ref_digest"):
        d = row[field]
        if d is not None and not (isinstance(d, str) and _HEX64.fullmatch(d)):
            raise ScopeError(f"{field} {d!r} is neither None nor a "
                             f"64-hex digest")
    if row["contributor_type"] != "edge":
        raise ScopeError(f"contributor_type {row['contributor_type']!r} "
                         f"outside the closed set {{'edge'}} — and it is "
                         f"never defaulted (R11-2)")
    if not (isinstance(row["contributor_ref"], str)
            and row["contributor_ref"]):
        raise ScopeError("every plan row NAMES its contributor — "
                         "contributor_ref must be a non-empty string "
                         "(R10-3: the missing-direct-ref cell)")
    payload = row["payload"]
    validate_plan_site_payload(row["site"], payload)
    if payload == {"closure": "incomplete"} \
            and row.get("identity_digest") is not None:
        raise ScopeError("a closure-incompleteness marker asserts MISSING "
                         "evidence — identity_digest must be None")
    # R12-1: the WRITER cross-product — this context may write ONLY its
    # own (site, payload-class) cells
    if context not in WRITER_CONTEXTS:
        raise ScopeError(f"unknown writer context {context!r} — the set "
                         f"is closed: {sorted(WRITER_CONTEXTS)}")
    cell = (row["site"], payload_class(payload))
    if cell not in WRITER_CONTEXTS[context]["cells"]:
        raise ScopeError(
            f"writer context {context!r} may not emit the "
            f"(site, payload-class) cell {cell!r} — its closed set is "
            f"{sorted(WRITER_CONTEXTS[context]['cells'])} (R12-1: each "
            f"atomic primitive owns its own cells)")
    # R13-1: the OPERATION BINDING — the context's op-ID domain is
    # CONSUMED here, and the row's key must EQUAL the context's
    # derivation over (op, survivor, contributor); a caller cannot select
    # an arbitrary, cross-context, or null key.
    if not (isinstance(op, str)
            and re.fullmatch(WRITER_CONTEXTS[context]["op_re"], op)):
        raise ScopeError(
            f"operation id {op!r} is outside writer context {context!r}'s "
            f"domain {WRITER_CONTEXTS[context]['op_re']!r} (R13-1)")
    expected_key = (native_row_op_key(op, survivor_id,
                                      row["contributor_ref"])
                    if context == "native"
                    else row_op_key(op, row["site"], survivor_id,
                                    row["contributor_ref"]))
    if row["op_key"] != expected_key:
        raise ScopeError(
            f"op_key {row['op_key']!r} is not the context's derivation "
            f"over (op, survivor, contributor) — absent, null, malformed, "
            f"cross-context, and mis-derived keys all land here (R13-1: "
            f"the key is DERIVED, never selected)")


def plan_row_id(user_id: str, survivor_type: str, survivor_id: str,
                row: dict, context: str, *, op: str) -> str:
    """THE ONE canonical logical-row projection (0009 §4c amendment,
    R9-3): a framed digest over EVERY semantic field — user, survivor
    coordinates, site, identity digest, evidence digest, contributor
    type AND ref, and the CANONICAL PAYLOAD. Excluded are ONLY the
    operational fields (the re-minted op key and the commit timestamp).
    Idempotent-equality has exactly ONE definition: plan_row_id set
    equality. The cross-field validator runs first — a contradictory
    row never projects."""
    validate_row_plan(row, context, op=op, survivor_id=survivor_id)
    parts = [b"veracium.import-contribution-row.v2"]
    for v in (user_id, survivor_type, survivor_id, row["site"],
              row["identity_digest"],
              row["evidence_ref_digest"],
              row["contributor_type"],     # never defaulted (R11-2)
              row["contributor_ref"],
              canonical_payload(row["payload"])):
        parts.append(_framed(b"\x00" if v is None
                             else b"\x01" + str(v).encode("utf-8")))
    return hashlib.sha256(b"".join(parts)).hexdigest()


def row_op_key(op: str, site: str, survivor_id: str,
               contributor_ref: str) -> str:
    """The PER-ROW op key, INJECTIVE framed-digest form (R9-2): the
    prefix fields are colon-free by construction (`op-<12hex>` + the
    site token); the pair of unrestricted ids is FRAMED and
    domain-separated into one fixed-width digest."""
    if not _OP_ID.fullmatch(op or ""):
        raise ScopeError(f"op must be op-<12hex>, got {op!r}")
    if site not in PLAN_SITES:
        raise ScopeError(f"op-key site token {site!r} outside {PLAN_SITES}")
    h = hashlib.sha256(b"veracium.import-row-op-key.v1"
                       + _framed(survivor_id.encode("utf-8"))
                       + _framed(contributor_ref.encode("utf-8"))
                       ).hexdigest()
    return f"{op}:{site}:{h}"


def native_row_op_key(op_id: str, survivor_id: str,
                      contributor_ref: str) -> str:
    """The NATIVE-context per-row key (R12-1): the shipped supersession
    op id is `sup-{edge.id}` with an UNRESTRICTED suffix, so it is
    FRAMED INTO the digest with the pair — never a colon-delimited
    prefix. Ported for the 0021 feature implementation; unused by
    shipped code today."""
    if not re.fullmatch(r"sup-.+", op_id or ""):
        raise ScopeError(f"native op id must be sup-<edge-id>, got "
                         f"{op_id!r}")
    h = hashlib.sha256(b"veracium.native-attribution-op-key.v1"
                       + _framed(op_id.encode("utf-8"))
                       + _framed(survivor_id.encode("utf-8"))
                       + _framed(contributor_ref.encode("utf-8"))
                       ).hexdigest()
    return f"{SITE_ATTRIBUTION}:{h}"


def import_row_op_key(import_op: str, survivor_id: str,
                      contributor_ref: str) -> str:
    """The imported-absorption specialization of `row_op_key`."""
    return row_op_key(import_op, SITE_IMPORTED, survivor_id,
                      contributor_ref)


def construct_plan_row(context: str, op: str, survivor_id: str, *,
                       site: str, identity_digest, evidence_ref_digest,
                       contributor_ref: str, payload: dict) -> dict:
    """THE OPERATION-AWARE ROW CONSTRUCTOR (R13-1): the primitive
    derives `op_key` ITSELF from its store-owned operation id and the
    row coordinates — callers never supply a key. The full validator
    (domain, cell, exact key equality) runs before the row is
    returned. Every normative row producer builds through here."""
    ctx = WRITER_CONTEXTS.get(context)
    if ctx is None:
        raise ScopeError(f"unknown writer context {context!r}")
    if not (isinstance(op, str) and re.fullmatch(ctx["op_re"], op)):
        raise ScopeError(f"operation id {op!r} outside context "
                         f"{context!r}'s domain (R13-1)")
    key = (native_row_op_key(op, survivor_id, contributor_ref)
           if context == "native"
           else row_op_key(op, site, survivor_id, contributor_ref))
    row = {"site": site, "identity_digest": identity_digest,
           "evidence_ref_digest": evidence_ref_digest,
           "contributor_ref": contributor_ref,
           "contributor_type": "edge", "payload": payload,
           "op_key": key}
    validate_row_plan(row, context, op=op, survivor_id=survivor_id)
    return row


# ---- import-time reconstruction (0020 §4a-iii) -----------------------------

def _resolve_winner(record: dict, file_ids: set) -> str:
    """The DECIDABLE linkage rule (R7-2).

    1. STRUCTURED FIRST: a record carrying `absorbed_by_id` (the
       FORMAT-7 rider carrier) uses it verbatim — no note parsing. It
       must name a record in the file.
    2. LEGACY NOTE: the LAST `absorbed_by:` occurrence governs and is
       the ONLY tag that must resolve. The tag's value is matched
       against the export's OWN id universe: candidate winners are every
       file id W where the remainder equals W, or starts with
       W + " (restated as " or W + "; " (the shipped append framings).
       EXACTLY ONE candidate resolves; ZERO refuses
       (missing/unresolvable); MORE THAN ONE refuses (the legacy carrier
       is genuinely ambiguous there — the structured field is the fix,
       refusal is the fallback)."""
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
                                import_op: str) -> dict:
    """The 0020 §4a-iii import-time RECONSTRUCTION rule.

    PRE-COMMIT (R7-2): `export_records` are the records AS PARSED FROM
    THE EXPORT FILE — original ids, before any destination write. Winner
    resolution happens in the file's own id universe; `id_remap` (the
    importer's old→new table when a `user_id=` remap runs) translates
    OUTPUT keys and refs. A raised `ImportLinkageError` means the
    importer never writes — destination unchanged.

    COMPLETE ROWS (R8-3): every emitted row carries site,
    identity_digest, the typed contributor_ref (post-remap absorbed
    record id), evidence_ref_digest (the shipped construction over the
    absorbed record's resolved origin + evidence_ref), the closed
    payload, and the injective per-row op_key — built through the
    operation-aware constructor. `import_op` is the ONE `op-<12hex>` id
    the import operation mints.

    TRANSITIVE (R7-1): each absorbed record's digest propagates to its
    direct winner AND every transitive absorber — reconstructed sets
    are BORN CLOSED; cyclic winner chains refuse.

    These rows are ATTRIBUTION evidence for scope membership ONLY —
    they are NOT 0014 §4a absorption payloads and provide NO reversal
    (R6-2)."""
    if not _OP_ID.fullmatch(import_op or ""):
        raise ScopeError(f"import_op must be the minted op-<12hex> "
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
        d = identity_digest_of(r.get("origin"), r.get("source_id"),
                               local_origin)
        ev = evidence_digest_of(r.get("origin"), r.get("evidence_ref"),
                                local_origin)
        cref = id_remap.get(rid, rid)
        # propagate to the direct winner and every transitive absorber —
        # DIRECT links land at imported-absorption; transitive copies at
        # scope-attribution (R10-1)
        hop, visited, direct = winner_of[rid], {rid}, True
        while True:
            if hop in visited:
                raise ImportLinkageError(
                    f"absorption linkage from {rid!r} is CYCLIC at "
                    f"{hop!r} — corrupt history; the import REFUSES (R7-1)")
            visited.add(hop)
            surv = id_remap.get(hop, hop)
            site = SITE_IMPORTED if direct else SITE_ATTRIBUTION
            payload = ({"reconstructed": True} if direct
                       else {"flattened": True, "reconstructed": True})
            out.setdefault(surv, []).append(construct_plan_row(
                "import", import_op, surv, site=site, identity_digest=d,
                evidence_ref_digest=ev, contributor_ref=cref,
                payload=payload))
            if hop not in winner_of:
                break
            hop = winner_of[hop]
            direct = False
    return out


# ---- the export reverse link (0020 §4a-iii R9-1) ---------------------------

def _is_canonical(row: dict) -> bool:
    """CANONICAL means: a DIRECT link (a native `absorption` or
    `imported-absorption` row) or a REPARENTED link (a scope-attribution
    row whose payload is the reparented class). Plain flattened copies
    are never canonical, and NEITHER is the closure-incompleteness
    marker (R10-2's executed launder)."""
    p = row.get("payload") or {}
    site = row.get("site")
    if site in ("absorption", SITE_IMPORTED):
        return True
    if site == SITE_ATTRIBUTION:
        return set(p) == {"reparented_from"}
    return False


def derive_absorbed_by(contributor_id: str, ledger_rows: dict):
    """The EXACT reverse-link algorithm (R9-1; the canonical predicate
    per R10-1/R10-2 — see `_is_canonical`). `ledger_rows` is
    {survivor_id: [row dicts]} carrying at least
    site/payload/contributor_ref.

    Returns the unique canonical absorber's survivor id; None when no
    canonical row exists (the exporter OMITS `absorbed_by_id` and the
    record travels as legacy — the import-side note rule governs,
    fail-closed on ambiguity); raises ExportLinkageError on >1 canonical
    row (corrupt — the export refuses whole)."""
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
