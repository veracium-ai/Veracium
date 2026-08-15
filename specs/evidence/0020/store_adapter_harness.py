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
(3) export→import of a survivor — the ledger does not travel; the
import-time NOTE-RECONSTRUCTION rule rebuilds the absorption rows and the
cross-identity survivor ASSERTS UNRESOLVED on the destination (round-5
F1's executable carrier); (4) a host record with no rows → own
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
        # ROUND-5 F1: the import-time RECONSTRUCTION rule is now the
        # executable carrier — rebuild absorption rows from the imported
        # records' absorbed_by notes and ASSERT the cross-identity
        # survivor fails closed on the destination.
        from reference_scope import reconstruct_absorption_rows
        imported = [{"id": e.id, "origin": e.provenance.origin,
                     "source_id": e.provenance.source_id,
                     "invalidation_reason": e.invalidation_reason,
                     "note": e.note}
                    for e in dest.edges("u1", active_only=False)]
        rebuilt = reconstruct_absorption_rows(imported, dlocal)
        rrows = rebuilt.get("e-a", [])
        assert rrows, "reconstruction produced no rows for the survivor"
        dgot = membership(_record_shape(dsurv), rrows, "none", dlocal)
        assert dgot == UNRESOLVED, (
            f"imported cross-identity absorption survivor must be "
            f"UNRESOLVED via reconstruction, got {dgot!r}")
        checks.append("imported absorption survivor -> UNRESOLVED via "
                      f"note-reconstruction ({len(rrows)} rebuilt row(s)); "
                      "import_memory writing REAL rows is the named "
                      "implementation obligation")
        dest.close()

        # (3b) THE FULL IMPORT MATRIX (round-6 F1 — driving ACTUAL
        # import_memory: remap, whitespace ids, missing tag, unresolvable
        # tag; the reference's refusal semantics asserted on each)
        from reference_scope import (reconstruct_absorption_rows as _rec,
                                     ImportLinkageError)
        # (3b-i) supported user_id remap: ids change, notes do not —
        # the id_remap parameter translates (content-matched here; the
        # importer's own table is the implementation carrier)
        dest2 = SqliteStore(f"{d}/dest2.db")
        portability.import_memory(dest2, exp, user_id="u2")
        imp2 = [{"id": e.id, "origin": e.provenance.origin,
                 "source_id": e.provenance.source_id,
                 "invalidation_reason": e.invalidation_reason,
                 "note": e.note, "object": e.object}
                for e in dest2.edges("u2", active_only=False)]
        by_obj = {e["object"]: e["id"] for e in imp2}
        remap = {"e-a": by_obj.get("cat Miso"), "e-b": by_obj.get("Miso"),
                 "e-w2": by_obj.get("dog Rex"), "e-p2": by_obj.get("Rex")}
        # (the refusal rule caught this map when it was incomplete — an
        # unresolvable winner refused the whole reconstruction, which is
        # exactly the fail-closed behaviour under test)
        rebuilt2 = _rec(imp2, dest2.local_origin(), id_remap=remap)
        new_surv = remap["e-a"]
        assert new_surv in rebuilt2 and rebuilt2[new_surv], \
            "remap-aware reconstruction missed the survivor"
        checks.append("REMAPPED import: reconstruction keys to post-remap "
                      f"ids via id_remap ({new_surv})")
        dest2.close()
        # (3b-ii) whitespace id in a note: the anchored grammar parses to
        # the '(restated as' anchor, and an id containing spaces resolves
        ws = [{"id": "winner id", "invalidation_reason": None, "note": "",
               "origin": None, "source_id": None},
              {"id": "prior-1", "invalidation_reason": "absorbed_duplicate",
               "note": "absorbed_by:winner id (restated as 'x')",
               "origin": "org-b", "source_id": "agent-9"}]
        rws = _rec(ws, "L")
        assert "winner id" in rws, "whitespace id not parsed to the anchor"
        checks.append("whitespace winner id parsed via the anchored grammar")
        # (3b-iii) missing tag -> REFUSE; unresolvable tag -> REFUSE
        for bad, why in (
            ([{"id": "s", "invalidation_reason": "absorbed_duplicate",
               "note": "retired", "origin": None, "source_id": None}],
             "missing tag"),
            ([{"id": "s", "invalidation_reason": "absorbed_duplicate",
               "note": "absorbed_by:ghost-id", "origin": None,
               "source_id": None}], "unresolvable tag"),
        ):
            try:
                _rec(bad, "L")
                raise AssertionError(f"{why} did not refuse")
            except ImportLinkageError:
                pass
        checks.append("missing/unresolvable linkage -> whole-import REFUSAL")

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
    results = run()                      # once (round-5 F4's note)
    for line in results:
        print("PASS", line)
    print(f"store adapter harness: {len(results)} regression groups pass "
          f"against the SHIPPED store")
