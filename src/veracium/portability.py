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

Trust note: provenance in an export file is *data*. Importing a file grants its
records whatever authorship and disclosure they claim — import only from
sources you trust exactly as much as the database file itself.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from .schema import Edge, Episode
from .store.base import DESTINATION_CHANGED

FORMAT_VERSION = 3
_IMPORT_RETRIES = 8   # bounded whole-import retries before refusing a persistent race


def export_memory(store, user_id: str, path) -> dict:
    """Write `user_id`'s complete memory (all edges incl. superseded and
    quarantined, all episodes) to `path` as JSONL. Returns counts."""
    edges = store.edges(user_id, active_only=False, include_quarantined=True)
    episodes = store.episodes(user_id)
    path = Path(path)
    with path.open("w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": FORMAT_VERSION,
                            "user_id": user_id,
                            "exported_at": datetime.now(timezone.utc).isoformat()})
                + "\n")
        for e in edges:
            f.write(json.dumps({"record": "edge", **json.loads(e.model_dump_json())})
                    + "\n")
        for ep in episodes:
            f.write(json.dumps({"record": "episode", **json.loads(ep.model_dump_json())})
                    + "\n")
    return {"edges": len(edges), "episodes": len(episodes), "path": str(path)}


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


def import_memory(store, path, *, user_id: Optional[str] = None) -> dict:
    """Load a Veracium export into `store`. Idempotent (an existing, record-equal
    record is skipped); `user_id` remaps every record into that user.

    specs/0009 §4c: the WHOLE file is parsed, cross-user remapped, legacy-converted
    (§4f-ii) and topology-validated BEFORE any persistent write, then committed as
    one atomic plan via `commit_outcome_import_plan` — so a valid chain A is never
    left persisted when a later chain B refuses, and the commit linearizes against
    concurrent `append_outcome_if_head` (no branch, no partial import). Returns counts."""
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

    # (3) legacy-format outcome conversion (§4f-ii) OR v3 explicit-field check (H13).
    outcome_recs = [r for r in ep_recs if r.get("kind") == "outcome"]
    if src_version < FORMAT_VERSION:
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
                                        incoming_chains)
        if outcome is not DESTINATION_CHANGED:
            return {**outcome, "user_id": target_uid}
    raise ValueError(f"{path}: import kept losing a race against concurrent writes "
                     f"after {_IMPORT_RETRIES} attempts — refused (specs/0009 §4c)")


def _preflight_and_commit(store, path, target_uid, edges, eps, incoming_chains):
    """One preflight-then-commit pass: validate the COMBINED destination graph
    against the live store, build the plan + the full destination-state assumptions,
    and commit atomically. Returns the store's result (counts dict or
    `DESTINATION_CHANGED`). specs/0009 §4c."""
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
                                 f"different content — refuse (specs/0009 §4c)")
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
                                 f"different content — refuse (specs/0009 §4c)")
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
                        f"content — refuse the whole import (specs/0009 §4c)")
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
