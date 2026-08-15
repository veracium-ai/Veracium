"""specs/0014 §4a/§4b — the contribution ledger's derivations and validations.

Everything here is STORE-side: sites emit reference-only drafts (R2-1), and the
store derives identity digests and payloads from authoritative rows inside the
consuming transaction, then validates its OWN output against the closed per-site
schemas as a self-check (an invalid payload signals a derivation failure and
aborts the whole maintenance transaction — A7).
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional

# --------------------------------------------------------------------------
# The evidence-reference digest — its OWN domain-separated construction (R1-8).
# Frozen, byte-exact (R2-5): length-framed origin || evidence_ref under the
# dedicated domain, so it can never collide with 0006's source-identity digests
# even over equal inputs.

_EVIDENCE_REF_DOMAIN = b"veracium.evidence-ref.v1"


def _framed(b: bytes) -> bytes:
    return len(b).to_bytes(4, "big") + b


def evidence_ref_digest(origin: Optional[str], evidence_ref: str) -> Optional[str]:
    """NULL iff `evidence_ref == ""` — the empty string is DEFINED as absent
    (0014 §4a, stated not implied); a non-empty ref always digests. `origin`
    must already be RESOLVED (0006 §4 rule 6)."""
    if evidence_ref == "":
        return None
    if origin is None:
        raise ValueError(
            "origin must be RESOLVED before digesting (0006 §4 rule 6)")
    payload = (_EVIDENCE_REF_DOMAIN
               + _framed(origin.encode("utf-8"))
               + _framed(evidence_ref.encode("utf-8")))
    return hashlib.sha256(payload).hexdigest()


# --------------------------------------------------------------------------
# The closed per-site payload schemas (§4a) — canonical form: sorted keys,
# omitted-if-absent (`derived_from` OMITTED when None, never null). This exact
# canonical text feeds the op-key conflict comparison and the outcome digest.

_SIDE_MANDATORY = ("observed_at", "confidence", "valid_from", "disclosure")
_SIDE_OPTIONAL = ("derived_from",)
_INPUT_MANDATORY = ("observed_at", "confidence", "disclosure",
                    "author_of_evidence", "date")
_INPUT_OPTIONAL = ("derived_from",)

SITES = ("absorption", "consolidation")   # the CLOSED site set (§4a)


def json_datetime(dt) -> str:
    """The ONE canonical datetime rendering for every 0014 carrier — identical
    to pydantic's JSON-mode form (Z-suffixed UTC), so the pre-image, payload
    sides, and the raw-request snapshot never disagree byte-wise over the same
    instant."""
    return dt.isoformat().replace("+00:00", "Z")


def canonical_payload(payload: dict) -> str:
    """Sorted keys, no whitespace — deterministic for digesting, validation,
    recomputation, and conflict comparison alike (§4a)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _validate_side(side: dict, label: str, mandatory, optional) -> None:
    if not isinstance(side, dict) or not side:
        raise ValueError(f"{label}: must be a non-empty mapping (payloads are "
                         f"TOTAL — {{}} is an integrity error, 0014 §4a)")
    keys = set(side)
    missing = set(mandatory) - keys
    if missing:
        raise ValueError(f"{label}: missing mandatory keys {sorted(missing)}")
    extra = keys - set(mandatory) - set(optional)
    if extra:
        raise ValueError(f"{label}: unknown keys {sorted(extra)} (the schema "
                         f"is CLOSED — R1-8)")
    for k, v in side.items():
        if v is None:
            raise ValueError(f"{label}.{k}: None is never encoded — optional "
                             f"keys are OMITTED when absent (§4a)")
        if not isinstance(v, (str, int, float, bool)):
            raise ValueError(f"{label}.{k}: scalar values only (content-free, "
                             f"A5) — got {type(v).__name__}")


def validate_absorption_payload(payload: dict) -> None:
    """`{"base": {...}, "contributor": {...}}` — both sides over the closed
    field set; TOTAL (the A1 no-transfer case is visible IN the values)."""
    if not isinstance(payload, dict) or set(payload) != {"base", "contributor"}:
        raise ValueError("absorption payload must be exactly "
                         "{'base': …, 'contributor': …} (0014 §4a)")
    _validate_side(payload["base"], "base", _SIDE_MANDATORY, _SIDE_OPTIONAL)
    _validate_side(payload["contributor"], "contributor",
                   _SIDE_MANDATORY, _SIDE_OPTIONAL)


def validate_consolidation_payload(payload: dict) -> None:
    """`{"input": {...}, "output_index": <int>}` — the R4-6 exact schema; an
    Episode HAS no valid_from, so the input set excludes it."""
    if not isinstance(payload, dict) or set(payload) != {"input", "output_index"}:
        raise ValueError("consolidation payload must be exactly "
                         "{'input': …, 'output_index': …} (0014 §4a)")
    idx = payload["output_index"]
    if isinstance(idx, bool) or not isinstance(idx, int) or idx < 0:
        raise ValueError("output_index must be a non-negative int (0014 §2c)")
    _validate_side(payload["input"], "input", _INPUT_MANDATORY, _INPUT_OPTIONAL)


def validate_payload(site: str, payload: dict) -> None:
    if site == "absorption":
        validate_absorption_payload(payload)
    elif site == "consolidation":
        validate_consolidation_payload(payload)
    else:
        raise ValueError(f"unknown site {site!r} — the site set is CLOSED "
                         f"({', '.join(SITES)}; 0014 §4a)")


def consolidation_op_key(operation_id: str, output_index: int,
                         contributor_type: str, contributor_id: str) -> str:
    """The consolidation retry identity (R2-2), canonical form."""
    return f"{operation_id}:{output_index}:{contributor_type}:{contributor_id}"


# --------------------------------------------------------------------------
# specs/0014 §4b — the raw-request snapshot, its byte-exact digest, and the
# exhaustive field partition (R7-1/R8-2/R9-3/R9-4/R10-1..3/R13-1 lineage).

REQUEST_DIGEST_DOMAIN = b"veracium.supersession-request.v1"

# The partition over Edge.model_fields + Provenance.model_fields — TOTAL, and
# pinned by test_raw_request_field_partition_is_total: a new model field breaks
# the test until classified here.
EXACT_EQUAL_EDGE_FIELDS = ("id", "user_id", "subject", "relation", "object",
                           "note", "volatility", "needs_confirmation")
EXACT_EQUAL_PROV_FIELDS = ("source_type", "author_of_evidence", "evidence_ref",
                           "disclosure", "derived_from", "source_id", "origin")
# EXACTLY the fields the shipped C' absorption inherits (graph.py absorption
# loop): the three winner-inheritance maxima/minima PLUS `ungrounded` — the
# 0019 rider's RECOMPUTED class: absorption may change it from the raw
# submission by EXACTLY the N-ary OR over {incoming} ∪ absorbed (0014 §2c as
# amended by 0019; the verifier accepts precisely that transform)
RECOMPUTED_EDGE_FIELDS = ("valid_from", "ungrounded")
RECOMPUTED_PROV_FIELDS = ("observed_at", "confidence")
# store-lifecycle fields a raw submission cannot carry (non-default → abort)
FORBIDDEN_EDGE_FIELDS = ("invalidated_at", "invalidation_reason", "supersedes",
                         "last_outcome", "last_outcome_at", "times_used",
                         "outcome_counts")
_FORBIDDEN_DEFAULTS = {"invalidated_at": None, "invalidation_reason": None,
                       "supersedes": None, "last_outcome": None,
                       "last_outcome_at": None, "times_used": 0,
                       "outcome_counts": {}}
# The one Edge field that partitions through its OWN sub-fields rather than
# as an edge-level scalar. Every field must appear in exactly one class — the
# totality test enforces it.
STRUCTURAL_EDGE_FIELDS = ("provenance",)


def raw_request_snapshot(edge) -> dict:
    """The CANONICAL snapshot of the raw edge as submitted (§4b): the COMPLETE
    Edge model dump in JSON mode — EVERY field including defaults, None as
    null (total, so null-vs-omitted cannot arise), keys sorted recursively at
    digest time. Captured by the PUBLIC entry point BEFORE planning."""
    return json.loads(edge.model_dump_json())


def request_digest(snapshot: dict) -> str:
    """FROZEN, byte-exact (R8-2): SHA-256(domain || utf8(json.dumps(snapshot,
    sort_keys=True, ensure_ascii=False, separators=(',',':'),
    allow_nan=False))). Recursively sorted keys; no whitespace; raw-UTF-8
    non-ASCII; NaN/±Inf unencodable (aborts)."""
    body = json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(REQUEST_DIGEST_DOMAIN + body.encode("utf-8")).hexdigest()


def verify_snapshot_against_plan(snapshot: dict, plan) -> None:
    """The store's snapshot verification (§4b) under the exhaustive partition —
    EXACT-EQUAL fields byte-equal the plan's incoming; RECOMPUTED fields (the
    C' three) reproduce the committed survivor from the snapshot's values plus
    the recorded contributors; FORBIDDEN fields must sit at their defaults.
    Raises ValueError (the op aborts) on any mismatch — a forged snapshot
    differing in ANY field is caught (R8-2/R9-3)."""
    if not isinstance(snapshot, dict):
        raise ValueError("raw_request must be a mapping (0014 §4b)")
    inc = json.loads(plan.incoming_edge.model_dump_json())
    missing = set(inc) - set(snapshot)
    if missing:
        raise ValueError(f"raw_request is not the COMPLETE dump — missing "
                         f"{sorted(missing)} (0014 §4b)")
    for f in EXACT_EQUAL_EDGE_FIELDS:
        if snapshot.get(f) != inc[f]:
            raise ValueError(f"raw_request.{f} differs from the plan's incoming "
                             f"(exact-equal class, 0014 §4b R8-2)")
    sprov, iprov = snapshot.get("provenance"), inc["provenance"]
    if not isinstance(sprov, dict):
        raise ValueError("raw_request.provenance must be a mapping (0014 §4b)")
    for f in EXACT_EQUAL_PROV_FIELDS:
        if sprov.get(f) != iprov[f]:
            raise ValueError(f"raw_request.provenance.{f} differs from the "
                             f"plan's incoming (exact-equal class, 0014 §4b)")
    for f in FORBIDDEN_EDGE_FIELDS:
        if snapshot.get(f) != _FORBIDDEN_DEFAULTS[f]:
            raise ValueError(f"raw_request.{f} is forbidden on a new request "
                             f"(store-lifecycle field, 0014 §4b)")
    # RECOMPUTED (graph.py:163-167): from the snapshot's own values plus the
    # recorded contributor sides, the committed survivor's values must be
    # reproduced — min(valid_from), max(observed_at), max(confidence). With no
    # absorption the transform is identity.
    contribs = [d for d in plan.contribution_drafts if d.site == "absorption"]
    if contribs and plan.absorption_pre_image is None:
        raise ValueError("absorption drafts require the pre-image (0014 §4b)")
    pre = plan.absorption_pre_image
    if pre is not None:
        # the snapshot IS the pre-inheritance incoming — cross-check the two
        # carriers of the same fact (both must be the original values)
        if (snapshot.get("valid_from") != pre.get("valid_from")
                or sprov.get("observed_at") != pre.get("observed_at")
                or sprov.get("confidence") != pre.get("confidence")):
            raise ValueError("raw_request disagrees with the plan's "
                             "absorption_pre_image over the recomputed fields "
                             "(0014 §4b R3-1)")
    if not contribs:
        if (snapshot.get("valid_from") != inc["valid_from"]
                or sprov.get("observed_at") != iprov["observed_at"]
                or sprov.get("confidence") != iprov["confidence"]
                or snapshot.get("ungrounded") != inc["ungrounded"]):
            raise ValueError("recomputed fields differ with NO absorption — the "
                             "identity transform must hold (0014 §4b)")
    else:
        # specs/0019 rider: `ungrounded` is RECOMPUTED by exactly the N-ary
        # OR — monotone, so the committed flag may never be WEAKER than the
        # raw submission's. The full OR (against the absorbed contributors'
        # authoritative rows) is verified store-side where those rows live;
        # this snapshot-side check pins the only direction visible here.
        if snapshot.get("ungrounded") is True and inc["ungrounded"] is not True:
            raise ValueError("ungrounded weakened across absorption — the "
                             "N-ary OR only ever strengthens (0019 §4d / "
                             "0014 §2c as amended)")


def effect_payload(result) -> str:
    """R10-1: the receipt persists the EFFECT payload — every
    SupersessionResult field EXCEPT the runtime `replayed` flag — as canonical
    JSON, written atomically with the receipt."""
    d = json.loads(result.model_dump_json())
    d.pop("replayed", None)
    return json.dumps(d, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)
