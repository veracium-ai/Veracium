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

from .schema import Edge, Episode

FORMAT_VERSION = 2


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


def import_memory(store, path, *, user_id: Optional[str] = None) -> dict:
    """Load a Veracium export into `store`. Idempotent (existing ids are
    skipped); `user_id` remaps every record into that user. Returns counts."""
    path = Path(path)
    with path.open() as f:
        lines = [ln for ln in (l.strip() for l in f) if ln]
    if not lines:
        raise ValueError(f"{path}: empty file")
    header = json.loads(lines[0])
    if header.get("kind") != "veracium-export":
        raise ValueError(f"{path}: not a Veracium export (missing header)")
    if header.get("version", 0) > FORMAT_VERSION:
        raise ValueError(f"{path}: export version {header['version']} is newer "
                         f"than this Veracium understands ({FORMAT_VERSION})")

    target_uid = user_id or header.get("user_id")
    existing_edges = {e.id for e in store.edges(target_uid, active_only=False,
                                                include_quarantined=True)}
    existing_eps = {ep.id for ep in store.episodes(target_uid)}

    imported = {"edges": 0, "episodes": 0}
    skipped = 0
    for ln in lines[1:]:
        rec = json.loads(ln)
        kind = rec.pop("record", None)
        if kind is None and rec.get("kind") in ("edge", "episode"):
            kind = rec.pop("kind")   # format v1: the marker was named "kind"
        rec["user_id"] = target_uid
        if kind == "edge":
            edge = Edge.model_validate(rec)
            if edge.id in existing_edges:
                skipped += 1
                continue
            store.add_edge(edge)
            imported["edges"] += 1
        elif kind == "episode":
            ep = Episode.model_validate(rec)
            if ep.id in existing_eps:
                skipped += 1
                continue
            store.add_episode(ep)
            imported["episodes"] += 1
        else:
            raise ValueError(f"{path}: unknown record kind {kind!r}")
    return {**imported, "skipped": skipped, "user_id": target_uid}
