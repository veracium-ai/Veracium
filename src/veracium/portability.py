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

from .schema import (Disclosure, Edge, Episode, EvidenceAuthor, Provenance,
                     is_historical_id, to_historical_id)
from .source_identity import resolve_origin
from .store.base import DESTINATION_CHANGED, NON_QUIESCENT

# specs/0014 §4c/§7a (R5-4): the exported Episode.consolidation_output_index
# field bumps the format 4→5 per accepted 0010's refuse-don't-drop rule — an
# older importer REFUSES a v5 export rather than silently dropping the field.
# specs/0019: v6 added the `ungrounded` flag (same refuse-don't-drop rule).
FORMAT_VERSION = 7  # specs/0016 D2 (0019 rider A3): the source_type-less
                    # file — a v7 export omits the deleted key entirely; an
                    # OLD build's Provenance REQUIRED source_type, so without
                    # the bump a new export died there as a pydantic error —
                    # the bump makes it an honest version refusal. A ≤6
                    # file's provenance.source_type key is DROPPED on import
                    # (the record otherwise intact, §2c row 1).
_IMPORT_RETRIES = 8   # bounded whole-import retries before refusing a persistent race

# specs/0005 §4d — the PINNED default-path refusal warning (P10/P15). A bare
# pointer at --restore would recruit the operator into the bypass on a
# tampered own-export; the message must carry both halves.
_RESTORE_WARNING = (
    "import refused: existing records differ from the capped incoming form. "
    "If - and only if - this file is your own store's export, --restore "
    "imports it with trust preserved. --restore trusts every record in the "
    "file exactly as written; use it only on a file you exported yourself or "
    "have independently verified, record by record (specs/0005 §4d)")


def export_memory(store, user_id: str, path) -> dict:
    """Write `user_id`'s complete memory (all edges incl. superseded and
    quarantined, all episodes) to `path` as JSONL. Returns counts."""
    # specs/0010 §4f/X17: export is a READ-ONLY quiescent snapshot. The quiescence
    # check and the episode snapshot are ONE atomic, linearizable observation — a
    # claim starting mid-export yields NON_QUIESCENT, never a dangling `claimed_by`.
    # Export never mutates; the caller runs consolidate()/maintain() first and retries.
    episodes = store.quiescent_episode_snapshot(user_id)
    if episodes is NON_QUIESCENT:
        raise ValueError(
            f"export refuses: a consolidation is in flight for {user_id!r} — run "
            f"consolidate()/maintain() to settle it, then retry (specs/0010 §4f)")
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

    path = Path(path)
    with path.open("w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": FORMAT_VERSION,
                            "user_id": user_id,
                            "exported_at": datetime.now(timezone.utc).isoformat()})
                + "\n")
        for e in edges:
            f.write(json.dumps({"record": "edge", **_materialise(json.loads(e.model_dump_json()))})
                    + "\n")
        for ep in episodes:
            rec = _materialise(json.loads(ep.model_dump_json()))
            # specs/0014 §4c (R7-3): the index serializes with EXCLUDE-NONE
            # semantics — OMITTED when None (a stated exception to the default;
            # an explicit null on import is malformed). A native v5 output
            # always carries its index; absence is the unprivileged legacy shape.
            if rec.get("consolidation_output_index") is None:
                rec.pop("consolidation_output_index", None)
            f.write(json.dumps({"record": "episode", **rec}) + "\n")
    return {"edges": len(edges), "episodes": len(episodes), "path": str(path)}


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


def _chain_id(ep: Episode) -> tuple:
    """The `(edge_id, evidence_ref)` identity that groups one outcome chain."""
    return (ep.edge_id, ep.provenance.evidence_ref)


def _validate_incoming_chain(members: list, key, path) -> tuple:
    """specs/0009 §4c per-chain topology: a valid outcome chain is a single
    `1`-rooted, dense-`+1`, single-leaf path within one identity — no branch, no
    cycle, no gap. Refuse (never repair) anything else. Returns (root, leaf)."""
    by_id = {m.id: m for m in members}
    roots = [m for m in members if m.supersedes_episode is None]
    if len(roots) != 1:
        raise ValueError(f"{path}: outcome chain {key} has {len(roots)} roots — "
                         f"import refuses rather than repairing (specs/0009 §4c/H5)")
    root = roots[0]
    if (root.seq or 0) != 1:
        raise ValueError(f"{path}: outcome chain {key} root seq={root.seq!r} != 1 — "
                         f"imported history must inhabit the store's state space "
                         f"(specs/0009 §4c/H5)")
    child_of: dict = {}
    for m in members:
        if m.supersedes_episode is None:
            continue
        pred = by_id.get(m.supersedes_episode)
        if pred is None:
            raise ValueError(f"{path}: outcome chain {key} link {m.id!r} supersedes "
                             f"{m.supersedes_episode!r}, absent from this chain — "
                             f"refuse (specs/0009 §4c/H5)")
        if (m.seq or 0) != (pred.seq or 0) + 1:
            raise ValueError(f"{path}: outcome chain {key} is not dense +1 at "
                             f"{m.id!r} (seq {m.seq!r} on parent {pred.seq!r}) — "
                             f"refuse (specs/0009 §4c/H5)")
        if m.supersedes_episode in child_of:
            raise ValueError(f"{path}: outcome chain {key} branches at "
                             f"{m.supersedes_episode!r} — refuse (specs/0009 §4c/H5)")
        child_of[m.supersedes_episode] = m
    leaves = [m for m in members if m.id not in child_of]
    if len(leaves) != 1:
        raise ValueError(f"{path}: outcome chain {key} has {len(leaves)} leaves — "
                         f"refuse (specs/0009 §4c/H5)")
    leaf = leaves[0]
    seen: set = set()
    cur = leaf
    while cur is not None:
        if cur.id in seen:
            raise ValueError(f"{path}: outcome chain {key} has a cycle — refuse "
                             f"(specs/0009 §4c/H5)")
        seen.add(cur.id)
        cur = by_id.get(cur.supersedes_episode) if cur.supersedes_episode else None
    if len(seen) != len(members) or (leaf.seq or 0) != len(members):
        raise ValueError(f"{path}: outcome chain {key} is disconnected or has a "
                         f"seq gap — refuse (specs/0009 §4c/H5)")
    return root, leaf


def import_memory(store, path, *, user_id: Optional[str] = None,
                  restore: bool = False) -> dict:
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
    concurrent `append_outcome_if_head` (no branch, no partial import). Returns counts."""
    # specs/0005 §4a — the two argument gates, in order, BEFORE the file is
    # opened: the closed bool predicate (P13), then mutual exclusion (P5).
    if type(restore) is not bool:
        raise TypeError(
            f"restore must be a bool, got {type(restore).__name__!s} — no "
            f"truthiness coercion at a trust boundary (specs/0005 P13)")
    if restore and user_id is not None:
        raise ValueError(
            "restore and user_id are mutually exclusive — a restore is this "
            "store's own history and never remaps (specs/0005 P5)")
    path = Path(path)
    with path.open() as f:
        lines = [ln for ln in (l.strip() for l in f) if ln]
    if not lines:
        raise ValueError(f"{path}: empty file")
    header = json.loads(lines[0])
    if header.get("kind") != "veracium-export":
        raise ValueError(f"{path}: not a Veracium export (missing header)")
    src_version = header.get("version", 0)
    if src_version > FORMAT_VERSION:
        raise ValueError(f"{path}: export version {src_version} is newer "
                         f"than this Veracium understands ({FORMAT_VERSION})")
    target_uid = user_id or header.get("user_id")

    # (1) parse every record
    edge_recs: list = []
    ep_recs: list = []
    for ln in lines[1:]:
        rec = json.loads(ln)
        marker = rec.pop("record", None)
        if marker is None and rec.get("kind") in ("edge", "episode"):
            marker = rec.pop("kind")   # format v1: the record marker was named "kind"
        if marker not in ("edge", "episode"):
            raise ValueError(f"{path}: unknown record kind {marker!r}")
        rec["user_id"] = target_uid
        (edge_recs if marker == "edge" else ep_recs).append(rec)

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
        elif prov.get("origin") is None:
            raise ValueError(
                f"{path}: v{src_version} record {rec.get('id')!r} carries provenance with "
                f"no origin — a current-format import MUST carry origin; a missing one is "
                f"malformed and is NEVER resolved to this store (specs/0006 I14)")
        elif prov["origin"] == dest_origin:
            # A LOCAL record coming home (its materialised origin IS this store's singleton):
            # canonicalise back to absent so it resolves to us and stores byte-identically to
            # the original local row — that is what makes an export→re-import idempotent and
            # groups the two as ONE source (I9). A genuinely FOREIGN origin is left untouched
            # (I2b) — trust of it is 0005's import boundary, applied first (I7).
            prov["origin"] = None

    # (3) legacy-format outcome conversion (§4f-ii) OR v3 explicit-field check (H13).
    # Pinned to the OUTCOME-field format version (3, specs/0009), NOT FORMAT_VERSION: the
    # 0006 v3→v4 bump introduced source-identity fields, not outcome fields, so v3 AND v4
    # both carry explicit outcome fields and must take the H13 branch. Keying this on
    # FORMAT_VERSION would wrongly legacy-convert a v3 export after the bump.
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
                raise ValueError(
                    f"{path}: legacy import holds {len(members)} outcome records for "
                    f"chain {gk} — refuse rather than branch (specs/0009 §4f-ii)")
        for r in outcome_recs:   # the same honest conversion as the on-disk migration
            r["seq"] = 1
            r["supersedes_episode"] = None
            r["judgment_time_known"] = False
    else:
        for r in outcome_recs:   # a v3 outcome record MUST be explicit (H13)
            jtk = r.get("judgment_time_known")
            if jtk is None:
                raise ValueError(
                    f"{path}: v3 outcome record {r.get('id')!r} omits "
                    f"judgment_time_known — refuse (specs/0009 H13)")
            # state-space rule (§ Episode fields, round-5 Correction B): a
            # False label is a LEGACY-ROOT-ONLY state — never a non-root.
            if jtk is False and (r.get("seq") != 1
                                 or r.get("supersedes_episode") is not None):
                raise ValueError(
                    f"{path}: v3 outcome record {r.get('id')!r} has "
                    f"judgment_time_known=False but is not a root (seq="
                    f"{r.get('seq')!r}, supersedes_episode="
                    f"{r.get('supersedes_episode')!r}) — refuse (specs/0009)")

    # (3b) specs/0010 X18/X19: consolidation shapes cross the boundary honestly.
    for r in ep_recs:
        if r.get("claimed_by") is not None:
            raise ValueError(
                f"{path}: episode {r.get('id')!r} is a CLAIMED input whose "
                f"consolidation op is non-portable — refuse rather than orphan it "
                f"(specs/0010 X18)")
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
            raise ValueError(
                f"{path}: episode {r.get('id')!r} carries an explicit null "
                f"consolidation_output_index — the exporter omits None, so an "
                f"explicit null is malformed (specs/0014 §4c R7-3)")
        if idx is not None and (isinstance(idx, bool)
                                or not isinstance(idx, int) or idx < 0):
            raise ValueError(
                f"{path}: episode {r.get('id')!r} consolidation_output_index "
                f"{idx!r} is not a non-negative integer (specs/0014 §2c)")
        if idx is not None and not r.get("lineage"):
            raise ValueError(
                f"{path}: episode {r.get('id')!r} carries a consolidation_output_"
                f"index but no lineage — store-assigned identity cannot be "
                f"fabricated on a plain episode (specs/0014 §4c)")
        if r.get("lineage"):                      # a consolidation OUTPUT
            lin = r["lineage"]
            if not (isinstance(lin, list)
                    and all(isinstance(x, str) and is_historical_id(x) for x in lin)):
                raise ValueError(
                    f"{path}: episode {r.get('id')!r} has a malformed lineage shape — "
                    f"every lineage id must be historical (specs/0010 X18)")
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
            raise ValueError(
                f"{path}: two lineage-bearing outputs claim the same "
                f"(origin, operation_id, index) {k!r} within one import — "
                f"partial history explains gaps, never duplicates "
                f"(specs/0014 §2c R8-3)")
        seen_keys[k] = r
    skip_ids = set()
    if incoming_indexed:
        dest_uid = user_id if user_id is not None else header.get("user_id")
        dest_by_key = {}
        for dep in store.episodes(dest_uid):
            if dep.lineage and dep.consolidation_output_index is not None:
                drec = json.loads(dep.model_dump_json())
                dest_by_key[_out_key(drec)] = drec
        for r in incoming_indexed:
            hit = dest_by_key.get(_out_key(r))
            if hit is None:
                continue
            if (source_identity_projection(r)
                    == source_identity_projection(hit)):
                skip_ids.add(r["id"])              # idempotent re-import: no-op
            else:
                raise ValueError(
                    f"{path}: incoming output {r.get('id')!r} claims the "
                    f"existing identity {_out_key(r)!r} with a DIFFERENT "
                    f"source-identity projection — rejected "
                    f"(specs/0014 §2c R9-5/R11-3)")
    if skip_ids:
        ep_recs = [r for r in ep_recs if r["id"] not in skip_ids]

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
    for _attempt in range(_IMPORT_RETRIES):
        outcome = _preflight_and_commit(store, path, target_uid, edges, eps,
                                        incoming_chains, capped_path=not restore)
        if outcome is not DESTINATION_CHANGED:
            return {**outcome, "capped": capped_count, "user_id": target_uid}
    raise ValueError(f"{path}: import kept losing a race against concurrent writes "
                     f"after {_IMPORT_RETRIES} attempts — refused (specs/0009 §4c)")


def _preflight_and_commit(store, path, target_uid, edges, eps, incoming_chains,
                          *, capped_path: bool = True):
    """One preflight-then-commit pass: validate the COMBINED destination graph
    against the live store, build the plan + the full destination-state assumptions,
    and commit atomically. Returns the store's result (counts dict or
    `DESTINATION_CHANGED`). specs/0009 §4c.

    `capped_path` (specs/0005 §4d): on the default (capping) import path the
    record-equality refusals append the pinned `--restore` warning, because
    the commonest trigger is an own-store re-import whose stored originals
    differ from the capped incoming form (P10); the warning is never a bare
    remedy (P15). Restore-path refusals keep the plain message."""
    _tail = f". {_RESTORE_WARNING}" if capped_path else ""
    existing_edges = {e.id: e for e in store.edges(
        target_uid, active_only=False, include_quarantined=True)}
    existing_eps = {ep.id: ep for ep in store.episodes(target_uid)}
    importing_edge_ids = {e.id for e in edges}

    plan_edges: list = []
    plan_eps: list = []
    skipped = 0
    edge_ids_expected: dict = {}     # id -> expected-present
    ep_records_expected: dict = {}   # id -> current-persisted-json (None if absent)
    chain_heads_expected: dict = {}  # (edge_id, evidence_ref) -> head id or None

    # edges: record-equal existing → idempotent skip; differing → refuse; new → insert
    for edge in edges:
        prior = existing_edges.get(edge.id)
        if prior is not None:
            if prior.model_dump() != edge.model_dump():
                raise ValueError(f"{path}: edge {edge.id!r} already exists with "
                                 f"different content — refuse (specs/0009 §4c){_tail}")
            skipped += 1
            edge_ids_expected[edge.id] = True
        else:
            plan_edges.append(edge)
            edge_ids_expected[edge.id] = False

    # every outcome chain's edge_id must resolve to an Edge owned by the target user
    for (edge_id, _evref) in incoming_chains:
        if edge_id not in importing_edge_ids and edge_id not in existing_edges:
            raise ValueError(f"{path}: outcome chain references edge {edge_id!r}, "
                             f"which is missing or foreign to {target_uid!r} — refuse "
                             f"(specs/0009 §4c)")
        edge_ids_expected.setdefault(edge_id, edge_id in existing_edges)

    # non-outcome episodes: same record-equality idempotency as edges
    for ep in eps:
        if ep.kind == "outcome":
            continue
        prior = existing_eps.get(ep.id)
        ep_records_expected[ep.id] = None if prior is None else prior.model_dump_json()
        if prior is not None:
            if prior.model_dump() != ep.model_dump():
                raise ValueError(f"{path}: episode {ep.id!r} already exists with "
                                 f"different content — refuse (specs/0009 §4c){_tail}")
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
                    raise ValueError(
                        f"{path}: outcome link {m.id!r} already exists with different "
                        f"content — refuse the whole import (specs/0009 §4c){_tail}")
                skipped += 1
            else:
                new_members.append(m)
        if new_members:
            first_new = new_members[0]
            if first_new.supersedes_episode != (dest_head.id if dest_head else None):
                raise ValueError(
                    f"{path}: outcome chain {key} does not extend the destination head "
                    f"{(dest_head.id if dest_head else None)!r} (would branch or "
                    f"diverge) — refuse (specs/0009 §4c)")
            plan_eps.extend(new_members)

    plan = {"edges": plan_edges, "episodes": plan_eps}
    expected = {"edge_ids": edge_ids_expected,
                "episode_records": ep_records_expected,
                "chain_heads": chain_heads_expected}
    result = store.commit_outcome_import_plan(target_uid, plan, expected)
    if result is DESTINATION_CHANGED:
        return DESTINATION_CHANGED
    return {"edges": result["edges"],
            "episodes": result["episodes"], "skipped": skipped}
