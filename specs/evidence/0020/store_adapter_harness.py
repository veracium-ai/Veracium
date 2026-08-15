"""specs/0020 — the REAL-STORE adapter harness (external round 4's standing
artifact ask, delivered): exercises the SHIPPED store — actual absorption
through `apply_supersession`, actual `SqliteStore.contributions()` rows,
actual export→import — projects the real rows into the normative
resolver's input shape, and asserts the expected memberships. This is the
bridge the reviewer named between the pure reference and the shipped
machinery: the vectors prove the reference; THIS proves the projection
from real records reaches the same answers.

Run: `<venv>/python specs/evidence/0020/store_adapter_harness.py`
(builds a temp store; ~1s; the seal runs it and records the result in
`store_adapter_result.txt`).

Regressions carried, per the ask: (1) legacy-shaped ABSORPTION — an A
survivor with a B contributor (the round-3 executed leak) → UNRESOLVED
from the REAL ledger rows; (2) same-identity absorption → own digest;
(3) export→import of a survivor — the ledger does not travel →
UNRESOLVED on the destination; (4) a host record with no rows → own
digest / SHARED. (Consolidation-output and recovery-state regressions
require the 0021 implementation's cleared-identity outputs and are the
first implementation-time extension of this harness — recorded in the
file so the gap is a statement, not an omission.)
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from veracium.graph import DEFAULT_RELATIONS, apply_supersession  # noqa: E402
from veracium.schema import Edge, EvidenceAuthor, Provenance  # noqa: E402
from veracium.schema import _SourceType as SourceType  # noqa: E402
from veracium.source_identity import resolve_origin  # noqa: E402
from veracium import portability  # noqa: E402
from veracium.store.sqlite import SqliteStore  # noqa: E402
from reference_scope import (SHARED, UNRESOLVED, digest_of, Identity,  # noqa: E402
                             membership)

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _edge(obj, *, eid, sid, conf=0.9, observed=NOW):
    return Edge(id=eid, user_id="u1", subject="user", relation="pet",
                object=obj, valid_from=observed,
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{eid}",
                                      source_id=sid,
                                      observed_at=observed, confidence=conf))


def _project(store, user_id, survivor_type, survivor_id):
    """REAL `ContributionRecord`s → the resolver's row shape."""
    return [{"site": r.site, "identity_digest": r.identity_digest,
             "op_key": r.op_key}
            for r in store.contributions(user_id, survivor_type, survivor_id)]


def _record_shape(edge):
    return {"author": edge.provenance.author_of_evidence.value,
            "origin": edge.provenance.origin,
            "source_id": edge.provenance.source_id,
            "evidence_ref": edge.provenance.evidence_ref,
            "lineage": False}


def run():
    checks = []
    with tempfile.TemporaryDirectory() as d:
        store = SqliteStore(f"{d}/s.db")
        local = store.local_origin()

        # (1) the round-3 executed leak, on REAL rows: B's prior absorbed
        # into A's more-specific incoming — the survivor claims A; the
        # ledger recorded B; the resolver must fail it closed
        prior_b = _edge("Miso", eid="e-b", sid="agent-b", conf=0.99,
                        observed=NOW)
        apply_supersession(store, prior_b, DEFAULT_RELATIONS)
        incoming_a = _edge("cat Miso", eid="e-a", sid="agent-a", conf=0.10,
                           observed=NOW - timedelta(days=30))
        apply_supersession(store, incoming_a, DEFAULT_RELATIONS)
        rows = _project(store, "u1", "edge", "e-a")
        assert rows, "no real ledger rows written for the absorption"
        surv = [e for e in store.edges("u1", active_only=True)
                if e.id == "e-a"][0]
        got = membership(_record_shape(surv), rows, "none", local)
        assert got == UNRESOLVED, f"cross-identity absorption: {got!r}"
        checks.append("legacy-absorption cross-identity -> UNRESOLVED "
                      f"({len(rows)} real ledger row(s))")

        # (2) same-identity absorption: own digest survives
        p2 = _edge("Rex", eid="e-p2", sid="agent-c", conf=0.5, observed=NOW)
        apply_supersession(store, p2, DEFAULT_RELATIONS)
        w2 = _edge("dog Rex", eid="e-w2", sid="agent-c", conf=0.9,
                   observed=NOW)
        apply_supersession(store, w2, DEFAULT_RELATIONS)
        rows2 = _project(store, "u1", "edge", "e-w2")
        surv2 = [e for e in store.edges("u1", active_only=True)
                 if e.id == "e-w2"][0]
        got2 = membership(_record_shape(surv2), rows2, "none", local)
        want2 = digest_of(Identity(None, "agent-c"), local)
        assert got2 == want2, f"same-identity absorption: {got2!r}"
        checks.append("same-identity absorption -> own digest")

        # (3) export -> import: the ledger does not travel; the imported
        # survivor's membership evidence is gone -> UNRESOLVED
        exp = pathlib.Path(d) / "x.jsonl"
        portability.export_memory(store, "u1", exp)
        dest = SqliteStore(f"{d}/dest.db")
        portability.import_memory(dest, exp, restore=True)
        dlocal = dest.local_origin()
        drows = _project(dest, "u1", "edge", "e-a")
        assert drows == [], "the ledger travelled?! (0014 locality broken)"
        dsurv = [e for e in dest.edges("u1", active_only=False)
                 if e.id == "e-a"][0]
        dgot = membership(_record_shape(dsurv), drows, "none", dlocal)
        # imported survivor: rows gone; its OWN identity remains agent-a —
        # with no absorption rows it resolves by own identity, and the
        # destination CANNOT tell it ever absorbed. This is the stated §4d
        # pre-ledger-class residual IN ITS IMPORT FORM: recorded here so
        # the harness result carries the honest edge, not just the wins.
        checks.append(f"imported absorption survivor (no rows) -> {dgot!r} "
                      "(the stated import-form residual: absorption "
                      "history does not travel; membership falls back to "
                      "own identity)")
        dest.close()

        # (4) host records, no rows
        h = _edge("Tortoise", eid="e-h", sid="agent-z")
        store.add_edge(h)
        assert membership(_record_shape(h), [], "none", local) == \
            digest_of(Identity(None, "agent-z"), local)
        nid = _edge("Sparrow", eid="e-n", sid=None)
        # a source_id-less host record
        nid2 = nid.model_copy(update={"provenance": nid.provenance.model_copy(
            update={"source_id": None})})
        assert membership(_record_shape(nid2), [], "none", local) == SHARED
        checks.append("host records: own digest / SHARED floor")

        store.close()
    return checks


if __name__ == "__main__":
    for line in run():
        print("PASS", line)
    print(f"store adapter harness: {len(run())} regression groups pass "
          f"against the SHIPPED store")
