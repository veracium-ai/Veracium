"""Portable memory export/import — the no-lock-in guarantee, as a file format.

One JSONL file per user: a header line, then one record per line carrying the
FULL unit — provenance, disclosure, validity windows, supersession links,
invalidation reasons. Nothing is summarized or dropped: an import into a fresh
store reproduces the memory exactly, superseded history and quarantined claims
included. The wiki cache is deliberately not exported — it is a derived view
and recompiles from the store of record.

    {"kind": "veracium-export", "version": 2, "user_id": "...", "exported_at": "..."}
    {"record": "edge", ...Edge fields...}
    {"record": "episode", ...Episode fields...}
    {"record": "redaction", ...the attestation record + its source identity (format 13, specs/0041)...}

Format v2 renamed the per-line type marker from "kind" to "record" because
Episode gained its own `kind` field (outcome tracking); v1 files import
unchanged.

Import is idempotent: records whose id already exists in the target store are
skipped, never overwritten. `user_id=` remaps the import into a different user.

Trust note (specs/0005): provenance in an export file is *data*, and the
sentence "importing a file grants its records whatever authorship and
disclosure they claim" is true ONLY under `restore=True` — the operator's
explicit assertion that the file is this store's own history. The DEFAULT
import caps every record's trust instead: `author_of_evidence` and
`derived_from` are set to `THIRD_PARTY` and `disclosure` is floored to
`USE_ONLY` (`QUARANTINED` is never weakened), so nothing imported is
assertable or grounded as the target user's own testimony, regardless of what
the file claims, omits, or sets its header to.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .schema import (DEFAULT_RELATIONS, Disclosure, Edge, Episode, EvidenceAuthor,
                     Provenance, is_historical_id, is_procedural,
                     is_procedural_relation, to_historical_id)
from .scope_linkage import (derive_absorbed_by, plan_row_id,
                            reconstruct_absorption_rows)
from .source_identity import resolve_origin
from .attestation import DEFAULT_IMPORT as _DEFAULT_IMPORT, NOT_ATTESTED as _NOT_ATTESTED
from . import redaction as _redaction
from .store.base import DESTINATION_CHANGED, NON_QUIESCENT
from .census import declare_site

# specs/0042 (tranche 4): the enforcement points of this module, each a declared site the
# decision is returned THROUGH — consult() brackets the decision, fire() wraps the value
_SITE_EXPORT_NON_QUIESCENT = declare_site("portability.export.non-quiescent")
_SITE_IMPORT_CHAIN = declare_site("portability.import.chain")
_SITE_IMPORT_RESTORE_NOT_BOOL = declare_site("portability.import.restore-not-bool")
_SITE_IMPORT_RESTORE_WITH_USER = declare_site("portability.import.restore-with-user")
_SITE_IMPORT_FILE = declare_site("portability.import.file")
_SITE_IMPORT_AGREEMENT_INVALID = declare_site("portability.import.agreement-invalid")
_SITE_IMPORT_ORIGIN_MISSING = declare_site("portability.import.origin-missing")
_SITE_IMPORT_RECORD = declare_site("portability.import.record")
_SITE_IMPORT_RACE_EXHAUSTED = declare_site("portability.import.race-exhausted")
_SITE_IMPORT_PREFLIGHT = declare_site("portability.import.preflight")
# specs/0044 §4l (T11a): the arity era's refusals — the records' shape, the unit's admission, the staged-union decision
_SITE_IMPORT_ARITY_RECORDS = declare_site("portability.import.arity-records")
_SITE_IMPORT_ARITY_UNIT = declare_site("portability.import.arity-unit")
_SITE_IMPORT_ARITY_PREFLIGHT = declare_site("portability.import.arity-preflight")
_SITE_IMPORT_ACT_RECORDS = declare_site("portability.import.act-records")
_SITE_IMPORT_ACT_PREFLIGHT = declare_site("portability.import.act-preflight")
_SITE_IMPORT_AXIS = declare_site("portability.import.axis")

# specs/0014 §4c/§7a (R5-4): the exported Episode.consolidation_output_index
# field bumps the format 4→5 per accepted 0010's refuse-don't-drop rule — an
# older importer REFUSES a v5 export rather than silently dropping the field.
# specs/0019: v6 added the `ungrounded` flag (same refuse-don't-drop rule).
FORMAT_VERSION = 15  # specs/0031 v23.1 (§4f.3's portability row): the CALL-PATH era — `Provenance.call_path` on an
# edge or episode, or a confirmation line whose `call_path` is not `host_api`. Stamped CONDITIONALLY like every era
# below: a store holding no such record exports exactly the bytes it exported before (0026 V7); every older reader
# REFUSES a 15 file; a file declaring below 15 that carries either is REFUSED WHOLE, never stripped — a strip would
# move an agent's act to the host reading, the false record 0031 §4f §1d prevents (the arity era's rule, not the
# producer era's).
_CALL_PATH_VERSION = 15
#: the two AGENT call paths a confirmation line can carry (ConfirmationCallPath minus host_api). A line carrying any
#: OTHER value is not an agent path but a malformed one, refused by the act lines' closed shape (0047 I2), not here
_AGENT_CALL_PATHS = frozenset(("mcp_direct", "adapter_direct"))
# Was: FORMAT_VERSION = 14  # specs/0044 §4l (T11a, 2026-10-20): the ARITY era — a file may carry `{"record":
# "arity_outcome", ...}` lines (the user's migration outcomes for edges the file carries) and at most one
# `{"record": "arity_plan", "state": ...}` line (the EXPORTING store's plan state, written only when it holds a plan
# header: absence reads "uninitialized", so a feature-free export stays byte-identical — 0026 V7). Stamped
# CONDITIONALLY, like every era below; T11b extends the same era in place (no release falls between them).
_ARITY_VERSION = 14     # the arity era's own number: its gates key on it, never on the reader's head (T11b extends it)
_ACT_VERSION = 14       # specs/0008 §6d / 0047 §4f / 0045 §4f (T11b): the same era, extended in place — `confirmation`
# and `reply` lines (an act's origin, derived identity and position) and the edge's grounding axis `att`/`src`/`attv`
_REDACTION_VERSION = 13  # specs/0041 D2/§4g (tranche 4b, 2026-09-20): the REDACTION era — a file may carry
# `{"record": "redaction", ...}` lines, one per redaction record of the user (the attestation record with
# its SOURCE identity: origin, source user, source event ref; the carriers treated; the vocabulary reason;
# the marker version; never a content digest). Stamped CONDITIONALLY at write like every era below: an
# export from a store holding ANY redaction record is 13, which every older reader REFUSES ("newer than this
# Veracium understands" — the refuse-don't-drop rule; a reader that dropped the notice would import the
# record un-redacted, the exact harm §4g exists to prevent); a store without one exports 12 as before.
_PRODUCER_VERSION = 12  # specs/0037 v23 §4e: the PRODUCER era — `Provenance.producer`
# (which product path minted a procedural record). Stamped CONDITIONALLY at
# write, the same rule as every era below: an export from a store holding ANY
# producer-stamped record is 12, which every older reader REFUSES ("newer than
# this Veracium understands" — the refuse-don't-drop rule of 0010/0019/0026,
# V-OLD-READER-REFUSES); a store whose procedural records all predate the
# stamp exports 11 exactly as before.
_PROCEDURAL_VERSION = 11  # specs/0037 §4e: the PROCEDURAL era — `Provenance.record_kind` /
# `Provenance.basis`. Stamped CONDITIONALLY at write exactly as 0026 stamps 10:
# an export from a store holding ANY procedural record (stamp or basis) is 11,
# which every older reader REFUSES ("newer than this Veracium understands" —
# the refuse-don't-drop rule of 0010/0019/0026, V-OLD-READER-REFUSES); a
# procedural-free export stamps 10 (or 9 without agreements) and is
# byte-identical to the pre-feature file (V-DECLARATIVE-UNCHANGED).
_PRE_PROCEDURAL_VERSION = 10  # specs/0026 §3d: the Edge.agreement era. The bump is
                     # CONDITIONAL at write: an export from a store holding
                     # ANY agreement-bearing record stamps 10 so an old
                     # reader REFUSES rather than silently dropping the
                     # field; a marker-free export stamps the pre-agreement
                     # 9 and stays byte-compatible (V7's frozen oracle
                     # depends on exactly this).
_PRE_AGREEMENT_VERSION = 9  # specs/0001 (candidate): the ASSISTANT era —  # specs/0025 §2: the Edge.original_relation era — the
                    # field appears in exports only when non-None (the
                    # None-omission rule keeps unaffected edge payloads
                    # byte-identical); a v7 export imports absent→None; OLD
                    # readers REFUSE v8 — the gate working, not a failure.
                    # (v7: specs/0016 D2 / 0019 rider A3, the source_type-less
                    # file — a v7 export omits the deleted key entirely; an
                    # OLD build's Provenance REQUIRED source_type, so without
                    # the bump a new export died there as a pydantic error —
                    # the bump makes it an honest version refusal. A ≤6
                    # file's provenance.source_type key is DROPPED on import
                    # (the record otherwise intact, §2c row 1).
                    # specs/0021 §7b (the 0016/0018 rider): a v7 edge record
                    # MAY carry `absorbed_by_id` — present iff the record is
                    # an absorbed_duplicate with a unique CANONICAL ledger
                    # row naming it (derive_absorbed_by, NEVER from notes);
                    # importers consume it as 0020 §4a-iii's structured
                    # carrier; files without it take the legacy note rule.
_IMPORT_RETRIES = 8   # bounded whole-import retries before refusing a persistent race

# specs/0005 §4d — the PINNED default-path refusal warning (P10/P15). A bare
# pointer at --restore would recruit the operator into the bypass on a
# tampered own-export; the message must carry both halves.
_RESTORE_WARNING = (
    "import refused: existing records differ from the capped incoming form. "
    "If - and only if - this file is your own store's export, --restore "
    "imports it with trust preserved. --restore trusts every record in the "
    "file exactly as written, and applies its redaction notices to the records "
    "you hold; use it only on a file you exported yourself or "
    "have independently verified, record by record (specs/0005 §4d)")


_GROUNDING_AXIS = ("att", "src", "attv")    # specs/0045 §2: the declarative grounding axis's stored fields

# specs/0044 §4l (T11a): the arity-era records' closed shapes
_ARITY_PLAN_STATES = ("initialized-empty", "initialized")      # "uninitialized" is the ABSENCE of the record
_OUTCOME_KEYS = frozenset(("outcome_uid", "plan_id", "edge_id", "outcome", "pre_invalidated_at", "pre_reason",
                           "successor_evidence", "stage", "origin", "undone_at"))
_OUTCOME_STAGES = ("live", "ended", "undone")


def _outcome_stage(row: dict) -> str:
    """0044 §4l's lifecycle STAGE of a held row: `undone`, else `live` (applicable), else `ended`."""
    return "undone" if row["undone_at"] is not None else ("live" if row["applicable"] else "ended")


def _canon_instant(value):
    """0044 §4l / build note D15 (research T2): an outcome's time as ONE canonical text, UTC `isoformat()`, so 'Z' and
    '+00:00' compare equal; None for a NAIVE or malformed value, which the caller refuses — never compared, never
    assumed UTC."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else None
    except ValueError:
        dt = None
    return None if dt is None or dt.tzinfo is None else dt.astimezone(timezone.utc).isoformat()


def _outcome_projection(o: dict) -> tuple:
    """0044 §4l's canonical comparison projection (v1.5, R3-02): uid, plan, edge (after remapping), outcome, the
    pre-state, the successor evidence (remapped) and the STAGE — never the row id, the write time, the trust label,
    `undo_request_ref` or `undone_at`'s value."""
    return (o["outcome_uid"], o["plan_id"], o["edge_id"], o["outcome"], o["pre_invalidated_at"], o["pre_reason"],
            json.dumps(o["successor_evidence"], separators=(",", ":")), o["stage"])


def _arity_records(path, outcome_recs, plan_recs, src_version) -> tuple:
    """0044 §4l (T11a): the arity era's records validated WHOLE before any record is admitted — (outcomes, the source's
    plan state). Refuse-don't-drop both ways: an arity record in an envelope declaring an older format, a second or
    unknown plan-state record, or an outcome outside its closed shape refuses the import (build note D14)."""
    with _SITE_IMPORT_ARITY_RECORDS.consult():
        if (outcome_recs or plan_recs) and src_version < _ARITY_VERSION:
            raise _SITE_IMPORT_ARITY_RECORDS.fire(ValueError(
                f"{path}: the file declares format {src_version} but carries arity records (format {_ARITY_VERSION}) "
                f"— refused (specs/0044 §4l)"), "record-below-era")
        if len(plan_recs) > 1 or any(set(r) != {"state"} or r.get("state") not in _ARITY_PLAN_STATES
                                     for r in plan_recs):
            raise _SITE_IMPORT_ARITY_RECORDS.fire(ValueError(
                f"{path}: the file's arity plan-state record is repeated or outside {list(_ARITY_PLAN_STATES)} — "
                f"refused (specs/0044 §4l)"), "plan-state")
        state = plan_recs[0]["state"] if plan_recs else "uninitialized"
        def _utf8(v):                               # research's T11a S2-5: a lone surrogate refuses here, never at the INSERT
            try:
                v.encode("utf-8")
                return True
            except UnicodeEncodeError:
                return False
        out = []
        for r in outcome_recs:
            succ = r.get("successor_evidence")
            ok = (set(r) == _OUTCOME_KEYS
                  and all(isinstance(r[k], str) and r[k] for k in ("outcome_uid", "plan_id", "edge_id", "pre_reason"))
                  and r["outcome"] in ("restored", "withheld_revoked") and r["stage"] in _OUTCOME_STAGES
                  and r["origin"] in ("local", "restored", "imported")
                  and isinstance(succ, list) and len(succ) == 2 and isinstance(succ[1], list)
                  and all(isinstance(x, str) and x for x in succ[1])
                  and ((succ[0] == "pointer" and succ[1]) or (succ[0] == "none" and not succ[1]))
                  and (r["stage"] == "undone") == (r["undone_at"] is not None)
                  and (r["outcome"] != "withheld_revoked" or r["stage"] == "ended")       # S2-5: never applicable
                  and all(_utf8(r[k]) for k in ("outcome_uid", "plan_id", "edge_id", "pre_reason"))
                  and all(_utf8(x) for x in succ[1]))
            if not ok:
                raise _SITE_IMPORT_ARITY_RECORDS.fire(ValueError(
                    f"{path}: arity outcome {r.get('outcome_uid')!r} is outside its closed shape — refused, nothing "
                    f"imported (specs/0044 §4g, §4l)"), "outcome-shape")
            o = dict(r)
            o["pre_invalidated_at"] = _canon_instant(r["pre_invalidated_at"])
            o["undone_at"] = None if r["undone_at"] is None else _canon_instant(r["undone_at"])
            if o["pre_invalidated_at"] is None or (r["undone_at"] is not None and o["undone_at"] is None):
                raise _SITE_IMPORT_ARITY_RECORDS.fire(ValueError(
                    f"{path}: arity outcome {r['outcome_uid']!r} carries a time that is not a timezone-aware ISO-8601 "
                    f"instant — refused, nothing imported (specs/0044 §4l)"), "outcome-time")
            out.append(o)
        return out, state


def _remap_outcomes(outcomes, remap, remapping, target_uid) -> list:
    """0044 §4l "the edge reference after user and id remapping"; build note D11 (research's Q3): under a cross-user
    remap an outcome's uid is RE-MINTED with its edge — derived from the file's uid (which carries the origin store and
    plan) and the destination user and edge — so outcomes duplicate exactly when their edges do."""
    from .store.data_migration import portable_uid
    out = []
    for o in outcomes:
        o = dict(o)
        o["edge_id"] = remap(o["edge_id"])
        o["successor_evidence"] = [o["successor_evidence"][0], [remap(x) for x in o["successor_evidence"][1]]]
        if remapping:
            o["outcome_uid"] = portable_uid("remapped", o["outcome_uid"], target_uid, o["edge_id"])
        out.append(o)
    return out


def _validate_outcome_unit(path, outcomes, edge_recs) -> list:
    """0044 §4l's whole-unit validation, before any write, over the FILE: every outcome's edge is in the unit; a uid
    repeated in the unit is the same projection (else refused); one outcome per destination edge in the unit (build
    note D6c); the edge's state agrees with the outcome — a live `restored` ⇒ active, `undone` ⇒ retired with the
    recorded pre-state (an instant comparison). Returns the deduplicated outcomes."""
    from .store import lifetime as _lifetime
    by_edge = {r.get("id"): r for r in edge_recs}
    with _SITE_IMPORT_ARITY_UNIT.consult():
        uniq: dict = {}
        for o in outcomes:
            held = uniq.get(o["outcome_uid"])
            if held is not None and _outcome_projection(held) != _outcome_projection(o):
                raise _SITE_IMPORT_ARITY_UNIT.fire(ValueError(
                    f"{path}: arity outcome {o['outcome_uid']!r} appears twice with different contents — refused "
                    f"(specs/0044 §4l)"), "outcome-uid-conflict")
            uniq[o["outcome_uid"]] = o
        seen: dict = {}
        for o in uniq.values():
            e = by_edge.get(o["edge_id"])
            if e is None:
                raise _SITE_IMPORT_ARITY_UNIT.fire(ValueError(
                    f"{path}: arity outcome {o['outcome_uid']!r} names edge {o['edge_id']!r}, which the file does not "
                    f"carry — refused (specs/0044 §4l: every outcome's edge is in the unit)"), "outcome-edge-not-in-unit")
            if o["edge_id"] in seen:
                raise _SITE_IMPORT_ARITY_UNIT.fire(ValueError(
                    f"{path}: edge {o['edge_id']!r} has two arity outcomes in the file ({seen[o['edge_id']]!r}, "
                    f"{o['outcome_uid']!r}) — refused (specs/0044 §4l, one outcome per edge)"), "outcome-slot")
            seen[o["edge_id"]] = o["outcome_uid"]
            missing = [x for x in o["successor_evidence"][1] if x not in by_edge]
            if missing:
                raise _SITE_IMPORT_ARITY_UNIT.fire(ValueError(
                    f"{path}: arity outcome {o['outcome_uid']!r} names successor(s) {missing!r} the file does not carry "
                    f"— a remapped reference that does not resolve refuses the whole unit (specs/0044 §4l)"),
                    "outcome-successor-unresolved")
            retired = _lifetime.retirement(e)
            if o["outcome"] == "restored" and o["stage"] == "live" and retired is not None:
                raise _SITE_IMPORT_ARITY_UNIT.fire(ValueError(
                    f"{path}: arity outcome {o['outcome_uid']!r} is a live restoration of edge {o['edge_id']!r}, which "
                    f"the file carries retired — refused (specs/0044 §4l)"), "outcome-edge-state")
            if o["stage"] == "undone" and not _lifetime.same_retirement(retired, (o["pre_invalidated_at"], o["pre_reason"])):
                raise _SITE_IMPORT_ARITY_UNIT.fire(ValueError(
                    f"{path}: arity outcome {o['outcome_uid']!r} is undone, but edge {o['edge_id']!r} is not retired "
                    f"with the recorded pre-state — refused (specs/0044 §4l)"), "outcome-edge-state")
        return list(uniq.values())


def _without_axis(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in _GROUNDING_AXIS}


# specs/0008 §6e–§6f / 0047 §4f (T11b): the act lines' closed shapes. No row id travels (destination-internal, §6e):
# an act's file identity IS its `act_uid`, a resolve names its challenge by `target_uid`, and the position's store is
# the uid's store (one `origin_store` column carries both, §2a), so the wire does not repeat it (build note D1)
_ACT_KEYS = {
    "confirmation": frozenset(("act_uid", "act_seq", "edge_id", "confirmed_at", "actor", "call_path",
                               "recorded_correlation_id", "request_digest", "origin")),
    "reply": frozenset(("act_uid", "act_seq", "edge_id", "kind", "target_uid", "text", "actor",
                        "recorded_correlation_id", "request_digest", "origin", "written_at")),
}
_ACT_TABLE = {"confirmation": "confirmations", "reply": "replies"}
_ACT_NOUN = {table: marker for marker, table in _ACT_TABLE.items()}     # research's T11b landing nit: never `[:-1]`
_PROOF = ("local", "restored")          # 0008 §3a: the origins that are proof; `imported` is testimony


def _utf8(v) -> bool:
    try:
        v.encode("utf-8")
        return True
    except UnicodeEncodeError:
        return False


def _act_records(path, act_recs, src_version) -> list:
    """specs/0008 §6e / 0047 §4f (T11b, build note D13): the act lines validated WHOLE before any record is admitted.
    Refuse-don't-drop below the era (an act line in an envelope declaring an older format); a closed shape per kind —
    an `act_uid` of three non-empty strict-UTF-8 strings (absent refuses: a store never mints an `act_uid` for an act it
    did not originate), a positive position or null (unknown), the closed origin, actor, call-path and kind sets, a
    target iff `resolve` and text iff not (add_reply's shape rule), no marker INSIDE a text (the treated shape is the
    marker whole), a digest of 64 hex or the marker, an original request id in the caller's grammar or null; and every
    time a timezone-aware instant re-rendered as canonical UTC `isoformat()` (D3–D5: 'Z' and offsets agree, a naive
    time refuses). Returns normalised dicts."""
    from .schema import ConfirmationActor, ConfirmationCallPath, ReplyActor, REPLY_KINDS, _CORRELATION_ID_RE
    from .store.sqlite import _reply_shape_problem
    with _SITE_IMPORT_ACT_RECORDS.consult():
        if act_recs and src_version < _ACT_VERSION:
            raise _SITE_IMPORT_ACT_RECORDS.fire(ValueError(
                f"{path}: the file declares format {src_version} but carries confirmation or reply lines (format "
                f"{_ACT_VERSION}) — refused (specs/0008 §6d, 0047 §4f)"), "record-below-era")
        out = []
        for marker, r in act_recs:
            uid = r.get("act_uid")
            seq = r.get("act_seq")
            tuid = r.get("target_uid")
            orig = r.get("recorded_correlation_id")
            dig = r.get("request_digest")
            def _uid_ok(u):
                return isinstance(u, list) and len(u) == 3 and all(isinstance(x, str) and x and _utf8(x) for x in u)
            ok = (set(r) == _ACT_KEYS[marker] and _uid_ok(uid)
                  and (seq is None or (isinstance(seq, int) and not isinstance(seq, bool) and seq >= 1))
                  and isinstance(r["edge_id"], str) and r["edge_id"] and _utf8(r["edge_id"])
                  and r["origin"] in ("local", "imported", "restored")
                  and (orig is None or (isinstance(orig, str) and _CORRELATION_ID_RE.fullmatch(orig) is not None))
                  and isinstance(dig, str) and (dig == _redaction.MARKER or (len(dig) == 64 and all(
                      c in "0123456789abcdef" for c in dig))))
            if ok and marker == "confirmation":
                ok = (r["actor"] in {a.value for a in ConfirmationActor}
                      and r["call_path"] in {c.value for c in ConfirmationCallPath})
            elif ok:
                text = r["text"]
                ok = (r["kind"] in REPLY_KINDS and r["actor"] in {a.value for a in ReplyActor}
                      and (tuid is None or _uid_ok(tuid))
                      and _reply_shape_problem(r["kind"], text, None if tuid is None else "target") is None
                      and (text is None or text == _redaction.MARKER or not _redaction.carries_marker(text)))
            if not ok:
                raise _SITE_IMPORT_ACT_RECORDS.fire(ValueError(
                    f"{path}: {marker} {uid!r} is outside its closed shape — refused, nothing imported (specs/0008 "
                    f"§6e, 0047 §4b/§4f)"), "act-shape")
            times = ("confirmed_at",) if marker == "confirmation" else ("written_at",)
            a = {"table": _ACT_TABLE[marker], "act_uid": tuple(uid), "act_seq": seq, "edge_id": r["edge_id"],
                 "kind": "confirm" if marker == "confirmation" else r["kind"],
                 "target_uid": None if tuid is None else tuple(tuid), "text": r.get("text"), "actor": r["actor"],
                 "call_path": r.get("call_path"), "confirmed_at": None, "written_at": None,
                 "recorded_correlation_id": orig, "request_digest": dig, "origin": r["origin"]}
            for k in times:
                a[k] = _canon_instant(r[k])
                if a[k] is None:
                    raise _SITE_IMPORT_ACT_RECORDS.fire(ValueError(
                        f"{path}: {marker} {uid!r} carries a {k} that is not a timezone-aware ISO-8601 instant — refused, "
                        f"nothing imported (specs/0008 §6e: normalised dates)"), "act-time")
            out.append(a)
        return out


def _remap_namespace(uid: tuple, target_uid: str, import_op: str) -> tuple:
    """The owner's R-D6 ruling (2026-10-20; build note D6): under a cross-user remap an act moves into a REMAP
    NAMESPACE — its store becomes a hash of (origin store, destination user, this import's operation id), its user the
    destination's, its act id and position kept. Outcomes re-mint only user and edge because nothing orders them; an act
    also has a POSITION, and a second remapped copy at the source's positions would tie (§6f), so the namespace is per
    import: acts duplicate exactly when their edges do, and a copy keeps its own order."""
    from .store.data_migration import portable_uid
    return ("remap:" + portable_uid("remapped", uid[0], target_uid, import_op)[:32], target_uid, uid[2])


def _remap_acts(acts, remap, remapping, target_uid, import_op) -> list:
    out = []
    for a in acts:
        a = dict(a, edge_id=remap(a["edge_id"]))
        if remapping:
            a["act_uid"] = _remap_namespace(a["act_uid"], target_uid, import_op)
            if a["target_uid"] is not None:
                a["target_uid"] = _remap_namespace(a["target_uid"], target_uid, import_op)
        out.append(a)
    return out


def _axis_records(path, edge_recs, src_version, restore) -> list:
    """specs/0045 §2c/§4e/§4f (T11b, build note D10, research's M4): the grounding axis at the import boundary. Below
    era 14 it is newer than the declared format and STRIPPED (0006 I10). From era 14 the file's values are CHECKED in
    BOTH modes before anything is written or stamped — an `att` outside its two values, an `attv` outside its grammar
    (every version the grammar admits: versions coexist, INV-G13), an `attv` or `src` without `att`, the axis on a
    procedural record, or a `src` that is not a non-empty string → the unit refused. Then the mode's write rule: a
    DEFAULT import writes `not_attested`, NULL, `default-import` whatever the file says (INV-G9); a TRUSTED RESTORE keeps
    the recorded values (INV-G13), a `src` naming no held or carried episode admitted (the owner's F1(b): a deleted or
    consumed source names nothing)."""
    from .attestation import valid_attv
    with _SITE_IMPORT_AXIS.consult():
        for rec in edge_recs:
            if src_version < _ACT_VERSION:
                for k in _GROUNDING_AXIS:
                    rec.pop(k, None)
            else:
                att, src, attv = (rec.get(k) for k in _GROUNDING_AXIS)
                problem = ("att" if att not in (None, "attested", "not_attested")
                           else "attv" if attv is not None and not valid_attv(attv)
                           else "without-att" if att is None and (attv is not None or src is not None)
                           else "procedural" if _raw_procedural(rec) and (att, src, attv) != (None, None, None)
                           else "src" if src is not None and not (isinstance(src, str) and src and _utf8(src))
                           else None)
                if problem is not None:
                    raise _SITE_IMPORT_AXIS.fire(ValueError(
                        f"{path}: edge {rec.get('id')!r} carries a grounding axis outside its rules ({problem}: att="
                        f"{att!r}, attv={attv!r}, src={src!r}) — refused, nothing imported (specs/0045 §2c)"),
                        f"axis-{problem}")
            if not restore:
                for k in _GROUNDING_AXIS:
                    rec.pop(k, None)
                if not _raw_procedural(rec):
                    rec["att"], rec["attv"] = _NOT_ATTESTED, _DEFAULT_IMPORT
        return edge_recs


def _held_act_uid(row: dict, local: str) -> tuple:
    """specs/0008 §6e v7: a held act's portable identity — DERIVED for a local act (its origin columns are NULL: this
    store's origin, its own user and id), stored for an imported or restored one."""
    if row["origin_store"] is None:
        return (local, row["user_id"], row["id"])
    return (row["origin_store"], row["origin_user"], row["origin_act_id"])


def _held_original_id(row: dict):
    """§6e: the ORIGINAL request's id — a local act's own `correlation_id`, else its recorded one; an internal key never."""
    if row["origin"] == "local":
        return None if row["correlation_id"].startswith("#act:") else row["correlation_id"]
    return row["recorded_correlation_id"]


def _act_projection(a: dict, cov) -> tuple:
    """specs/0008 §6e's canonical TREATED projection: identity, edge (after remapping), kind, target (portable), actor,
    call path, `confirmed_at` (canonical UTC), the content carriers (`text`, `request_digest`) — each replaced by the
    marker where the coverage attests it — the original request id, and the position. Never the row id, the internal
    key, the registry, `written_at` or the trust label (D3)."""
    prefix = "confirmations." if a["table"] == "confirmations" else "replies."
    text = a["text"]
    if text is not None and "replies.text" in cov:
        text = _redaction.MARKER
    dig = _redaction.MARKER if prefix + "request_digest" in cov else a["request_digest"]
    return (a["act_uid"], a["edge_id"], a["kind"], a["target_uid"], a["actor"], a["call_path"], a["confirmed_at"],
            text, dig, a["recorded_correlation_id"], a["act_seq"])


def _act_ordered(a: dict, b: dict, restore: bool):
    """specs/0008 §6f: True when `a` precedes `b` (same `origin_store`, both positions known, lower `act_seq`), False
    when `b` precedes `a`, None when incomparable — except the owner's R-M1 ruling (2026-10-20): in a TRUSTED RESTORE,
    between two PROOF acts (recorded `local`/`restored`) of one origin, an UNKNOWN position precedes every known one
    (§2a: "no legacy act receives a value" — the counter starts at the v16 step). Testimony stays incomparable."""
    if a["act_uid"][0] != b["act_uid"][0]:
        return None
    sa, sb = a["act_seq"], b["act_seq"]
    if sa is not None and sb is not None:
        return sa < sb
    if restore and (sa is None) != (sb is None) and a["label"] in _PROOF and b["label"] in _PROOF:
        return sa is None
    return None


def _raw_procedural(rec: dict) -> bool:
    """0037's floor rule on a raw file record: `record_kind == "procedural"` OR `basis` set."""
    prov = rec.get("provenance") if isinstance(rec.get("provenance"), dict) else {}
    return prov.get("record_kind") == "procedural" or prov.get("basis") is not None


def export_memory(store, user_id: str, path) -> dict:
    """Write `user_id`'s complete memory (all edges incl. superseded and
    quarantined, all episodes) to `path` as JSONL. Returns counts."""
    # specs/0010 §4f/X17: export is a READ-ONLY quiescent snapshot. The quiescence
    # check and the episode snapshot are ONE atomic, linearizable observation — a
    # claim starting mid-export yields NON_QUIESCENT, never a dangling `claimed_by`.
    # Export never mutates; the caller runs consolidate()/maintain() first and retries.
    episodes = store.quiescent_episode_snapshot(user_id)
    with _SITE_EXPORT_NON_QUIESCENT.consult():
        if episodes is NON_QUIESCENT:
            raise _SITE_EXPORT_NON_QUIESCENT.fire(ValueError(
                f"export refuses: a consolidation is in flight for {user_id!r} — run "
                f"consolidate()/maintain() to settle it, then retry (specs/0010 §4f)"))
    edges = store.edges(user_id, active_only=False, include_quarantined=True)
    # specs/0006 §4 rule 3/6 — MATERIALISE the resolved origin on export so the file is
    # self-describing (I6). A local record (origin absent) is written with THIS store's
    # singleton; a foreign/imported record keeps its own (resolve_origin). This is what
    # lets a local source survive an export→import round-trip and group as one (I9).
    local = store.local_origin()

    def _materialise(rec: dict) -> dict:
        prov = rec.get("provenance")
        if isinstance(prov, dict):
            prov["origin"] = resolve_origin(prov.get("origin"), local)
        return rec

    # specs/0021 §7b — the FORMAT-7 `absorbed_by_id` rider (0016/0018
    # amendment): for every absorbed_duplicate record, derive the structured
    # reverse link from the ledger's TYPED `contributor_ref` rows via the
    # canonical-class algorithm (`derive_absorbed_by` — direct or reparented
    # rows only; plain flattened copies and markers never), NEVER from notes.
    # Exactly one canonical row → the field is written; zero (incl. the
    # disclosed legacy class: pre-v8 rows carry NULL contributor_ref and
    # never match) → the field is OMITTED and the record travels legacy;
    # more than one → ExportLinkageError refuses the WHOLE export — derived
    # BEFORE the file opens, so a corrupt ledger never yields a partial file.
    absorbed_by: dict = {}
    for e in edges:
        if e.invalidation_reason != "absorbed_duplicate":
            continue
        ledger_rows: dict = {}
        for row in store.contributions_naming(user_id, e.id):
            if row["survivor_type"] != "edge":
                continue
            ledger_rows.setdefault(row["survivor_id"], []).append(row)
        winner = derive_absorbed_by(e.id, ledger_rows)   # >1 canonical raises
        if winner is not None:
            absorbed_by[e.id] = winner

    path = Path(path)
    with path.open("w") as f:
        # specs/0026 §3d / specs/0037 §4e: the conditional stamp (see
        # FORMAT_VERSION) — the highest era any record in the file needs
        # specs/0041 §11.6.6 (T4; research's B1): which notices an export carries. An APPLIED record exports treated,
        # so its pair always SHOWS the redaction; a STANDING row travels only when the file does NOT carry its target
        # (it re-arrives standing). A PENDING notice never travels: its target is held and untreated by definition, so
        # exporting it beside its record would make the store's OWN export unrestorable (the table refuses a unit
        # carrying a record unredacted beside its notice) — measured at a2dc7b0 for a standing notice over a local
        # write, refused three ways. The cost, stated: a restore does not reproduce pending state; re-importing the
        # source file re-pends it. Relaying pending testimony would need an unauthenticated state label (INV-RR14).
        _carried = {("edge", e.id) for e in edges} | {("episode", ep.id) for ep in episodes}
        redaction_records = [r for r in store.redaction_records(user_id)
                             if r["state"] == "applied"
                             or (r["state"] == "standing" and (r["target_kind"], r["target_id"]) not in _carried)]
        # specs/0044 §4l (T11a): the user's outcomes for edges this file carries, and the store's plan state — the
        # record written ONLY when a plan header exists (its absence reads "uninitialized": research's D2, so a
        # feature-free export stays byte-identical, 0026 V7). A backend with no arity tables holds neither.
        _edge_ids = {e.id for e in edges}
        try:
            arity_outcomes = [r for r in store.migration_outcomes(user_id) if r["edge_id"] in _edge_ids]
            plan_state = store.arity_plan_state()["state"]
        except NotImplementedError:
            arity_outcomes, plan_state = [], "uninitialized"
        # specs/0008 §6d / 0047 §4f (T11b): the user's acts, with their origin; never the request registry
        acts = store.act_rows(user_id)
        _version = (_CALL_PATH_VERSION
                    if (any(e.provenance.call_path is not None for e in edges)
                        or any(ep.provenance.call_path is not None for ep in episodes)
                        or any(r["table"] == "confirmations" and r["call_path"] != "host_api" for r in acts))
                    else _ARITY_VERSION
                    if arity_outcomes or plan_state != "uninitialized" or acts or any(e.att is not None for e in edges)
                    else _REDACTION_VERSION
                    if redaction_records
                    else _PRODUCER_VERSION
                    if any(e.provenance.producer is not None for e in edges)
                    else _PROCEDURAL_VERSION
                    if any(is_procedural(e) for e in edges)
                    else _PRE_PROCEDURAL_VERSION
                    if any(e.agreement is not None for e in edges)
                    else _PRE_AGREEMENT_VERSION)
        f.write(json.dumps({"kind": "veracium-export", "version": _version,
                            "user_id": user_id,
                            "exported_at": datetime.now(timezone.utc).isoformat()})
                + "\n")
        for e in edges:
            # specs/0045 §4f (T11b): the grounding axis travels on the edge line, `attv` WITH `att` (INV-G13); a None
            # field is omitted (Edge's serialisation), so a legacy row's bytes are unchanged and stamp no era
            rec = _materialise(json.loads(e.model_dump_json()))
            if e.id in absorbed_by:
                rec["absorbed_by_id"] = absorbed_by[e.id]
            f.write(json.dumps({"record": "edge", **rec}) + "\n")
        for ep in episodes:
            rec = _materialise(json.loads(ep.model_dump_json()))
            # specs/0014 §4c (R7-3): the index serializes with EXCLUDE-NONE
            # semantics — OMITTED when None (a stated exception to the default;
            # an explicit null on import is malformed). A native v5 output
            # always carries its index; absence is the unprivileged legacy shape.
            if rec.get("consolidation_output_index") is None:
                rec.pop("consolidation_output_index", None)
            f.write(json.dumps({"record": "episode", **rec}) + "\n")
        # specs/0041 D2 (tranche 4b): the redaction records travel — the record itself travels redacted (its
        # json holds the marker), and the notice is what lets the destination ATTEST it (§4g). Source identity
        # materialised: this store's origin for its own redactions, the original source's for witnessed ones.
        # Round 10 (R9-05): the notice's BODY is the source's own — this store's facts for its own redaction, the
        # immutable foreign body for a witnessed one — so a relay re-exports the source's reason, time and store
        # versions unchanged, and an original and its honest relay are one notice wherever they meet.
        for r in redaction_records:
            f.write(json.dumps({"record": "redaction", "origin": r["origin"], "source_user": r["source_user"],
                                "source_event_ref": r["source_event_ref"], "target_kind": r["target_kind"],
                                "target_id": r["target_id"], **r["notice_body"]}) + "\n")
        # specs/0044 §4l: the outcome's projection fields, its STAGE, and its trust label (the destination maps it by
        # the origin matrix); never `undo_request_ref` (store-local, §4g) and never `op_id` (this store's operation)
        if plan_state != "uninitialized":
            f.write(json.dumps({"record": "arity_plan", "state": plan_state}) + "\n")
        for r in arity_outcomes:
            f.write(json.dumps({"record": "arity_outcome", "outcome_uid": r["outcome_uid"], "plan_id": r["plan_id"],
                                "edge_id": r["edge_id"], "outcome": r["outcome"],
                                "pre_invalidated_at": _held_instant(r["pre_invalidated_at"]),
                                "pre_reason": r["pre_reason"], "successor_evidence": json.loads(r["successor_evidence"]),
                                "stage": _outcome_stage(r), "origin": r["origin"],
                                "undone_at": None if r["undone_at"] is None else _held_instant(r["undone_at"])}) + "\n")
        # specs/0008 §6e–§6f (T11b, build note D1–D2): each act with its origin, its portable identity (DERIVED for a
        # local act, §6e v7: this store's origin, its own user and id — export stays read-only), its position (NULL:
        # unknown, never synthesized), and the ORIGINAL request's id (never an internal `#act:` key); no row id, no
        # internal key, no registry row. A resolve names its challenge by identity
        uid_of = {r["id"]: list(_held_act_uid(r, local)) for r in acts}
        # research's T11b S2-2: an act whose edge this store no longer holds is CORRUPTION (no verb writes one; an edge
        # leaves only with its user's acts, by erasure) — exported as held and REPORTED, never refused here: refusing
        # would remove the whole backup. Its import refuses whole (INV-R11)
        orphaned = sum(r["edge_id"] not in _edge_ids for r in acts)
        for r in acts:
            line = {"record": "confirmation" if r["table"] == "confirmations" else "reply",
                    "act_uid": uid_of[r["id"]], "act_seq": r["act_seq"], "edge_id": r["edge_id"]}
            if r["table"] == "confirmations":
                line.update(confirmed_at=_held_instant(r["confirmed_at"]), actor=r["actor"], call_path=r["call_path"])
            else:
                line.update(kind=r["kind"], target_uid=None if r["target"] is None else uid_of.get(r["target"]),
                            text=r["text"], actor=r["actor"], written_at=_held_instant(r["written_at"]))
            line.update(recorded_correlation_id=_held_original_id(r), request_digest=r["request_digest"],
                        origin=r["origin"])
            f.write(json.dumps(line) + "\n")
    return {"edges": len(edges), "episodes": len(episodes), "redactions": len(redaction_records),
            "outcomes": len(arity_outcomes), "confirmations": sum(r["table"] == "confirmations" for r in acts),
            "replies": sum(r["table"] == "replies" for r in acts), "acts_orphaned": orphaned, "path": str(path)}


# specs/0014 §2c (R11-3/R12-3/R13-2): the source-identity projection over TWO
# EXACT SETS, riding accepted 0010's stable historical namespace. EXCLUDED =
# destination-minted, no source meaning; VERBATIM = everything else, compared
# byte-for-byte after JSON-mode dump — INCLUDING lineage (historical ids are
# stable across export/import by X18's design: never remapped) and the
# operation reference (X19's transform is deterministic and retry-stable, so
# post-transform comparison is direct equality). There is NO normalized set —
# nothing in the shipped boundary rewrites these references.
PROJECTION_EXCLUDED_FIELDS = ("id", "user_id")
PROJECTION_VERBATIM_FIELDS = tuple(
    f for f in Episode.model_fields if f not in PROJECTION_EXCLUDED_FIELDS)


def source_identity_projection(record: dict) -> dict:
    """The canonical projection of an (imported or stored) indexed-output
    episode record: the JSON-form dict minus exactly the EXCLUDED fields.
    Absent optional keys and present-with-default keys compare equal by
    normalizing through the model dump."""
    ep = Episode.model_validate({k: v for k, v in record.items()
                                 if k in Episode.model_fields})
    d = json.loads(ep.model_dump_json())
    for f in PROJECTION_EXCLUDED_FIELDS:
        d.pop(f, None)
    return d


# Round 13 (0041 R12-01): the 0014 §2c RIDER's one admitted class. Fields that, differing, are never a redaction:
# the output's identity and its history (the key's operation and index are equal by construction of the collision).
HELD_OUTPUT_STRUCTURE = ("lineage", "operation_id", "consolidation_output_index")


def held_output_redaction(held: dict, incoming: dict, notice_fields) -> bool:
    """0014 §2c as amended by 0041 (round 13; the owner's approval 2026-10-05): an incoming lineage-bearing output
    colliding with a HELD one admits a verbatim difference iff it is a REDACTION OF THAT OUTPUT — a notice for it exists
    (its `fields` passed here; None when there is none), every differing field is named by that notice AND is an
    episode record carrier path, and for each such field the held value or the incoming value carries the marker. Any
    difference in the output's structure (`HELD_OUTPUT_STRUCTURE`) is never one. Pure: the caller decides what follows
    (the arrival is not installed; the notice binds to the held id). An EQUAL projection is the idempotent path, not
    this class, so it returns False."""
    from .redaction import MARKER, attestation_paths
    if notice_fields is None:
        return False
    a, b = source_identity_projection(held), source_identity_projection(incoming)
    differing = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
    if not differing or differing & set(HELD_OUTPUT_STRUCTURE):
        return False
    if not differing <= (attestation_paths("episode") & set(notice_fields)):
        return False
    # round 14 (R13-02): the rider's third condition is that the held OR the incoming VALUE IS the marker — the whole
    # value, compared exactly. Round 13 asked `marker_fields`, whose `carries_marker` is a SUBSTRING test (the right test
    # for ordinary-write reservation and unattested-marker diagnostics, which keep it), and so admitted prefix+MARKER+suffix
    return all(a.get(k) == MARKER or b.get(k) == MARKER for k in differing)


# Round 11 (R10-01): the STRUCTURE of an outcome link — the chain's topology and the chain key's evidence_ref half —
# NAMED, not inferred. A held link differing here is a topology conflict and refuses whatever notice accompanies it
# (INV-1, §4h; the verdict: "this does not authorize overwriting outcome history"); a held link equal here and
# differing elsewhere differs in CONTENT, which the held-differs rule shared with edges and episodes decides.
OUTCOME_LINK_STRUCTURE = ("id", "user_id", "kind", "edge_id", "seq", "supersedes_episode", "provenance.evidence_ref")


def _outcome_structure(ep: Episode) -> tuple:
    d = ep.model_dump(mode="json")
    return tuple(d["provenance"]["evidence_ref"] if f == "provenance.evidence_ref" else d.get(f)
                 for f in OUTCOME_LINK_STRUCTURE)


def held_differs_verdict(attested_complete: bool, noticed: bool) -> str:
    """specs/0041 §4g — the ONE held-differs rule, for every record kind (round 11, R10-01; it was the edge and
    non-outcome episode branches' rule, and the outcome branch had none). The destination holds the record with
    DIFFERENT content:
      • it ATTESTS a redaction of it and the file carries no notice → "attested-redaction" (INV-11 at the import
        boundary);
      • the file's notice names it → "inconsistent": content-derived divergence is no ground to keep content the
        source says was redacted — the held version is redacted anyway (the notice applies in the commit), the
        incoming copy is not written, and the import flags it in `inconsistent_notices` — on a RESTORE whose file
        shows the redaction; on the default path (specs/0041 §11.6.6) a notice over a held record is PENDING, never
        applied: the held version is kept, the incoming copy is still not written, and the target is reported in
        `notices_not_applied` with reason `held-target` instead;
      • otherwise → "conflict", refused with the branch's own message and census label.
    Pure: the caller fires the refusal, so each census id stays in the one function that declares it."""
    if attested_complete and not noticed:
        return "attested-redaction"
    return "inconsistent" if noticed else "conflict"


def _chain_id(ep: Episode) -> tuple:
    """The `(edge_id, evidence_ref)` identity that groups one outcome chain."""
    return (ep.edge_id, ep.provenance.evidence_ref)


def _validate_incoming_chain(members: list, key, path) -> tuple:
    """specs/0009 §4c per-chain topology: a valid outcome chain is a single
    `1`-rooted, dense-`+1`, single-leaf path within one identity — no branch, no
    cycle, no gap. Refuse (never repair) anything else. Returns (root, leaf)."""
    with _SITE_IMPORT_CHAIN.consult():
        by_id = {m.id: m for m in members}
        roots = [m for m in members if m.supersedes_episode is None]
        if len(roots) != 1:
            raise _SITE_IMPORT_CHAIN.fire(ValueError(f"{path}: outcome chain {key} has {len(roots)} roots — "
                             f"import refuses rather than repairing (specs/0009 §4c/H5)"), "roots")
        root = roots[0]
        if (root.seq or 0) != 1:
            raise _SITE_IMPORT_CHAIN.fire(ValueError(f"{path}: outcome chain {key} root seq={root.seq!r} != 1 — "
                             f"imported history must inhabit the store's state space "
                             f"(specs/0009 §4c/H5)"), "root-seq")
        child_of: dict = {}
        for m in members:
            if m.supersedes_episode is None:
                continue
            pred = by_id.get(m.supersedes_episode)
            if pred is None:
                raise _SITE_IMPORT_CHAIN.fire(ValueError(f"{path}: outcome chain {key} link {m.id!r} supersedes "
                                 f"{m.supersedes_episode!r}, absent from this chain — "
                                 f"refuse (specs/0009 §4c/H5)"), "absent-predecessor")
            if (m.seq or 0) != (pred.seq or 0) + 1:
                raise _SITE_IMPORT_CHAIN.fire(ValueError(f"{path}: outcome chain {key} is not dense +1 at "
                                 f"{m.id!r} (seq {m.seq!r} on parent {pred.seq!r}) — "
                                 f"refuse (specs/0009 §4c/H5)"), "not-dense")
            if m.supersedes_episode in child_of:
                raise _SITE_IMPORT_CHAIN.fire(ValueError(f"{path}: outcome chain {key} branches at "
                                 f"{m.supersedes_episode!r} — refuse (specs/0009 §4c/H5)"), "branches")
            child_of[m.supersedes_episode] = m
        leaves = [m for m in members if m.id not in child_of]
        if len(leaves) != 1:
            raise _SITE_IMPORT_CHAIN.fire(ValueError(f"{path}: outcome chain {key} has {len(leaves)} leaves — "
                             f"refuse (specs/0009 §4c/H5)"), "leaves")
        leaf = leaves[0]
        seen: set = set()
        cur = leaf
        while cur is not None:
            if cur.id in seen:
                raise _SITE_IMPORT_CHAIN.fire(ValueError(f"{path}: outcome chain {key} has a cycle — refuse "
                                 f"(specs/0009 §4c/H5)"), "cycle")
            seen.add(cur.id)
            cur = by_id.get(cur.supersedes_episode) if cur.supersedes_episode else None
        if len(seen) != len(members) or (leaf.seq or 0) != len(members):
            raise _SITE_IMPORT_CHAIN.fire(ValueError(f"{path}: outcome chain {key} is disconnected or has a "
                             f"seq gap — refuse (specs/0009 §4c/H5)"), "disconnected")
        return root, leaf


def import_memory(store, path, *, user_id: Optional[str] = None,
                  restore: bool = False, relations=None) -> dict:
    """Load a Veracium export into `store`. Idempotent (an existing, record-equal
    record is skipped); `user_id` remaps every record into that user.

    specs/0005: the DEFAULT import caps every record's trust (the three levers,
    §4a) after validation and before every comparison gate; the returned dict
    gains ``capped`` — the number of parsed records the cap changed, counted
    pre-skip so it is a pure function of (file, flags) (P11). ``restore=True``
    skips the cap and nothing else (trust-field-faithful; the identity
    canonicalization below still applies) and is mutually exclusive with
    ``user_id``. ``restore`` must be a real bool — no truthiness (P13).

    specs/0009 §4c: the WHOLE file is parsed, cross-user remapped, legacy-converted
    (§4f-ii) and topology-validated BEFORE any persistent write, then committed as
    one atomic plan via `commit_outcome_import_plan` — so a valid chain A is never
    left persisted when a later chain B refuses, and the commit linearizes against
    concurrent `append_outcome_if_head` (no branch, no partial import). Returns counts.

    specs/0020 §4a-iii / 0021 §7b: absorption linkage is RECONSTRUCTED
    PRE-COMMIT from the file's own records (structured `absorbed_by_id`
    first; the decidable legacy note rule otherwise; missing/unresolvable/
    ambiguous/cyclic linkage raises `ImportLinkageError` before any write),
    and the reconstructed contribution rows ride the SAME atomic commit
    through the amended 0009 primitive. The returned dict gains
    ``contributions`` (rows written) and ``contributions_existing`` (rows
    skipped as plan-row-id-equal on an idempotent re-import)."""
    # specs/0005 §4a — the two argument gates, in order, BEFORE the file is
    # opened: the closed bool predicate (P13), then mutual exclusion (P5).
    with _SITE_IMPORT_RESTORE_NOT_BOOL.consult():   # the six other sites consult at their own first check (round 6, R6-2a)
        if type(restore) is not bool:
            raise _SITE_IMPORT_RESTORE_NOT_BOOL.fire(TypeError(
                f"restore must be a bool, got {type(restore).__name__!s} — no "
                f"truthiness coercion at a trust boundary (specs/0005 P13)"))
        _SITE_IMPORT_RESTORE_WITH_USER.consult()
        if restore and user_id is not None:
            raise _SITE_IMPORT_RESTORE_WITH_USER.fire(ValueError(
                "restore and user_id are mutually exclusive — a restore is this "
                "store's own history and never remaps (specs/0005 P5)"))
        path = Path(path)
        _raw = path.read_bytes()
        # specs/0044 §4l (T11a; research's Q1): the converting import's `inputs_digest` names the FILE's bytes as read
        inputs_digest = __import__("hashlib").sha256(_raw).hexdigest()
        lines = [ln for ln in (l.strip() for l in _raw.decode("utf-8").splitlines()) if ln]
        _SITE_IMPORT_FILE.consult()                 # one consult for the file's sequence of checks
        if not lines:
            raise _SITE_IMPORT_FILE.fire(ValueError(f"{path}: empty file"), "empty")
        header = json.loads(lines[0])
        if header.get("kind") != "veracium-export":
            raise _SITE_IMPORT_FILE.fire(ValueError(f"{path}: not a Veracium export (missing header)"), "not-an-export")
        src_version = header.get("version", 0)
        if src_version > FORMAT_VERSION:
            raise _SITE_IMPORT_FILE.fire(ValueError(f"{path}: export version {src_version} is newer "
                             f"than this Veracium understands ({FORMAT_VERSION})"), "newer-version")
        target_uid = user_id or header.get("user_id")

        # (1) parse every record
        edge_recs: list = []
        ep_recs: list = []
        notice_recs: list = []
        outcome_recs: list = []
        plan_recs: list = []
        act_raw: list = []
        for ln in lines[1:]:
            rec = json.loads(ln)
            marker = rec.pop("record", None)
            if marker is None and rec.get("kind") in ("edge", "episode"):
                marker = rec.pop("kind")   # format v1: the record marker was named "kind"
            if marker == "redaction":
                notice_recs.append(rec)    # specs/0041 §4g (format 13): a redaction NOTICE
                continue
            if marker == "arity_outcome":
                outcome_recs.append(rec)   # specs/0044 §4l (format 14): a migration outcome
                continue
            if marker == "arity_plan":
                plan_recs.append(rec)      # specs/0044 §4l (format 14): the exporting store's plan state
                continue
            if marker in _ACT_KEYS:
                act_raw.append((marker, rec))   # specs/0008 §6d / 0047 §4f (format 14, T11b): a confirmation or reply
                continue
            if marker not in ("edge", "episode"):
                raise _SITE_IMPORT_FILE.fire(ValueError(f"{path}: unknown record kind {marker!r}"), "unknown-kind")
            rec["user_id"] = target_uid
            (edge_recs if marker == "edge" else ep_recs).append(rec)
        # specs/0041 §4g: the notices — VALIDATED HERE, before any record is admitted, so an invalid notice
        # refuses the record-and-notice UNIT (the import is atomic: nothing is written); deduplicated by
        # SOURCE IDENTITY (origin, source user, source event ref) — the same notice twice is one notice, and
        # two notices under one identity with different bodies are a corrupted source, refused; the user
        # remap moves the notice's subject with the record's (the target id is never remapped).
        from .redaction import (MARKER_VERSION as _MARKER_VERSION, ORIGINATING_REASONS as _REASONS,
                                marker_fields as _marker_fields, attestation_paths as _attestation_paths)
        from .store.sqlite import SqliteStore as _S
        if notice_recs and src_version < _REDACTION_VERSION:
            # refuse-don't-drop, in the other direction: a notice in an envelope declaring a version below the
            # redaction era is a record kind the declared version cannot carry — never silently admitted
            raise _SITE_IMPORT_FILE.fire(ValueError(
                f"{path}: the file declares format {src_version} but carries redaction notices (format "
                f"{_REDACTION_VERSION}) — refused (specs/0041 §4g)"), "notice-below-era")
        # specs/0031 v23.1: the call-path era, refused WHOLE in a file that declares below it — before any record is
        # admitted, before the act lines are parsed (a planted `adapter_direct` confirmation in a 14 file refuses here,
        # naming the era, rather than as an unknown enum value)
        if src_version < _CALL_PATH_VERSION and (
                any(isinstance(r.get("provenance"), dict) and "call_path" in r["provenance"]
                    for r in edge_recs + ep_recs)
                or any(m == "confirmation" and r.get("call_path") in _AGENT_CALL_PATHS for m, r in act_raw)):
            raise _SITE_IMPORT_FILE.fire(ValueError(
                f"{path}: the file declares format {src_version} but carries an agent call path (format "
                f"{_CALL_PATH_VERSION}) — refused whole: a stripped call path would read as a host act "
                f"(specs/0031 v23.1)"), "call-path-below-era")
        # specs/0044 §4l (T11a): the arity era's records, validated whole here, before any record is admitted
        arity_outcomes, src_arity_state = _arity_records(path, outcome_recs, plan_recs, src_version)
        # specs/0008 §6e (T11b): the act lines, validated whole here, before any record is admitted
        acts = _act_records(path, act_raw, src_version)
        notices: dict = {}
        for n in notice_recs:
            need = ("origin", "source_user", "source_event_ref", "target_kind", "target_id", "fields", "marker_version", "reason")
            if any(k not in n for k in need):
                raise _SITE_IMPORT_FILE.fire(ValueError(
                    f"{path}: redaction notice is missing {[k for k in need if k not in n]} — the record-and-notice "
                    f"unit is refused, nothing imported (specs/0041 §4g)"), "invalid-notice")
            def _opt_int(v):
                return v is None or (isinstance(v, int) and not isinstance(v, bool) and v >= 0)
            if (n["target_kind"] not in ("edge", "episode") or not isinstance(n["target_id"], str) or not n["target_id"]
                    or not isinstance(n["fields"], list) or not all(isinstance(f, str) and f for f in n["fields"])
                    or not isinstance(n["marker_version"], int) or isinstance(n["marker_version"], bool)
                    or not 1 <= n["marker_version"] <= _MARKER_VERSION or n["reason"] not in _REASONS
                    or not all(isinstance(n[k], str) and n[k] for k in ("origin", "source_user", "source_event_ref"))
                    or not (n.get("recorded_at") is None or isinstance(n.get("recorded_at"), str))
                    or not _opt_int(n.get("store_version_before")) or not _opt_int(n.get("store_version_after"))):
                raise _SITE_IMPORT_FILE.fire(ValueError(
                    f"{path}: redaction notice for {n.get('target_kind')!r} {n.get('target_id')!r} is invalid — the "
                    f"record-and-notice unit is refused, nothing imported (specs/0041 §4g)"), "invalid-notice")
            # round 10 (R9-08): the field NAMES are carrier paths of the declared kind — the domain DERIVED from the
            # treatment tables — never free strings: prose, a wrong-kind path or a repeated path refuses the unit
            allowed = _attestation_paths(n["target_kind"])
            if len(set(n["fields"])) != len(n["fields"]) or not n["fields"] or not set(n["fields"]) <= allowed:
                raise _SITE_IMPORT_FILE.fire(ValueError(
                    f"{path}: redaction notice for {n['target_kind']!r} {n['target_id']!r} names fields outside the "
                    f"{n['target_kind']} carrier paths {sorted(set(n['fields']) - allowed) or '(empty or repeated)'} — "
                    f"the record-and-notice unit is refused, nothing imported (specs/0041 §4b, §4g)"), "invalid-notice")
            key = (n["origin"], n["source_user"], n["source_event_ref"])
            body = (n["target_kind"], n["target_id"], _S.notice_body(n))
            if key in notices:
                if notices[key]["_body"] != body:
                    raise _SITE_IMPORT_FILE.fire(ValueError(
                        f"{path}: two redaction notices share one source identity "
                        f"({n['origin']}, {n['source_user']}, {n['source_event_ref']}) with different bodies — a "
                        f"corrupted source, refused (specs/0041 §4g)"), "notice-integrity")
                continue
            notices[key] = {"origin": n["origin"], "source_user": n["source_user"],
                            "source_event_ref": n["source_event_ref"], "target_kind": n["target_kind"],
                            "target_id": n["target_id"], "fields": list(n["fields"]), "marker_version": n["marker_version"],
                            "reason": n["reason"], "recorded_at": n.get("recorded_at"),
                            "store_version_before": n.get("store_version_before"),
                            "store_version_after": n.get("store_version_after"), "_body": body}
        notice_list = [{k: v for k, v in n.items() if k != "_body"} for n in notices.values()]
        notice_targets = {(n["target_kind"], n["target_id"]) for n in notice_list}
        # §4g: a tombstone arriving with NO notice is ADMITTED as an UNATTESTED marker (§4b) — carrying, not
        # introducing — recorded as such and FLAGGED in the result
        unattested_markers = sorted(
            r.get("id") for kind, recs in (("edge", edge_recs), ("episode", ep_recs)) for r in recs
            if isinstance(r, dict) and _marker_fields({k: v for k, v in r.items() if k != "record"}) and (kind, r.get("id")) not in notice_targets)

        # (1a) specs/0037 §4e / §2c (round-3 F2, round-4 F1): THE PROCEDURAL
        # BOUNDARY, evaluated on the RAW record BEFORE any version normalization,
        # for every declared format version, PER RECORD (never per file — a
        # mixed file keeps its declarative records). DEFAULT path: a record is
        # refused as procedural when ANY of THREE independent signals fires —
        # (1) its stamp is "procedural", (2) its basis is present, (3) the
        # RECEIVING host's active registry declares its relation procedural —
        # naming the FIRST that fires in that order, and `raw: true` when the
        # envelope declared a version below the key (the presence is the
        # evidence). A basis in a foreign file is another host's declaration
        # (0005: an importing store's knowledge begins at ITS import). RESTORE
        # path: the operator asserts the file is this store's own history, which
        # is exactly the attestation basis requires — a CONSISTENT procedural
        # record (stamp AND basis in domain, or neither) restores VERBATIM;
        # either marker without the other, or an out-of-domain basis, is
        # MALFORMED and refused per record; the registry signal does NOT fire on
        # restore (the registry may have changed since). Only the records that
        # remain admissible are normalized, so the I10 strip has nothing
        # procedural to strip from them.
        reg = relations if relations is not None else DEFAULT_RELATIONS
        procedural_refusals: list = []
        admitted: list = []
        # specs/0037 v24.2 (round-6 finding 2): the inheritance lookup is built from the
        # RAW records BEFORE any refusal, so a predecessor refused as procedural on the
        # default path keeps constraining its successors — refusing a predecessor must
        # not erase its successors' requirements. Also the destination's existing
        # records, so the lookup is independent of file order and of what is already
        # stored. Procedural-ness is by LINEAGE: a record whose predecessor is
        # procedural by lineage is procedural whatever markers it carries (a chain
        # that drops the markers one hop later is the same laundering, one hop later).
        # specs/0037 v24.4 (round-8 finding 1): CONFLICTING IDS ARE RESOLVED BEFORE
        # LINEAGE IS DERIVED. `raw_by_id` kept the LAST incoming record per id and
        # the lineage helper preferred it over the destination's stored record, so
        # (a) a REFUSED incomplete copy of a stored procedural predecessor hid the
        # stored producer and a successor with another producer restored, and (b)
        # a file naming one id twice gave a file-order-dependent disposition. Now:
        # every incoming copy of an id the file names more than once is refused
        # (`duplicate_id` — a file cannot say two things about one record, and
        # both orders refuse the same copies); the lineage helper reads EVERY copy
        # of an id together with the destination's stored record, the stored
        # record's constraints taking precedence (a persisted stamp or producer is
        # never erased by an incoming copy, admitted or refused), and copies that
        # disagree about a constraint leave it UNRESOLVED, which fails every
        # successor's check (fail closed, order-independent by construction —
        # sets, never "the last one seen").
        raw_copies: dict = {}
        for rec in edge_recs:
            raw_copies.setdefault(rec.get("id"), []).append(rec)
        duplicate_ids = {rid for rid, copies in raw_copies.items() if len(copies) > 1}
        existing_by_id = {e.id: e for e in store.edges(target_uid, active_only=False,
                                                        include_quarantined=True)}
        _lineage: dict = {}
        # a constraint the file's copies disagree about: a UNIQUE object, never a
        # value a record could carry (research's pre-seal red team, 2026-09-14: a
        # string sentinel shared the producer's value space and was held out of
        # the check only by the closed producer lexicon — an accident, not a rule)
        _UNRESOLVED = object()

        def _signals(stamp, basis, producer, relation):
            """v24.3 (round-7 finding 2) / v24.4 (research's pre-seal red team,
            finding A): ONE reading of procedural-ness for BOTH custody states —
            the SAME four signals the filter above reads: stamp, basis, producer,
            and on the default path the receiving registry's kind for the
            relation. The stored record's `Provenance.procedural` is stamp-or-basis
            only; reading it for the destination's record gave a registry-only
            predecessor opposite dispositions depending on whether it was stored
            or incoming. A shared helper is what stops the two sides disagreeing a
            third time."""
            own = (stamp == "procedural" or basis is not None or producer is not None
                   or (not restore and is_procedural_relation(reg, relation)))
            return own, producer

        def _raw_markers(rec):
            prov = rec.get("provenance") if isinstance(rec.get("provenance"), dict) else {}
            return _signals(prov.get("record_kind"), prov.get("basis"), prov.get("producer"),
                            rec.get("relation"))

        def _stored_markers(e):
            return _signals(e.provenance.record_kind, e.provenance.basis, e.provenance.producer,
                            e.relation)

        def _one_or_unresolved(values):
            """The single agreed value of a constraint over a set of readings, None
            when no reading names one, `_UNRESOLVED` when readings disagree (or any
            reading is itself unresolved)."""
            named = [v for v in values if v is not None]
            if not named:
                return None
            if any(v is _UNRESOLVED for v in named) or len(set(named)) > 1:
                return _UNRESOLVED
            return named[0]

        def lineage(rid, _seen=()):
            """(procedural_by_lineage, validated_producer) for record `rid`, read
            from the RESOLVED description of the id: the destination's stored
            record when there is one (its stamp and producer take precedence —
            v24.4), together with EVERY incoming copy (a copy's markers can only
            add procedural-ness; a copy's producer counts only where nothing is
            stored). The validated producer is INHERITED down the chain: a record
            whose own producer disagrees with its predecessor's validated producer
            is a rejected intermediate, and the constraint it violated carries on
            to its successors unchanged (round-7 finding 2: the raw field of a
            rejected intermediate must never substitute for validated
            inheritance). A constraint the copies disagree about, or a cycle, is
            `_UNRESOLVED`, which no successor can satisfy."""
            if rid in _lineage:
                return _lineage[rid]
            if rid in _seen:                                   # a cycle: fail closed
                return True, _UNRESOLVED
            e = existing_by_id.get(rid)
            copies = raw_copies.get(rid, [])
            if e is None and not copies:
                _lineage[rid] = (False, None)
                return _lineage[rid]
            marks = [_raw_markers(c) for c in copies]
            stored_own, stored_producer = _stored_markers(e) if e is not None else (False, None)
            own = stored_own or any(m[0] for m in marks)
            if stored_producer is not None:
                own_producer = stored_producer
            else:
                own_producer = _one_or_unresolved(m[1] for m in marks)
            # ADDS, NEVER REMOVES, for the predecessor set too (research's pre-seal
            # red team, finding C): a stored declarative X must not shadow an
            # incoming X's claim to a procedural predecessor — X's own successor
            # would inherit from the shadow instead of the chain.
            preds = ({e.supersedes} if e is not None and e.supersedes is not None else set()) | {
                c.get("supersedes") for c in copies if c.get("supersedes") is not None}
            if not preds:
                result = (own, own_producer)
            else:
                chain = [lineage(pr, _seen + (rid,)) for pr in sorted(preds)]
                pred_proc = any(pp for pp, _ in chain)
                pred_producer = _one_or_unresolved(pv for _, pv in chain)
                if stored_producer is not None:
                    # v24.5 (round-9 F1): a PERSISTED producer is the constraint.
                    # The store enforced inheritance when the row was written, so
                    # the stored record is never a "rejected intermediate" — a
                    # claimed ancestry, from an admitted or a refused copy, can add
                    # procedural-ness and never replace the persisted producer
                    # (round 9: a refused copy of stored P claiming Q as its
                    # predecessor had let an `extractor` successor of a `host` P
                    # restore, because the chain's producer overrode the stored one).
                    validated = stored_producer
                else:
                    validated = pred_producer if pred_producer is not None else own_producer
                result = (own or pred_proc, validated)
            _lineage[rid] = result
            return result

        for rec in edge_recs:
            prov = rec.get("provenance")
            prov = prov if isinstance(prov, dict) else {}
            stamp = prov.get("record_kind")
            basis = prov.get("basis")
            producer = prov.get("producer")
            raw = src_version < _PROCEDURAL_VERSION
            if rec.get("id") in duplicate_ids:                 # v24.4: resolved before anything else
                procedural_refusals.append(
                    {"id": rec.get("id"), "refusal": "duplicate_id", "signal": "id", "raw": raw})
                continue
            if not restore:
                # specs/0037 v23: the producer stamp is a FOURTH independent
                # signal — a record carrying one is procedural by its own word
                signal = ("stamp" if stamp == "procedural"
                          else "basis" if basis is not None
                          else "producer" if producer is not None
                          else "registry" if is_procedural_relation(reg, rec.get("relation"))
                          else None)
                if signal is not None:
                    procedural_refusals.append(
                        {"id": rec.get("id"), "refusal": "procedural_import_refused",
                         "signal": signal, "raw": raw})
                    continue
            else:
                consistent = ((stamp is None and basis is None and producer is None)
                              or (stamp == "procedural" and basis in ("stated", "observed")
                                  and producer in (None, "host", "extractor")))
                if not consistent:
                    # the signal names the marker that is out of place: a producer
                    # outside its domain or without the kind stamp; otherwise the
                    # present half of a stamp/basis pair (or the invalid one)
                    producer_bad = producer is not None and (
                        producer not in ("host", "extractor") or stamp != "procedural")
                    procedural_refusals.append(
                        {"id": rec.get("id"), "refusal": "malformed_procedural_marker",
                         "signal": ("producer" if producer_bad
                                    else "stamp" if stamp is not None else "basis"), "raw": raw})
                    continue
            admitted.append(rec)
        edge_recs = admitted
        if src_version < _PROCEDURAL_VERSION:
            for rec in edge_recs:             # I10: nothing procedural left, by construction
                prov = rec.get("provenance")
                if isinstance(prov, dict):
                    prov.pop("record_kind", None)
                    prov.pop("basis", None)
        if src_version < _PRODUCER_VERSION:   # keyed on the producer's OWN era, not the reader's head (0041 4b moved the head)
            for rec in edge_recs:             # I10: a producer in a pre-12 envelope is never trusted
                prov = rec.get("provenance")  # (the record imports as pre-stamp: `procedural_unstamped`)
                if isinstance(prov, dict):
                    prov.pop("producer", None)

        # specs/0037 v24.1 (round-5 finding 3): the INHERITANCE rules the store's
        # choke point applies to an ordinary write — a successor of a procedural
        # predecessor is procedural (V-STAMP-INHERITED) and carries the SAME
        # producer (V-PRODUCER-INHERITED) — are applied here, at the boundary and
        # before anything commits, because the import commit writes rows directly.
        # The predecessor is looked up by id among the incoming records OR the
        # destination's existing records, so the check is independent of file
        # order; a violating successor is refused PER RECORD and counted.
        kept: list = []
        for rec in edge_recs:
            sid = rec.get("supersedes")
            if sid is None:
                kept.append(rec)
                continue
            if sid in raw_copies or sid in existing_by_id:         # RAW copies, refused or not, AND the stored record
                pred_proc, pred_producer = lineage(sid)              # …and the VALIDATED inherited producer
            else:
                kept.append(rec)                                     # no predecessor to inherit from
                continue
            prov = rec.get("provenance") or {}
            succ_proc = prov.get("record_kind") == "procedural" or prov.get("basis") is not None
            # an UNRESOLVED inherited producer is one no successor can match (v24.4)
            signal = ("stamp" if pred_proc and not succ_proc
                      else "producer" if pred_producer is not None and prov.get("producer") != pred_producer
                      else None)
            if signal is not None:
                procedural_refusals.append(
                    {"id": rec.get("id"), "refusal": "inheritance_violation", "signal": signal,
                     "predecessor": sid, "raw": src_version < _PROCEDURAL_VERSION})
                continue
            kept.append(rec)
        edge_recs = kept
        # specs/0037 §4e with 0047 §4f (T11b): an act whose record the file carries but this import REFUSED PER RECORD
        # (procedural, a duplicate id, an inheritance violation) goes with its record — refused with it and counted,
        # never an orphan that would refuse the whole file (the record's own refusal is already reported)
        _admitted_ids = {r.get("id") for r in edge_recs}
        acts_refused_with_edge = sum(1 for a in acts if a["edge_id"] in raw_copies and a["edge_id"] not in _admitted_ids)
        acts = [a for a in acts if not (a["edge_id"] in raw_copies and a["edge_id"] not in _admitted_ids)]

        # (1b) specs/0020 §4a-iii — the LINKAGE SNAPSHOT, taken over the file's
        # OWN id universe BEFORE the cross-user remap mutates ids (winner
        # resolution is defined in the file's universe; `id_remap` translates
        # only the OUTPUT keys/refs). The FORMAT-7 rider field is DETACHED from
        # the record here — it is a linkage carrier consumed by reconstruction,
        # never persisted state — and per 0006 I10 a pre-v7 envelope's
        # `absorbed_by_id` is STRIPPED, never trusted (the file takes the legacy
        # note rule); identity fields follow the same I10 rule as gate (2b).
        linkage_recs: list = []
        for rec in edge_recs:
            prov = rec.get("provenance")
            prov = prov if isinstance(prov, dict) else {}
            ab = rec.pop("absorbed_by_id", None)
            linkage_recs.append({
                "id": rec.get("id"),
                "invalidation_reason": rec.get("invalidation_reason"),
                "note": rec.get("note"),
                "absorbed_by_id": (ab if src_version >= 7 else None),
                "origin": (prov.get("origin") if src_version >= 4 else None),
                "source_id": (prov.get("source_id") if src_version >= 4 else None),
                "evidence_ref": prov.get("evidence_ref"),
            })

        # (2) cross-user remap — a COPY, not a move: edge ids are global primary keys, so
        # importing another user's ids would collide/overwrite (and add_edge refuses a
        # user_id change, specs/0008 §6d). Mint fresh ids and remap EVERY reference:
        # edge.supersedes, episode.edge_id, AND episode.supersedes_episode (§4c Corr. B —
        # the new episode→episode ref the v2 importer never remapped).
        remapping = user_id is not None and user_id != header.get("user_id")
        id_map: dict = {}
        if remapping:
            for rec in edge_recs:
                if rec.get("id") is not None:
                    id_map[rec["id"]] = f"imp-e-{uuid4().hex[:12]}"
            for rec in ep_recs:
                if rec.get("id") is not None:
                    id_map[rec["id"]] = f"imp-ep-{uuid4().hex[:12]}"

        def _remap(v):
            return id_map.get(v, v) if remapping else v

        for rec in edge_recs:
            if rec.get("id") is not None:
                rec["id"] = _remap(rec["id"])
            if rec.get("supersedes") is not None:
                rec["supersedes"] = _remap(rec["supersedes"])
        for rec in ep_recs:
            if rec.get("id") is not None:
                rec["id"] = _remap(rec["id"])
            if rec.get("edge_id") is not None:
                rec["edge_id"] = _remap(rec["edge_id"])
            if rec.get("supersedes_episode") is not None:
                rec["supersedes_episode"] = _remap(rec["supersedes_episode"])
        # specs/0041 §4g: the notice's SUBJECT moves with the record's — its target follows the same map (a
        # notice whose record is not in this file keeps the source's id: under a remap no record can arrive
        # under it, so it stands as the witness that the source redacted that id)
        for n in notice_list:
            n["target_id"] = _remap(n["target_id"])
        notice_targets = {(n["target_kind"], n["target_id"]) for n in notice_list}
        # specs/0044 §4l: the outcomes' edge and successor references follow the same map; the unit is validated whole
        arity_outcomes = _validate_outcome_unit(
            path, _remap_outcomes(arity_outcomes, _remap, remapping, target_uid), edge_recs)
        # the 2026-10-13 notice-binding hotfix (the owner's ruling, BOTH modes): the file must SHOW the redaction it
        # claims — a notice may apply only to a record this file carries, already in the notice's treated shape. Flagged
        # here, against the file's own copy, before the 0014 rider rebinds a notice to a held output; the commit applies
        # no notice that is not flagged shown.
        _file_recs = {("edge", r.get("id")): r for r in edge_recs}
        _file_recs.update({("episode", r.get("id")): r for r in ep_recs})
        for n in notice_list:
            rec = _file_recs.get((n["target_kind"], n["target_id"]))
            n["_shown"] = rec is not None and _redaction.shows_redaction(n["target_kind"], rec, n["fields"])
            n["_unshown"] = None if n["_shown"] else ("record-not-in-file" if rec is None else "record-untreated")

        # (2a) specs/0020 §4a-iii — PRE-COMMIT absorption reconstruction over the
        # linkage snapshot: structured `absorbed_by_id` first (the FORMAT-7 rider
        # carrier); the decidable LAST-tag note rule for legacy records; digests
        # propagate transitively to every absorber (born-closed row sets); a
        # missing, unresolvable, ambiguous, contradictory, or cyclic linkage
        # raises `ImportLinkageError` HERE — before any destination write, so a
        # refused import leaves the destination byte-identical (R7-2). The ONE
        # `op-<12hex>` import operation id is minted here; the reconstructed rows
        # ride the SAME atomic commit as the records (the amended 0009 §4c
        # primitive), keyed by the importer's own old→new table under a remap.
        import_op = f"op-{uuid4().hex[:12]}"
        # specs/0008 §6e (T11b; the owner's R-D6): the acts' edge references follow the map, and under a cross-user remap
        # each act moves into this import's remap namespace
        acts = _remap_acts(acts, _remap, remapping, target_uid, import_op)
        reconstructed = reconstruct_absorption_rows(
            linkage_recs, store.local_origin(),
            id_remap=(id_map if remapping else None), import_op=import_op)
        contrib_rows: list = []
        for surv in sorted(reconstructed):
            for row in reconstructed[surv]:
                contrib_rows.append({
                    "id": plan_row_id(target_uid, "edge", surv, row, "import",
                                      op=import_op),
                    "user_id": target_uid, "survivor_type": "edge",
                    "survivor_id": surv, **row})

        # (2c) specs/0005 §4a/§4c — THE IMPORT TRUST CAP, the boundary this spec
        # exists for. Sequence per §4c-ii: each record's provenance is VALIDATED
        # first (a malformed or null trust value raises here per the shipped
        # 9-cell matrix — never silently normalized into a valid capped value,
        # R1-4/P14), then the three levers are applied to the validated model:
        # author_of_evidence := THIRD_PARTY (the claim made true relative to the
        # target owner, R1-1), derived_from := THIRD_PARTY (min, never raised),
        # disclosure floored to USE_ONLY (QUARANTINED never weakened). The cap
        # runs BEFORE every comparison gate below — the 0006 origin gates, the
        # 0014 identity projection (which per its 0005 rider receives the
        # path-transformed incoming form), and the 0009 record-equality
        # preflight — so no gate ever sees an uncapped record. `capped` counts
        # the records the cap CHANGED, over the parsed file, pre-skip: a pure
        # function of (file, flags), never of destination state (N1/P11).
        # restore=True skips exactly this block (trust-field-faithful, R1-3).
        # specs/0026 §3d — THE AGREEMENT MODE-SPLIT, per the accepted ONE
        # decision table (import_matrix.MATRIX, V6a). I10 first: a field
        # newer than the declared format is STRIPPED, never trusted. Then:
        # restore=True validates every present record against the CLOSED
        # SHAPE and RAISES on malformed BEFORE any destination write
        # (grammar membership is VERSION-SCOPED — a well-typed record under
        # a FOREIGN lexicon version restores verbatim, its markers opaque;
        # the R1-4 ruling: garbage declares something untrue). Default mode
        # never consumes the incoming value at all: it is compared for the
        # diagnostic counter, then discarded for the recomputation (below,
        # after the cap fixes final disclosure).
        from .schema import AgreementRecord as _AgreementRecord
        agreement_mismatches = 0
        for rec in edge_recs:
            if src_version < _PRE_PROCEDURAL_VERSION:   # I10: `agreement` is the format-10 key
                rec.pop("agreement", None)
        if restore:
            for rec in edge_recs:
                agr = rec.get("agreement")
                if agr is None:
                    continue
                _SITE_IMPORT_AGREEMENT_INVALID.consult()
                try:
                    _AgreementRecord.model_validate(agr)
                except Exception as exc:
                    raise _SITE_IMPORT_AGREEMENT_INVALID.fire(ValueError(
                        f"{path}: malformed AgreementRecord on edge "
                        f"{rec.get('id')!r} — verbatim restore into a typed "
                        f"carrier is impossible for garbage; RAISES, nothing "
                        f"written (specs/0026 §3d V6a): {exc}")) from exc
        capped_count = 0
        if not restore:
            for rec in edge_recs + ep_recs:
                prov = rec.get("provenance")
                if not isinstance(prov, dict):
                    continue   # absent/non-dict provenance: judged by full model validation below
                model = Provenance.model_validate(prov)   # malformed/null -> raises, whole-import
                capped = model.model_copy(update={
                    "author_of_evidence": EvidenceAuthor.THIRD_PARTY,
                    "derived_from": EvidenceAuthor.THIRD_PARTY,
                    "disclosure": (Disclosure.QUARANTINED
                                   if model.disclosure == Disclosure.QUARANTINED
                                   else Disclosure.USE_ONLY),
                })
                if capped != model:
                    capped_count += 1
                rec["provenance"] = json.loads(capped.model_dump_json())
            # specs/0026 §3d — the default-mode RECOMPUTATION half: the
            # incoming agreement value (any state — absent, present, forged,
            # malformed, foreign-version) is compared for the diagnostic
            # counter and DISCARDED; the ONE derivation site recomputes
            # under the CURRENT lexicon from the record's own note/object
            # and its post-cap disclosure, so a forged record cannot enter
            # Q5's corpus and a stripped one cannot launder a relay past
            # the floor (the cap above already holds disclosure at
            # USE_ONLY/QUARANTINED, so the MENTIONABLE->USE_ONLY floor has
            # nothing left to lower here).
            from . import agreement as _agreement
            for rec in edge_recs:
                incoming = rec.pop("agreement", None)
                derived = _agreement.derive_record(
                    str(rec.get("note", "") or ""),
                    str(rec.get("object", "") or ""),
                    Disclosure(rec.get("provenance", {}).get(
                        "disclosure", "use_only")),
                    relation=rec.get("relation"))
                derived_dict = (json.loads(derived.model_dump_json())
                                if derived is not None else None)
                if derived_dict is not None:
                    rec["agreement"] = derived_dict
                if incoming != derived_dict:
                    agreement_mismatches += 1

        # (2b) specs/0006 — source-identity ingress gates, BEFORE any record enters the store.
        #  - I10: a field NEWER than the declared FORMAT_VERSION is STRIPPED, never trusted — a
        #    pre-v4 file that hand-adds source_id/origin has an UNKNOWN identity, so drop both.
        #  - I14: a current-format (v4+) record MUST carry a non-null origin. An absent origin is
        #    MALFORMED and REJECTED — it is NEVER resolved to this store's singleton (that
        #    resolution is for LOCAL stored rows only, §4 rule 6). A PRESENT foreign origin is
        #    preserved as-is (I2b), never localised; trust of it is 0005's boundary, applied first.
        # specs/0019 §2c: a pre-v6 envelope carrying `ungrounded` is STRIPPED,
        # never trusted (the 0006 I10 rule — a field newer than the declared
        # FORMAT_VERSION has unknown provenance); post-v6 absent → StrictBool
        # default False at model validation. Non-bool values REFUSE there (F7).
        if src_version < 6:
            for rec in edge_recs:
                rec.pop("ungrounded", None)

        # specs/0045 §2c/§4e/§4f (T11b): the grounding axis — stripped below era 14 (0006 I10), checked from it in BOTH
        # modes, then the default import's write rule (`not_attested`, NULL, `default-import`, whatever the file says)
        # or the trusted restore's (as recorded)
        edge_recs = _axis_records(path, edge_recs, src_version, restore)

        # specs/0016 D2 (FORMAT 7): `Provenance.source_type` is DELETED. A ≤6
        # file legitimately carries the historical key — it is DROPPED on import
        # with the rest of the record intact (§2c row 1); ANY carried value
        # (including a crafted one) is never read (§2c row 5). Explicit here so
        # the drop is a stated boundary rule, not an accident of extra=ignore.
        if src_version < 7:
            for rec in edge_recs + ep_recs:
                prov = rec.get("provenance")
                if isinstance(prov, dict):
                    prov.pop("source_type", None)

        dest_origin = store.local_origin() if src_version >= 4 else None
        for rec in edge_recs + ep_recs:
            prov = rec.get("provenance")
            if not isinstance(prov, dict):
                continue
            if src_version < 4:
                prov.pop("source_id", None)          # I10 — newer field in an older envelope
                prov.pop("origin", None)
            else:
                _SITE_IMPORT_ORIGIN_MISSING.consult()
                if prov.get("origin") is None:
                    raise _SITE_IMPORT_ORIGIN_MISSING.fire(ValueError(
                        f"{path}: v{src_version} record {rec.get('id')!r} carries provenance with "
                        f"no origin — a current-format import MUST carry origin; a missing one is "
                        f"malformed and is NEVER resolved to this store (specs/0006 I14)"))
                elif prov["origin"] == dest_origin:
                    # A LOCAL record coming home (its materialised origin IS this store's singleton):
                    # canonicalise back to absent so it resolves to us and stores byte-identically to
                    # the original local row — that is what makes an export→re-import idempotent and
                    # groups the two as ONE source (I9). A genuinely FOREIGN origin is left untouched
                    # (I2b) — trust of it is 0005's import boundary, applied first (I7).
                    prov["origin"] = None

        # (2d) specs/0023 N8 — THE DESTINATION-STANDING CAP, after identity has
        # SETTLED (the strip/materialise/canonicalise rules above decide what each
        # record's resolved identity IS; capping earlier would quarantine on an
        # identity the gates were about to change). A record whose resolved
        # identity stands revoked IN THE DESTINATION arrives QUARANTINED — in
        # BOTH modes, restore included: the 0005 cap is about the FILE's trust and
        # restore rightly skips it, but this cap is about THIS STORE's standing
        # state, which no flag on an import file may override (§3b). Covers the
        # export→revoke→reimport sequence into the same store: the come-home
        # canonicalisation above maps the record back to the local identity the
        # revocation named. QUARANTINED is a floor — never weakened, never
        # widened; Q2: a later lift does not revisit it.
        from .scope_linkage import identity_digest_of as _idg
        _standing_cache: dict = {}
        for rec in edge_recs + ep_recs:
            prov = rec.get("provenance")
            if not isinstance(prov, dict) or prov.get("source_id") is None:
                continue                      # N11: no source_id, no digest, unreachable
            uid = rec.get("user_id")
            if uid not in _standing_cache:
                _standing_cache[uid] = store.standing_revocations(uid)
            if not _standing_cache[uid]:
                continue
            d = _idg(prov.get("origin"), prov["source_id"], store.local_origin())
            if d is not None and d in _standing_cache[uid]:
                prov["disclosure"] = Disclosure.QUARANTINED.value

        # (3) legacy-format outcome conversion (§4f-ii) OR v3 explicit-field check (H13).
        # Pinned to the OUTCOME-field format version (3, specs/0009), NOT FORMAT_VERSION: the
        # 0006 v3→v4 bump introduced source-identity fields, not outcome fields, so v3 AND v4
        # both carry explicit outcome fields and must take the H13 branch. Keying this on
        # FORMAT_VERSION would wrongly legacy-convert a v3 export after the bump.
        _SITE_IMPORT_RECORD.consult()                   # ONE consult for the record checks below — every path through this section reaches them (R6-2a)
        outcome_recs = [r for r in ep_recs if r.get("kind") == "outcome"]
        if src_version < 3:
            # group by identity first: a pre-v3 export can hold two outcome records for
            # one (edge_id, evidence_ref); rooting each would branch — REFUSE instead.
            groups: dict = {}
            for r in outcome_recs:
                groups.setdefault(
                    (r.get("edge_id"), (r.get("provenance") or {}).get("evidence_ref")),
                    []).append(r)
            for gk, members in groups.items():
                if len(members) > 1:
                    raise _SITE_IMPORT_RECORD.fire(ValueError(
                        f"{path}: legacy import holds {len(members)} outcome records for "
                        f"chain {gk} — refuse rather than branch (specs/0009 §4f-ii)"), "legacy-outcome-multiplicity")
            for r in outcome_recs:   # the same honest conversion as the on-disk migration
                r["seq"] = 1
                r["supersedes_episode"] = None
                r["judgment_time_known"] = False
        else:
            for r in outcome_recs:   # a v3 outcome record MUST be explicit (H13)
                jtk = r.get("judgment_time_known")
                if jtk is None:
                    raise _SITE_IMPORT_RECORD.fire(ValueError(
                        f"{path}: v3 outcome record {r.get('id')!r} omits "
                        f"judgment_time_known — refuse (specs/0009 H13)"), "v3-outcome-key")
                # state-space rule (§ Episode fields, round-5 Correction B): a
                # False label is a LEGACY-ROOT-ONLY state — never a non-root.
                if jtk is False and (r.get("seq") != 1
                                     or r.get("supersedes_episode") is not None):
                    raise _SITE_IMPORT_RECORD.fire(ValueError(
                        f"{path}: v3 outcome record {r.get('id')!r} has "
                        f"judgment_time_known=False but is not a root (seq="
                        f"{r.get('seq')!r}, supersedes_episode="
                        f"{r.get('supersedes_episode')!r}) — refuse (specs/0009)"), "v3-outcome-chain-fields")

        # (3b) specs/0010 X18/X19: consolidation shapes cross the boundary honestly.
        for r in ep_recs:
            if r.get("claimed_by") is not None:
                raise _SITE_IMPORT_RECORD.fire(ValueError(
                    f"{path}: episode {r.get('id')!r} is a CLAIMED input whose "
                    f"consolidation op is non-portable — refuse rather than orphan it "
                    f"(specs/0010 X18)"), "claimed-input")
            # specs/0014 §4c/§2c — the store-assigned output index at the import
            # boundary. 0006 I10 first: a field NEWER than the declared
            # FORMAT_VERSION is STRIPPED, never trusted — a pre-v5 envelope cannot
            # legitimately carry the index, so it is dropped (matching the
            # source_id/origin treatment above), and the v5 gates below never see
            # it. For v5+ files: explicit null is MALFORMED (the export path omits
            # None — R7-3); type gates mirror the generic path; a NON-output
            # carrying an index is fabricated store identity and is refused.
            if src_version < 5:
                r.pop("consolidation_output_index", None)     # I10 — newer field
            idx_present = "consolidation_output_index" in r
            idx = r.get("consolidation_output_index")
            if idx_present and idx is None:
                raise _SITE_IMPORT_RECORD.fire(ValueError(
                    f"{path}: episode {r.get('id')!r} carries an explicit null "
                    f"consolidation_output_index — the exporter omits None, so an "
                    f"explicit null is malformed (specs/0014 §4c R7-3)"), "null-output-index")
            if idx is not None and (isinstance(idx, bool)
                                    or not isinstance(idx, int) or idx < 0):
                raise _SITE_IMPORT_RECORD.fire(ValueError(
                    f"{path}: episode {r.get('id')!r} consolidation_output_index "
                    f"{idx!r} is not a non-negative integer (specs/0014 §2c)"), "output-index-shape")
            if idx is not None and not r.get("lineage"):
                raise _SITE_IMPORT_RECORD.fire(ValueError(
                    f"{path}: episode {r.get('id')!r} carries a consolidation_output_"
                    f"index but no lineage — store-assigned identity cannot be "
                    f"fabricated on a plain episode (specs/0014 §4c)"), "index-without-lineage")
            if r.get("lineage"):                      # a consolidation OUTPUT
                lin = r["lineage"]
                if not (isinstance(lin, list)
                        and all(isinstance(x, str) and is_historical_id(x) for x in lin)):
                    raise _SITE_IMPORT_RECORD.fire(ValueError(
                        f"{path}: episode {r.get('id')!r} has a malformed lineage shape — "
                        f"every lineage id must be historical (specs/0010 X18)"), "lineage-shape")
                # X19: a finalized output's operation_id becomes a destination-local
                # HISTORICAL reference (deterministic, retry-stable — no persisted map) that
                # no LIVE local op id can inhabit, so it can never collide on import or after
                # a later local finalization. lineage ids are already historical.
                if r.get("operation_id") is not None:
                    r["operation_id"] = to_historical_id(r["operation_id"])

        # specs/0014 §2c (R8-3/R9-5/R10-5/R11-2/R11-3/R12-2/R13-2): indexed-output
        # identity at the import boundary. The uniqueness domain is incoming ∪
        # EXISTING DESTINATION STATE over the tenant-scoped origin-namespaced key
        # (destination user, resolved origin, operation_id, index) — partial history
        # explains GAPS, never DUPLICATES. A colliding incoming output is accepted
        # IFF SOURCE-IDENTICAL under the two-set projection (a true re-import
        # resolves idempotently — the record is SKIPPED, ordinary records keep the
        # shipped remap-copy semantics); ANY projected difference REJECTS.
        def _out_key(rec):
            origin = (rec.get("provenance") or {}).get("origin")   # post-canonical
            return (origin, rec.get("operation_id"), rec["consolidation_output_index"])

        incoming_indexed = [r for r in ep_recs
                            if r.get("lineage")
                            and r.get("consolidation_output_index") is not None]
        seen_keys = {}
        for r in incoming_indexed:
            k = _out_key(r)
            if k in seen_keys:
                raise _SITE_IMPORT_RECORD.fire(ValueError(
                    f"{path}: two lineage-bearing outputs claim the same "
                    f"(origin, operation_id, index) {k!r} within one import — "
                    f"partial history explains gaps, never duplicates "
                    f"(specs/0014 §2c R8-3)"), "duplicate-lineage-key")
            seen_keys[k] = r
        skip_ids = set()
        rebind: dict = {}                  # round 13 (R12-01, N12-01): an arriving output's id -> the HELD output's id
        redaction_arrivals: list = []      # the arrivals resolved by the 0014 §2c rider's one class (flagged, §4g)
        if incoming_indexed:
            dest_uid = user_id if user_id is not None else header.get("user_id")
            dest_by_key = {}
            for dep in store.episodes(dest_uid):
                if dep.lineage and dep.consolidation_output_index is not None:
                    drec = json.loads(dep.model_dump_json())
                    dest_by_key[_out_key(drec)] = drec
            # round 14 (R13-01): RESOLVE every arriving output to the held output it collides with BEFORE any notice is
            # read for a collision. Round 13 matched a notice's RAW target against "the arriving id OR the held id",
            # so with two outputs' ids permuted, B's notice (naming arriving `a`) read as A's (held `a`) and admitted A's
            # unexcused difference. A raw id now names ONE subject: an ARRIVING episode's id names that arrival (an
            # indexed one resolved to its held output, an ordinary one to its own id); any other id names a held or
            # standing record directly. A notice counts for a collision only through THAT collision's own arrival, or
            # directly — never through a DIFFERENT arrival that happens to resolve to the same destination record.
            hits = {r["id"]: dest_by_key.get(_out_key(r)) for r in incoming_indexed}
            arriving_eps = {r["id"] for r in ep_recs}

            def _notice_counts_for(n, r, h):
                if n["target_kind"] != "episode":
                    return False
                t = n["target_id"]
                if t in arriving_eps:
                    return t == r["id"]                # through THIS arrival only
                return t == h["id"]                    # no arrival under that id: the held output named directly

            for r in incoming_indexed:
                hit = hits[r["id"]]
                if hit is None:
                    continue
                if (source_identity_projection(r)
                        == source_identity_projection(hit)):
                    skip_ids.add(r["id"])              # idempotent re-import: no-op
                    rebind[r["id"]] = hit["id"]        # ... and a notice for the arrival names the held output (N12-01)
                    continue
                # the rider's ONE admitted class — a redaction of THIS held output, by a notice for it: in the unit,
                # resolved to it through this arrival or naming it directly, or already held for the held output
                in_unit = [set(n["fields"]) for n in notice_list if _notice_counts_for(n, r, hit)]
                held_fields = store._attested_fields(dest_uid, "episode", hit["id"], coverage=False)   # APPLIED: R10-02
                if any(held_output_redaction(hit, r, f) for f in in_unit + ([held_fields] if held_fields else [])):
                    skip_ids.add(r["id"])
                    rebind[r["id"]] = hit["id"]
                    redaction_arrivals.append(hit["id"])
                else:
                    raise _SITE_IMPORT_RECORD.fire(ValueError(
                        f"{path}: incoming output {r.get('id')!r} claims the "
                        f"existing identity {_out_key(r)!r} with a DIFFERENT "
                        f"source-identity projection — rejected "
                        f"(specs/0014 §2c R9-5/R11-3)"), "lineage-claims-foreign")
        if skip_ids:
            ep_recs = [r for r in ep_recs if r["id"] not in skip_ids]
        # the notice binds to the HELD output's id, never to an id minted for a discarded arrival (0041 R12-01 N12-01):
        # rebound HERE, before the commit, so the notice loop — R11-03's body comparison included — sees the held id
        for n in notice_list:
            if n["target_kind"] == "episode" and n["target_id"] in rebind:
                n["target_id"] = rebind[n["target_id"]]
        notice_targets = {(n["target_kind"], n["target_id"]) for n in notice_list}

        edges = [Edge.model_validate(r) for r in edge_recs]
        eps = [Episode.model_validate(r) for r in ep_recs]

        # (4) per-chain incoming topology (static — independent of the live destination)
        incoming_chains: dict = {}
        for ep in eps:
            if ep.kind == "outcome":
                incoming_chains.setdefault(_chain_id(ep), []).append(ep)
        for key, members in incoming_chains.items():
            _validate_incoming_chain(members, key, path)

        # (5) combined-destination validation + atomic commit, retried on a lost race so
        # NOTHING is ever partially imported (§4c). The destination is re-read each pass.
        # specs/0008 §6e (T11b, research's M3): the import's ONE clock read — no arriving REPLY's write time is later
        # than it (a confirmation's `confirmed_at` is in the projection and is never clamped: research's T11b S2-6(a)). The
        # store's clock where it has one (injectable, as the writers' is), so the clamp and the local writes agree
        now = store._now() if hasattr(store, "_now") else datetime.now(timezone.utc)
        for _attempt in range(_IMPORT_RETRIES):
            outcome = _preflight_and_commit(store, path, target_uid, edges, eps,
                                            incoming_chains, contrib_rows,
                                            capped_path=not restore, notices=notice_list,
                                            outcomes=arity_outcomes, src_arity_state=src_arity_state,
                                            registry=reg, import_op=import_op, inputs_digest=inputs_digest,
                                            acts=acts, now=now)
            if outcome is not DESTINATION_CHANGED:
                if redaction_arrivals:                 # the rider's arrivals: the held output treated, flagged (§4g)
                    _na = {(x[0], x[1]) for x in outcome.get("notices_not_applied", [])}
                    treated = {i for i in redaction_arrivals if ("episode", i) not in _na}   # only where it WAS applied
                    outcome = {**outcome, "inconsistent_notices": sorted(set(outcome.get("inconsistent_notices", []))
                                                                         | treated)}
                return {**outcome, "capped": capped_count,
                        # specs/0041 §4g: what the notices did, and the tombstones that came without one
                        "unattested_markers": unattested_markers,
                        "agreement_mismatches": agreement_mismatches,
                        # specs/0037 §4e: refused PER RECORD before the commit,
                        # the admitted set committed atomically as one transaction
                        "procedural_refused": len(procedural_refusals),
                        "procedural_refusals": procedural_refusals,
                        # T11b: acts refused with the record they name (that record's own refusal is listed above)
                        "acts_refused_with_edge": acts_refused_with_edge,
                        "user_id": target_uid}
        _SITE_IMPORT_RACE_EXHAUSTED.consult()
        raise _SITE_IMPORT_RACE_EXHAUSTED.fire(ValueError(f"{path}: import kept losing a race against concurrent writes "
                         f"after {_IMPORT_RETRIES} attempts — refused (specs/0009 §4c)"))


def _held_instant(v) -> str:
    """A held outcome's `pre_invalidated_at` (the inventory's bytes, possibly naive or 'Z') as the canonical text the
    projection compares (build note D15): naive reads UTC, as lifetime's instant test reads it."""
    from .schema import as_utc_required
    try:
        return as_utc_required(v).isoformat()
    except (TypeError, ValueError):
        return v


def _arity_preflight(store, path, target_uid, outcomes, src_state, edges, existing_edges, *, restore, registry,
                     import_op, inputs_digest, notice_targets) -> tuple:
    """0044 §4l over the STAGED UNION (destination ∪ unit, after remapping), before any write — (rows to insert, exact
    replays, the conversion plan, the report, the expected arity state the commit re-checks).
    - Replay is decided by COMPARISON: a held uid with an equal projection is a no-op; a held ended/undone row and an
      arrival that differs only by being live is older evidence of the same episode, a no-op; any other difference, or
      a held uid of another user, refuses the whole import. An arrival whose edge is a notice target in this unit is
      compared after that treatment (its live stage reads ended).
    - One outcome per destination EDGE (build note D6c, stricter than the (plan, edge) slot): an arriving uid on an edge
      that holds another refuses.
    - Trust (§4l's table, the 0008 amendment's origin matrix): a default import writes every outcome `imported`
      (testimony); a trusted restore maps local -> restored and never upgrades `imported`.
    - THE OWNER'S D3 RULING (2026-10-19, plan state + narrow): a CANDIDATE is a unit edge not already held, retired
      `superseded` under a relation the default registry reclassifies AND the receiving registry declares multi (T4),
      not a notice target, with no outcome in the staged union under any plan (T1, D6b). The source DECIDED iff the
      file carries a plan-state record. An undecided source's candidates are REFUSED into an uninitialized destination
      (`requires-data-migration-plan`, naming the plan-only mode), converted under an initialized one's plan relations
      (§4f's steps, in the import's transaction), and reported `nothing-to-convert` by an initialized-empty one. A
      decided source's candidates under the destination's plan relations — the default names when it has none (D13) —
      are reported `unknown-linkage`, kept retired, never reinstated by guess."""
    from .registry import declared_arity
    from .store import lifetime as _lifetime
    reg = registry if registry is not None else DEFAULT_RELATIONS
    names = set(_lifetime.RECLASSIFIED_RELATIONS) & {n for n, v in reg.items() if declared_arity(v) == "multi"}
    out_edges = {o["edge_id"] for o in outcomes}
    candidates = [e for e in edges if e.id not in existing_edges and not e.active
                  and e.invalidation_reason == _lifetime.SUPERSEDED and e.relation in names
                  and ("edge", e.id) not in notice_targets and e.id not in out_edges]
    report = {"arity_conversion": None, "arity_unknown_linkage": []}
    if not outcomes and not candidates:
        return [], 0, None, report, None
    held_by_edge: dict = {}
    for r in store.migration_outcomes(target_uid):
        held_by_edge.setdefault(r["edge_id"], []).append(r)
    candidates = [e for e in candidates if e.id not in held_by_edge]
    held_by_uid = store.migration_outcomes_by_uid([o["outcome_uid"] for o in outcomes])
    dest = store.arity_plan_state()
    rows, existing, conversion = [], 0, None
    with _SITE_IMPORT_ARITY_PREFLIGHT.consult():
        for o in outcomes:
            if o["stage"] == "live" and ("edge", o["edge_id"]) in notice_targets:
                o = {**o, "stage": "ended"}
            held = held_by_uid.get(o["outcome_uid"])
            if held is not None:
                hp = {**held, "pre_invalidated_at": _held_instant(held["pre_invalidated_at"]),
                      "successor_evidence": json.loads(held["successor_evidence"]), "stage": _outcome_stage(held)}
                same = held["user_id"] == target_uid and (
                    _outcome_projection(hp) == _outcome_projection(o)
                    or (hp["stage"] in ("ended", "undone") and o["stage"] == "live"
                        and _outcome_projection(hp)[:-1] == _outcome_projection(o)[:-1]))
                if not same:
                    raise _SITE_IMPORT_ARITY_PREFLIGHT.fire(ValueError(
                        f"{path}: arity outcome {o['outcome_uid']!r} is held here with a different projection (or for "
                        f"another user) — an outcome's replay is decided by comparison; refused whole (specs/0044 §4l, "
                        f"INV-A23)"), "outcome-replay-conflict")
                existing += 1
                continue
            if any(r["outcome_uid"] != o["outcome_uid"] for r in held_by_edge.get(o["edge_id"], [])):
                raise _SITE_IMPORT_ARITY_PREFLIGHT.fire(ValueError(
                    f"{path}: edge {o['edge_id']!r} already holds an arity outcome under another uid — one outcome per "
                    f"edge, refused whole (specs/0044 §4l; build note D6c)"), "outcome-slot-held")
            origin = "imported" if not restore else ("restored" if o["origin"] in ("local", "restored") else "imported")
            rows.append({"plan_id": o["plan_id"], "user_id": target_uid, "edge_id": o["edge_id"], "outcome": o["outcome"],
                         "pre_invalidated_at": o["pre_invalidated_at"], "pre_reason": o["pre_reason"],
                         "successor_evidence": json.dumps(o["successor_evidence"], separators=(",", ":")),
                         "applicable": int(o["stage"] == "live"), "origin": origin, "outcome_uid": o["outcome_uid"],
                         "undone_at": o["undone_at"], "undo_request_ref": None,
                         "op_id": None if origin == "imported" else import_op})
        # the owner's T11a S2-1 ruling (2026-10-20, option c): on a TRUSTED RESTORE the refusal is DECISION-BLIND — a
        # restore carrying a candidate into a store with no plan refuses whether the file's source decided or not, so a
        # store's own backup restored into a fresh store never loses "decided" (it would re-export undecided)
        if candidates and dest["state"] == "uninitialized" and (src_state == "uninitialized" or restore):
            raise _SITE_IMPORT_ARITY_PREFLIGHT.fire(ValueError(
                f"{path}: the file carries {len(candidates)} retired row(s) under a reclassified relation"
                + (" from a store that had not decided its arity restoration" if src_state == "uninitialized" else
                   ", and a trusted restore into a store without a plan would lose its source's decision")
                + ", and this store has no plan — run run_data_migration(path, ..., plan_only=True) first (it writes "
                  "the plan and restores nothing), then import again (specs/0044 §4l, Q9; the owner's D3 and T11a "
                  "S2-1 rulings)"), "requires-data-migration-plan")
        if candidates and src_state == "uninitialized":
            conv_rows = [(e.id, e.invalidated_at.isoformat(), _lifetime.SUPERSEDED) for e in candidates
                         if e.relation in dest["relations"]]
            if conv_rows:
                conversion = {"plan_id": dest["plan_id"], "rows": conv_rows, "op_id": import_op,
                              "inputs_digest": inputs_digest}
                report["arity_conversion"] = "converted"
            else:
                report["arity_conversion"] = "nothing-to-convert"
        elif candidates:
            rels = dest["relations"] or names      # an uninitialized OR empty plan: the default names (S2-3, D13)
            report["arity_unknown_linkage"] = sorted(e.id for e in candidates if e.relation in rels)
    touched = out_edges | {e.id for e in candidates}
    expected = {"plan_id": dest["plan_id"],
                "outcome_uids": {o["outcome_uid"]: held_by_uid.get(o["outcome_uid"]) for o in outcomes},
                "edge_outcomes": {eid: sorted(r["outcome_uid"] for r in held_by_edge.get(eid, [])) for eid in touched}}
    return rows, existing, conversion, report, expected


def _act_preflight(store, path, target_uid, acts, edges, existing_edges, *, restore, notices, now) -> tuple:
    """specs/0008 §6e–§6f / 0047 §4f / 0041 §11.6.6 (T11b) over the STAGED UNION (destination ∪ unit, after remapping),
    before any write — (rows to insert, exact replays, the expected act state the commit re-checks).
    - Per arriving act: an edge in neither the unit nor the destination refuses the whole file (INV-R11); rule 0, a
      DEFAULT file carrying this store's origin, refuses (read on the act as admitted, the owner's R-D6); coverage is
      all or nothing per row and a marker carrier needs a notice attesting it (INV-RR3/RR6/RR9); two copies of one
      `act_uid` in the unit with differing TREATED projections refuse (rule 2, INV-I6).
    - Rule 1 before rule 3: a held `act_uid` (store-wide; another user's refuses) with an equal treated projection is an
      exact replay and writes nothing (INV-I1, I4, I7); a differing one refuses (rule 2, INV-I2). Rule 3: a NEW act over
      an edge the destination held before this import, in a default import, refuses (INV-R16). Rule 4: admitted, its
      label by the origin matrix (INV-Q5/R21), an internal `#act:` key over its admitted uid, no registry row, no
      position from this store's counter (INV-Q4′), written treated where the coverage attests its carriers, and an
      arriving `written_at` later than this import's clock read clamped to it (research's M3).
    - A resolve names a challenge of its edge in H, by identity; then §6f over H: ties, a second resolve, a resolve
      before its challenge, and every challenge/confirmation pair of an edge of which one is new (INV-Q10, R23)."""
    if not acts:
        return [], 0, None
    from .store.data_migration import portable_uid
    local = store.local_origin()
    unit_edges = {e.id: e for e in edges}
    now_txt = now.astimezone(timezone.utc).isoformat()
    afields: dict = {}
    for n in notices:
        if n["target_kind"] == "edge":
            afields.setdefault(n["target_id"], set()).update(n["fields"])
    covs: dict = {}

    def cov(eid):
        if eid not in covs:
            covs[eid] = frozenset(store._attested_fields(target_uid, "edge", eid, coverage=True) | afields.get(eid, set()))
        return covs[eid]

    def carriers(a):
        if a["table"] == "confirmations":
            return {"confirmations.request_digest": a["request_digest"]}
        return {p: v for p, v in (("replies.text", a["text"]), ("replies.request_digest", a["request_digest"]))
                if v is not None}

    with _SITE_IMPORT_ACT_PREFLIGHT.consult():
        uniq: dict = {}
        for a in acts:
            e = unit_edges.get(a["edge_id"]) or existing_edges.get(a["edge_id"])
            if e is None:
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: {_ACT_NOUN[a['table']]} {a['act_uid']!r} names edge {a['edge_id']!r}, which neither the file nor "
                    f"this store holds — the whole file is refused, nothing imported (specs/0047 §4f, INV-R11)"),
                    "act-orphan")
            if not restore and a["act_uid"][0] == local:
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: act {a['act_uid']!r} claims THIS store's origin — only a trusted restore of its own history "
                    f"may carry it (specs/0008 §6e rule 0, INV-Q9). {_RESTORE_WARNING}"), "act-own-origin")
            c = cov(a["edge_id"])
            car = carriers(a)
            if any(v == _redaction.MARKER and p not in c for p, v in car.items()):
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: act {a['act_uid']!r} carries the marker with no notice attesting it — a fabricated tombstone, "
                    f"refused (specs/0041 §11.6.6, INV-RR3)"), "act-marker-unattested")
            redacted = bool(c) or bool(_redaction.marker_fields(json.loads(e.model_dump_json())))
            if redacted and not set(car) <= c:
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: act {a['act_uid']!r} arrives onto a redacted edge whose notices attest "
                    f"{sorted(c & set(car))}, not all of {sorted(car)} — coverage is all or nothing per row, refused "
                    f"(specs/0008 §6e, INV-RR6, INV-RR9)"), "act-coverage")
            p = _act_projection(a, c)
            if a["act_uid"] in uniq and uniq[a["act_uid"]][1] != p:
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: act {a['act_uid']!r} appears twice in the file with different contents — refused whole "
                    f"(specs/0008 §6e rule 2, INV-I6)"), "act-replay-conflict")
            uniq.setdefault(a["act_uid"], (a, p))
        targets = {a["target_uid"] for a, _p in uniq.values() if a["target_uid"] is not None}
        positions = {(u[0], a["act_seq"]) for u, (a, _p) in uniq.items() if a["act_seq"] is not None}
        touched = {a["edge_id"] for a, _p in uniq.values()}
        args = (sorted(set(uniq) | targets), sorted(positions), sorted(touched))
        state = store.act_state(target_uid, *args)
        id_uid = {r["id"]: _held_act_uid(r, local) for rows in (*state["by_edge"].values(), *state["uids"].values())
                  for r in rows}

        def held(r):
            conf = r["table"] == "confirmations"
            return {"table": r["table"], "act_uid": _held_act_uid(r, local), "act_seq": r["act_seq"],
                    "edge_id": r["edge_id"], "kind": "confirm" if conf else r["kind"],
                    "target_uid": None if conf or r["target"] is None else id_uid.get(r["target"], ("?", "?", r["target"])),
                    "text": None if conf else r["text"], "actor": r["actor"], "call_path": r.get("call_path"),
                    "confirmed_at": _held_instant(r["confirmed_at"]) if conf else None,
                    "recorded_correlation_id": _held_original_id(r), "request_digest": r["request_digest"],
                    "label": r["origin"], "id": r["id"], "user_id": r["user_id"]}

        rows, new, existing = [], [], 0
        for uid, (a, p) in uniq.items():
            hs = state["uids"][uid]
            if hs:
                h = held(hs[0])
                if len(hs) > 1 or h["user_id"] != target_uid or _act_projection(h, cov(a["edge_id"])) != p:
                    raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                        f"{path}: act {uid!r} is held here with a different projection (or for another user) — a "
                        f"conflicting replay refuses the whole file (specs/0008 §6e rule 2, INV-I2)"), "act-replay-conflict")
                existing += 1                          # rule 1: an exact replay writes nothing and grants nothing
                continue
            if not restore and a["edge_id"] in existing_edges:
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: act {uid!r} is new and acts on edge {a['edge_id']!r}, which this store already holds — an "
                    f"untrusted file cannot act as the subject over a local fact (specs/0008 §6e rule 3, 0047 §4f, "
                    f"INV-R16)"), "act-held-target")
            c = cov(a["edge_id"])
            conf = a["table"] == "confirmations"
            label = "imported" if not restore else ("restored" if a["origin"] == "local" else a["origin"])
            written = a["written_at"]
            if written is not None and datetime.fromisoformat(written) > now:
                written = now_txt                      # M3: no file dates a reply's write after this import
            row = {"table": a["table"], "id": ("c-" if conf else "r-") + uuid4().hex[:12], "user_id": target_uid,
                   "edge_id": a["edge_id"], "confirmed_at": a["confirmed_at"], "actor": a["actor"],
                   "call_path": a["call_path"], "kind": a["kind"], "target": None,
                   "text": _redaction.MARKER if a["text"] is not None and "replies.text" in c else a["text"],
                   "correlation_id": "#act:" + portable_uid(*uid)[:32],
                   "request_digest": (_redaction.MARKER if ("confirmations." if conf else "replies.") + "request_digest" in c
                                      else a["request_digest"]),
                   "origin": label, "recorded_correlation_id": a["recorded_correlation_id"], "origin_store": uid[0],
                   "origin_user": uid[1], "origin_act_id": uid[2], "act_seq": a["act_seq"], "written_at": written}
            rows.append(row)
            new.append(dict(a, label=label, id=row["id"], user_id=target_uid))
        held_by_uid = {_held_act_uid(r, local): r for rs in state["uids"].values() for r in rs}
        new_by_uid = {a["act_uid"]: (a, row) for a, row in zip(new, rows)}
        for a, row in new_by_uid.values():
            if a["kind"] != "resolve":
                continue
            t = a["target_uid"]
            ch = new_by_uid[t][0] if t in new_by_uid else (held(held_by_uid[t]) if t in held_by_uid else None)
            if ch is None or ch["kind"] != "challenge" or ch["edge_id"] != a["edge_id"] or ch["user_id"] != target_uid:
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: resolve {a['act_uid']!r} names no challenge of its edge in the merged history — refused "
                    f"whole (specs/0008 §6f, 0047 INV-R14)"), "act-resolve-target")
            row["target"] = ch["id"]
        # §6f over H: the user's held acts on every touched edge, and every act this import admits
        fresh = set(new_by_uid)
        H = [held(r) for rs in state["by_edge"].values() for r in rs] + new
        for a in new:
            if a["act_seq"] is None:
                continue
            pos = (a["act_uid"][0], a["act_seq"])
            others = [_held_act_uid(r, local) for r in state["positions"].get(pos, [])]
            others += [b["act_uid"] for b in new if (b["act_uid"][0], b["act_seq"]) == pos]
            if any(o != a["act_uid"] for o in others):
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: two different acts at one position {pos!r} — the counter never issues a position twice, so "
                    f"the history is forged or corrupted; refused whole (specs/0008 §6f, INV-Q10)"), "act-tie")
        by_uid = {a["act_uid"]: a for a in H}
        resolves: dict = {}
        for a in H:
            if a["kind"] == "resolve":
                resolves.setdefault(a["target_uid"], []).append(a)
        for cu, rs in resolves.items():
            if not (cu in fresh or any(r["act_uid"] in fresh for r in rs)):
                continue
            if len(rs) > 1:
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: challenge {cu!r} is resolved more than once in the merged history — refused whole "
                    f"(specs/0008 §6f, INV-Q10)"), "act-second-resolve")
            if cu in by_uid and _act_ordered(rs[0], by_uid[cu], restore) is True:
                raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                    f"{path}: resolve {rs[0]['act_uid']!r} is ordered before its own challenge — refused whole (specs/0008 "
                    f"§6f, INV-Q10)"), "act-resolve-before-challenge")
        challenges = [a for a in H if a["kind"] == "challenge"]
        for k in (a for a in H if a["kind"] == "confirm"):
            for c in challenges:
                if c["edge_id"] != k["edge_id"] or not (k["act_uid"] in fresh or c["act_uid"] in fresh):
                    continue
                o = _act_ordered(k, c, restore)
                if o is True:
                    continue                           # the confirmation was made before the challenge
                rs = resolves.get(c["act_uid"], [])
                if o is False and not any(_act_ordered(r, k, restore) is True for r in rs):
                    raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                        f"{path}: confirmation {k['act_uid']!r} was made under challenge {c['act_uid']!r}, which no resolve "
                        f"ordered before the confirmation closes in the merged history — refused whole (specs/0008 §6f, 0047 "
                        f"§4c, INV-R23)"), "act-under-challenge")
                if o is None and not rs:
                    raise _SITE_IMPORT_ACT_PREFLIGHT.fire(ValueError(
                        f"{path}: confirmation {k['act_uid']!r} cannot be ordered against challenge {c['act_uid']!r}, which "
                        f"is unresolved in the merged history (another origin, or an unknown position) — refused whole, "
                        f"never guessed (specs/0008 §6f, INV-R23)"), "act-order-unknown")
    return rows, existing, {"args": args, "state": state}


def _preflight_and_commit(store, path, target_uid, edges, eps, incoming_chains,
                          contrib_rows, *, capped_path: bool = True, notices=None, outcomes=(),
                          src_arity_state="uninitialized", registry=None, import_op=None, inputs_digest=None,
                          acts=(), now=None):
    """One preflight-then-commit pass: validate the COMBINED destination graph
    against the live store, build the plan + the full destination-state assumptions,
    and commit atomically. Returns the store's result (counts dict or
    `DESTINATION_CHANGED`). specs/0009 §4c.

    `capped_path` (specs/0005 §4d): on the default (capping) import path the
    record-equality refusals append the pinned `--restore` warning, because
    the commonest trigger is an own-store re-import whose stored originals
    differ from the capped incoming form (P10); the warning is never a bare
    remedy (P15). Restore-path refusals keep the plain message."""
    with _SITE_IMPORT_PREFLIGHT.consult():
        _tail = f". {_RESTORE_WARNING}" if capped_path else ""
        existing_edges = {e.id: e for e in store.edges(
            target_uid, active_only=False, include_quarantined=True)}
        existing_eps = {ep.id: ep for ep in store.episodes(target_uid)}
        importing_edge_ids = {e.id for e in edges}

        plan_edges: list = []
        plan_eps: list = []
        skipped = 0
        notices = notices or []
        notice_targets = {(n["target_kind"], n["target_id"]) for n in notices}
        inconsistent: list = []          # specs/0041 §4g: a held DIFFERENT version under a notice — redacted anyway, flagged
        edge_ids_expected: dict = {}     # id -> expected-present
        ep_records_expected: dict = {}   # id -> current-persisted-json (None if absent)
        chain_heads_expected: dict = {}  # (edge_id, evidence_ref) -> head id or None
        axis_kept: list = []             # research's M2: a held default-import axis kept over a restore's recorded one

        # edges: record-equal existing → idempotent skip; differing → the held-differs rule; new → insert
        for edge in edges:
            prior = existing_edges.get(edge.id)
            if prior is not None:
                # specs/0045 (T11b, build note D11 with research's M2): in a DEFAULT import the axis is a WRITE rule (the
                # file's is discarded and the row stamped), so equality excludes it; a TRUSTED RESTORE carries the
                # recorded axis, so it compares it (a held edge never has its axis rewritten, INV-G13) — except where the
                # held axis is `default-import`, this store's own judgement at a default import (as an act's trust label
                # is, §6e): kept, and listed
                if capped_path:
                    differs = _without_axis(prior.model_dump()) != _without_axis(edge.model_dump())
                elif prior.attv == _DEFAULT_IMPORT and _without_axis(prior.model_dump()) == _without_axis(edge.model_dump()):
                    differs = False
                    if prior.model_dump() != edge.model_dump():
                        axis_kept.append(edge.id)
                else:
                    differs = prior.model_dump() != edge.model_dump()
                if differs:
                    _v = held_differs_verdict(store._completed_attestation(target_uid, "edge", edge.id), ("edge", edge.id) in notice_targets)
                    if _v == "attested-redaction":
                        raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(
                            f"{path}: edge {edge.id!r} is redacted here (a redaction record attests it) and the file "
                            f"carries no notice for it — an import may not repopulate it (specs/0041 §4b-ii, INV-11; §4g)"), "attested-redaction")
                    if _v == "conflict":
                        raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(f"{path}: edge {edge.id!r} already exists with different content — refuse (specs/0009 §4c){_tail}"), "edge-conflict")
                    inconsistent.append(("edge", edge.id))           # "inconsistent": skip, the notice treats the held version
                skipped += 1
                edge_ids_expected[edge.id] = True
            else:
                plan_edges.append(edge)
                edge_ids_expected[edge.id] = False

        # every outcome chain's edge_id must resolve to an Edge owned by the target user
        for (edge_id, _evref) in incoming_chains:
            if edge_id not in importing_edge_ids and edge_id not in existing_edges:
                raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(f"{path}: outcome chain references edge {edge_id!r}, "
                                 f"which is missing or foreign to {target_uid!r} — refuse "
                                 f"(specs/0009 §4c)"), "chain-edge-missing")
            edge_ids_expected.setdefault(edge_id, edge_id in existing_edges)

        # non-outcome episodes: same record-equality idempotency as edges
        for ep in eps:
            if ep.kind == "outcome":
                continue
            prior = existing_eps.get(ep.id)
            ep_records_expected[ep.id] = None if prior is None else prior.model_dump_json()
            if prior is not None:
                if prior.model_dump() != ep.model_dump():
                    _v = held_differs_verdict(store._completed_attestation(target_uid, "episode", ep.id), ("episode", ep.id) in notice_targets)
                    if _v == "attested-redaction":
                        raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(
                            f"{path}: episode {ep.id!r} is redacted here (a redaction record attests it) and the file "
                            f"carries no notice for it — an import may not repopulate it (specs/0041 §4b-ii, INV-11; §4g)"), "attested-redaction")
                    if _v == "conflict":
                        raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(f"{path}: episode {ep.id!r} already exists with different content — refuse (specs/0009 §4c){_tail}"), "episode-conflict")
                    inconsistent.append(("episode", ep.id))        # "inconsistent": skip, the notice treats the held version
                skipped += 1
            else:
                plan_eps.append(ep)

        # outcome chains: prefix-extend-or-refuse against the COMBINED destination graph
        for key, members in incoming_chains.items():
            edge_id, evref = key
            dest = [ep for ep in existing_eps.values()
                    if ep.kind == "outcome" and _chain_id(ep) == key]
            dest_by_id = {m.id: m for m in dest}
            dest_head = max(dest, key=lambda m: m.seq or 0) if dest else None
            chain_heads_expected[key] = dest_head.id if dest_head else None

            new_members = []
            for m in sorted(members, key=lambda m: m.seq or 0):
                ep_records_expected[m.id] = (
                    dest_by_id[m.id].model_dump_json() if m.id in dest_by_id else None)
                prior = dest_by_id.get(m.id)
                if prior is not None:
                    if prior.model_dump() != m.model_dump():   # RECORD equality, not id
                        if _outcome_structure(prior) != _outcome_structure(m):
                            raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(
                                f"{path}: outcome link {m.id!r} already exists with a different chain STRUCTURE "
                                f"({', '.join(OUTCOME_LINK_STRUCTURE)}) — outcome history is never overwritten, notice "
                                f"or not; refuse the whole import (specs/0009 §4c, specs/0041 §4h){_tail}"),
                                "outcome-link-conflict")
                        # round 11 (R10-01): the same held-differs rule as edges and episodes — a notice for the
                        # link redacts the held version in the commit and flags it; without one, refuse
                        _v = held_differs_verdict(store._completed_attestation(target_uid, "episode", m.id), ("episode", m.id) in notice_targets)
                        if _v == "attested-redaction":
                            raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(
                                f"{path}: episode {m.id!r} is redacted here (a redaction record attests it) and the file "
                                f"carries no notice for it — an import may not repopulate it (specs/0041 §4b-ii, INV-11; §4g)"), "attested-redaction")
                        if _v == "conflict":
                            raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(f"{path}: outcome link {m.id!r} already exists with different content — refuse the whole import (specs/0009 §4c){_tail}"), "outcome-link-conflict")
                        inconsistent.append(("episode", m.id))        # "inconsistent": skip, the notice treats the held version
                    skipped += 1
                else:
                    new_members.append(m)
            if new_members:
                first_new = new_members[0]
                if first_new.supersedes_episode != (dest_head.id if dest_head else None):
                    raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(
                        f"{path}: outcome chain {key} does not extend the destination head "
                        f"{(dest_head.id if dest_head else None)!r} (would branch or "
                        f"diverge) — refuse (specs/0009 §4c)"), "chain-head-mismatch")
                plan_eps.extend(new_members)

        # specs/0009 §4c as amended (0020/0021): the contribution preflight —
        # for every survivor the reconstructed rows attribute, the destination's
        # current ledger rows must be ABSENT (first import) or EXACTLY EQUAL by
        # plan_row_id set equality (idempotent re-import → the rows skip). A
        # conflicting recorded history refuses the WHOLE import here, cleanly;
        # the primitive re-runs the same gate atomically (a mid-flight race
        # surfaces as DESTINATION_CHANGED and this preflight re-reads).
        contribution_state: dict = {}
        contrib_survivors = sorted({r["survivor_id"] for r in contrib_rows})
        for sid in contrib_survivors:
            current = [c.id for c in store.contributions(target_uid, "edge", sid)]
            planned = {r["id"] for r in contrib_rows if r["survivor_id"] == sid}
            if current and set(current) != planned:
                raise _SITE_IMPORT_PREFLIGHT.fire(ValueError(
                    f"{path}: destination record {sid!r} already carries a "
                    f"DIFFERENT recorded absorption history ({len(current)} "
                    f"ledger row(s) not plan-row-equal to the reconstruction) — "
                    f"a different history is refused whole, nothing written "
                    f"(specs/0009 §4c as amended by 0020/0021)"), "scope-rows-conflict")
            contribution_state[sid] = sorted(current)

        # specs/0044 §4l (T11a): the outcome rows and the D3 decision over the staged union
        outcome_rows, outcomes_existing, conversion, arity_report, arity_expected = _arity_preflight(
            store, path, target_uid, list(outcomes), src_arity_state, edges, existing_edges, restore=not capped_path,
            registry=registry, import_op=import_op, inputs_digest=inputs_digest, notice_targets=notice_targets)
        # specs/0008 §6e–§6f (T11b): the acts, over the same staged union
        act_rows, acts_existing, acts_expected = _act_preflight(
            store, path, target_uid, list(acts), edges, existing_edges, restore=not capped_path, notices=notices,
            now=now if now is not None else datetime.now(timezone.utc))
        plan = {"edges": plan_edges, "episodes": plan_eps,
                "acts": act_rows,
                "outcomes": outcome_rows, "arity_conversion": conversion,
                "contributions": contrib_rows, "redactions": notices,
                # specs/0041 §11.6.6: the MODE the binding table reads — a trusted restore ("any") applies a notice to a
                # held record whose file copy (or held self) shows it; a default import ("created") applies one only to a
                # record it creates showing it, and leaves every held target's notice PENDING
                "notice_scope": "created" if capped_path else "any"}
        expected = {"edge_ids": edge_ids_expected,
                    "episode_records": ep_records_expected,
                    "chain_heads": chain_heads_expected,
                    "contribution_state": contribution_state}
        if arity_expected is not None:
            expected["arity"] = arity_expected
        if acts_expected is not None:
            expected["acts"] = acts_expected
        result = store.commit_outcome_import_plan(target_uid, plan, expected)
        if result is DESTINATION_CHANGED:
            return DESTINATION_CHANGED
        return {"edges": result["edges"],
                "episodes": result["episodes"], "skipped": skipped,
                # specs/0044 §4l (T11a): outcomes written and exact replays; the D3 decision and its rows
                "outcomes": result.get("outcomes", 0), "outcomes_existing": outcomes_existing,
                "arity_conversion": arity_report["arity_conversion"],
                "arity_restored": result.get("arity_restored", []), "arity_withheld": result.get("arity_withheld", []),
                "arity_unknown_linkage": arity_report["arity_unknown_linkage"],
                # specs/0008 §6e (T11b): acts written per table, and exact replays; held default-import axes kept (M2)
                "confirmations": result.get("confirmations", 0), "replies": result.get("replies", 0),
                "acts_existing": acts_existing, "axis_kept_default_import": sorted(axis_kept),
                "contributions": result.get("contributions", 0),
                "contributions_existing": result.get("contributions_existing", 0),
                "notices_applied": result.get("notices_applied", 0),
                "notices_standing": result.get("notices_standing", 0),
                "notices_existing": result.get("notices_existing", 0),
                # `inconsistent_notices` keeps its meaning (the held version WAS redacted), so a target whose notice this
                # import left PENDING is not in it; those are in `notices_not_applied` ([kind, id, reason]: `held-target`,
                # `record-not-in-file`, `standing-arrival` — specs/0041 §11.6.6), never applied by the file's word
                "inconsistent_notices": sorted({i for k, i in inconsistent
                                                if (k, i) not in {(x[0], x[1]) for x in result.get("notices_not_applied", [])}}),
                "notices_not_applied": result.get("notices_not_applied", [])}
