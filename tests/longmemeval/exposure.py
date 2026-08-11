"""G1 — the exposure ledger, automated.

Which items have left the confirmatory set, as a durable append-only record
instead of a hard-coded union in whichever script last remembered to update
it. The v1 failure this replaces: draw_r2 checked the pilot ONLY and reported
"30 newly exposed" while the variance protocol had already burned one of the
items — incomplete enumeration, in the exposure dimension.

Rules (from the G1 queue row):
  * confirmatory membership is SNAPSHOTTED BEFORE execution — the snapshot is
    what a threshold may be approved against, so it must precede the run that
    spends items;
  * machine inspection (a script read the answers) and human inspection (a
    person did) are RECORDED SEPARATELY — they burn confirmatory standing
    differently and must never be merged into one bit.

The ledger is JSONL beside this module, committed. One event per line:
  {"ts": ..., "kind": "machine"|"human", "source": ..., "items": [...],
   "backfilled": bool}
"""

from __future__ import annotations

import json
import time
from pathlib import Path

LEDGER = Path(__file__).parent / "exposure_ledger.jsonl"
KINDS = ("machine", "human")


def _events() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(line) for line in LEDGER.read_text().splitlines() if line.strip()]


def record_exposure(item_ids, *, kind: str, source: str,
                    backfilled: bool = False) -> dict:
    """Append one exposure event. `source` names the protocol/run that spent
    the items (e.g. "stratified_pilot", "draw_r2 seed=7"). Returns the event."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
    ev = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "kind": kind, "source": source,
          "items": sorted(set(map(str, item_ids))), "backfilled": backfilled}
    with LEDGER.open("a") as f:
        f.write(json.dumps(ev, sort_keys=True) + "\n")
    return ev


def exposed_ids(kind: str | None = None) -> set[str]:
    """Every item any recorded event has exposed; optionally one kind only."""
    out: set[str] = set()
    for ev in _events():
        if kind is None or ev["kind"] == kind:
            out.update(ev["items"])
    return out


def confirmatory_snapshot(all_ids) -> dict:
    """Membership BEFORE an execution: call this — and persist/print its
    result — before the run that will spend items, never after. The hash is
    over the sorted confirmatory ids, so an approval can pin exactly the set
    it was granted against."""
    import hashlib
    exposed = exposed_ids()
    confirmatory = sorted(set(map(str, all_ids)) - exposed)
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "exposed": len(exposed), "confirmatory": confirmatory,
            "confirmatory_hash": hashlib.sha256(
                "\n".join(confirmatory).encode()).hexdigest(),
            "by_kind": {k: len(exposed_ids(k)) for k in KINDS}}


def ensure_seeded(items, evals) -> bool:
    """One-time backfill of the two historical exposure events the hard-coded
    union carried (pilot, variance). Recorded as machine exposure with
    backfilled=True so ledger history is honest about its provenance. Returns
    True if it wrote."""
    if LEDGER.exists() and _events():
        return False
    from draw_r2 import stratified_pilot, variance_subset
    record_exposure((i.question_id for i in stratified_pilot(items, evals)),
                    kind="machine", source="stratified_pilot (backfill)",
                    backfilled=True)
    record_exposure((i.question_id for i in variance_subset(items, evals)),
                    kind="machine", source="variance_subset (backfill)",
                    backfilled=True)
    return True
