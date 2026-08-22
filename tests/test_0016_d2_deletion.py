"""specs/0016 D2 — the source_type deletion: the receipt era boundary (v4,
on-sight refusal proven by exploding sentinels at BOTH phases over every
legal pre-D2 stored version), the defined digest collapse, and FORMAT 7 (the
source_type-less file; ≤6 keys dropped on import; too-new refused).

The removal of the public surface itself (names gone, model field gone, the
star-import pin at 41) is tested in test_0016_d1_deprecation.py — the D1
matrix resolved by deletion."""
import json
import uuid
from datetime import datetime, timezone

import pytest

from veracium import contribution as C
from veracium.graph import (DEFAULT_RELATIONS, _build_supersession_plan,
                            apply_supersession)
from veracium.portability import FORMAT_VERSION, export_memory, import_memory
from veracium.schema import Edge, Episode, EvidenceAuthor, Provenance
from veracium.store.base import (ReceiptSchemaBoundaryError,
                                 SupersessionIntegrityError)
from veracium.store.sqlite import SqliteStore

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)
RESP = '{"inserted_incoming":true,"invalidated":0,"refused":0}'

# every LEGAL pre-D2 stored receipt state (0014 R10-4 shapes over the pre-D2
# versions {1,2,3} — the 0019 rider's closed set at 0019's release)
PRE_D2_STATES = [
    (None, 1, None),          # migrated legacy
    (None, 2, RESP),          # 0014-era, snapshot-less
    ("d" * 64, 2, RESP),      # 0014-era, with snapshot
    (None, 3, RESP),          # 0019-era, snapshot-less
    ("d" * 64, 3, RESP),      # 0019-era, with snapshot
]


def _edge(obj="Miso", *, eid=None, conf=0.9, ref="ev-1"):
    return Edge(
        id=eid or f"e-{uuid.uuid4().hex[:8]}", user_id="u1", subject="user",
        relation="pet", object=obj, valid_from=NOW,
        provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                              evidence_ref=ref, observed_at=NOW,
                              confidence=conf))


def _store(tmp_path, name="s.db"):
    return SqliteStore(str(tmp_path / name))


def _insert_receipt(store, op_id, rd, ver, resp, *, uid="u1"):
    store._conn.execute(
        "INSERT INTO supersession_operations(user_id,operation_id,"
        "logical_request_digest,status,request_digest,response,"
        "outcome_digest_version) VALUES(?,?,?,?,?,?,?)",
        (uid, op_id, "stored-pre-d2-outcome-digest", "applied", rd, resp, ver))
    store._conn.commit()


def _arm_sentinels(monkeypatch):
    """Replace EVERY digest construction a receipt comparison could invoke
    with an exploding sentinel — if the boundary refusal is truly ON SIGHT,
    none of them runs (I5 / rider A2)."""
    def boom(*a, **k):
        raise AssertionError(
            "a digest was computed for a pre-D2 receipt — the era boundary "
            "must refuse ON SIGHT (specs/0016 D2, 0019 rider A2)")
    monkeypatch.setattr(C, "request_digest", boom)
    monkeypatch.setattr(SqliteStore, "_outcome_digest_v2", boom)
    monkeypatch.setattr(SqliteStore, "_logical_request_digest",
                        staticmethod(boom))


# -- the era boundary: on-sight refusal at BOTH phases ------------------------

@pytest.mark.parametrize("rd,ver,resp", PRE_D2_STATES)
def test_pre_d2_receipt_refuses_on_sight_phase_1(tmp_path, monkeypatch, rd,
                                                 ver, resp):
    """Phase 1 (the public pre-plan lookup in graph.py): a stored version < 4
    refuses UNCONDITIONALLY — the exploding sentinels prove no digest is
    computed and no comparison branch runs."""
    store = _store(tmp_path)
    edge = _edge(eid="e-boundary")
    _insert_receipt(store, f"sup-{edge.id}", rd, ver, resp)
    _arm_sentinels(monkeypatch)
    with pytest.raises(ReceiptSchemaBoundaryError):
        apply_supersession(store, edge, DEFAULT_RELATIONS)
    # fail-closed: nothing was applied
    assert not [e for e in store.edges("u1", active_only=True)
                if e.id == edge.id]
    store.close()


@pytest.mark.parametrize("rd,ver,resp", PRE_D2_STATES)
def test_pre_d2_receipt_refuses_on_sight_phase_2(tmp_path, monkeypatch, rd,
                                                 ver, resp):
    """Phase 2 (the store-side verify in apply_supersession_plan): same rule,
    same sentinels — the era gate precedes snapshot verification and every
    digest derivation, the plan's own request digest included."""
    store = _store(tmp_path)
    edge = _edge(eid="e-boundary2")
    plan, _ = _build_supersession_plan(store, edge, DEFAULT_RELATIONS,
                                       "op-boundary2")
    plan.raw_request = C.raw_request_snapshot(edge)
    _insert_receipt(store, "op-boundary2", rd, ver, resp)
    _arm_sentinels(monkeypatch)
    with pytest.raises(ReceiptSchemaBoundaryError):
        store.apply_supersession_plan(plan)
    assert not [e for e in store.edges("u1", active_only=True)
                if e.id == edge.id]
    store.close()


def test_boundary_error_is_a_conservative_integrity_subclass(tmp_path):
    """R2-3 re-ruled: the boundary error SUBCLASSES SupersessionIntegrityError
    (existing handlers keep catching it), carries the era context, and never
    says benign."""
    assert issubclass(ReceiptSchemaBoundaryError, SupersessionIntegrityError)
    store = _store(tmp_path)
    edge = _edge(eid="e-msg")
    _insert_receipt(store, f"sup-{edge.id}", None, 2, RESP)
    with pytest.raises(SupersessionIntegrityError) as exc:   # the parent catches
        apply_supersession(store, edge, DEFAULT_RELATIONS)
    msg = str(exc.value)
    assert "benign" not in msg.lower()
    assert "outcome_digest_version 2" in msg
    assert "source_type" in msg
    store.close()


# -- version-4 receipts follow the ordinary 0014 contract ---------------------

def test_v4_receipts_follow_the_ordinary_contract(tmp_path):
    """The other half of the one contract: a version-4 receipt replays an
    identical retry, and a genuinely different request reusing the op id is
    the LOUDER plain integrity conflict — never the boundary error."""
    store = _store(tmp_path)
    edge = _edge(eid="e-v4")
    apply_supersession(store, edge, DEFAULT_RELATIONS)
    r = store.supersession_receipt("u1", "sup-e-v4")
    assert r["outcome_digest_version"] == 4
    # identical retry → replay, no raise, no double-apply
    apply_supersession(store, edge, DEFAULT_RELATIONS)
    assert len([e for e in store.edges("u1", active_only=True)
                if e.id == "e-v4"]) == 1
    # different request, same op id → plain integrity conflict
    other = _edge(obj="COMPLETELY different", eid="e-v4", conf=0.2)
    with pytest.raises(SupersessionIntegrityError) as exc:
        apply_supersession(store, other, DEFAULT_RELATIONS)
    assert not isinstance(exc.value, ReceiptSchemaBoundaryError)
    store.close()


# -- the digest collapse (the defined API-break consequence) ------------------

def test_snapshot_excludes_the_deleted_field_and_is_stable():
    """The NEW construction: the raw-request snapshot is the COMPLETE model
    dump — which no longer contains source_type at any depth — and its digest
    is pinned (recorded expectation; drift fails loudly here)."""
    e = _edge(eid="e-collapse-vector", obj="cat", conf=0.5)
    snap = C.raw_request_snapshot(e)
    assert "source_type" not in snap["provenance"]
    assert "source_type" not in json.dumps(snap)
    assert C.request_digest(snap) == \
        "5a56c9953994a8195ea754441b6612ba7b5b4131d4f7084b2600bcb8389207f1"


def test_source_type_only_differences_stop_conflicting():
    """I7, the post-D2 direction: two submissions that (historically) differed
    ONLY in source_type ARE the same request — identical snapshots, identical
    digests. The pre-D2 direction is the boundary rule above."""
    base = {"id": "e-same", "user_id": "u1", "subject": "user",
            "relation": "pet", "object": "Miso",
            "valid_from": NOW.isoformat(),
            "provenance": {"author_of_evidence": "user", "evidence_ref": "ev",
                           "observed_at": NOW.isoformat()}}
    a = json.loads(json.dumps(base))
    b = json.loads(json.dumps(base))
    a["provenance"]["source_type"] = "stated"     # dropped at validation
    b["provenance"]["source_type"] = "inferred"   # dropped at validation
    ea, eb = Edge.model_validate(a), Edge.model_validate(b)
    sa, sb = C.raw_request_snapshot(ea), C.raw_request_snapshot(eb)
    assert sa == sb
    assert C.request_digest(sa) == C.request_digest(sb)


def test_partition_lost_the_field_and_stays_total():
    """The 0014 amendment, mechanically: EXACT_EQUAL_PROV_FIELDS excludes the
    deleted field and the partition still covers Provenance exactly."""
    assert "source_type" not in C.EXACT_EQUAL_PROV_FIELDS
    prov_classes = [set(C.EXACT_EQUAL_PROV_FIELDS),
                    set(C.RECOMPUTED_PROV_FIELDS)]
    assert set().union(*prov_classes) == set(Provenance.model_fields)
    assert sum(len(c) for c in prov_classes) == len(Provenance.model_fields)


def test_arbitrary_stored_source_type_dropped_post_d2(tmp_path):
    """§2c row 5: a stored row whose JSON carries ANY source_type value (a
    valid historical enum value or a crafted string — reachable only via
    hand-edit/bypass) is dropped on read like the historical key."""
    store = _store(tmp_path)
    e = _edge(eid="e-crafted")
    d = json.loads(e.model_dump_json())
    d["provenance"]["source_type"] = "totally-crafted-value"
    store._conn.execute(
        "INSERT INTO edges(id,user_id,subject,relation,object,active,"
        "quarantined,json) VALUES(?,?,?,?,?,1,0,?)",
        (e.id, "u1", "user", "pet", "Miso", json.dumps(d)))
    store._conn.commit()
    got = [x for x in store.edges("u1", active_only=True) if x.id == "e-crafted"]
    assert len(got) == 1
    assert "source_type" not in got[0].provenance.model_dump()
    store.close()


# -- the export format (0016's deleted-key property) --------------------------

def test_export_omits_the_deleted_key(tmp_path):
    # renamed from test_export_is_version_7_...: 0016's own property is the
    # deleted-key omission; the header version moved to 8 with specs/0025
    # and its pin lives in the 0025/portability tests, not here.
    store = _store(tmp_path)
    store.add_edge(_edge(eid="e-x"))
    store.add_episode(Episode(
        id="ep-x", user_id="u1", date="2026-08-01", summary="s",
        provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                              evidence_ref="ev-ep")))
    p = tmp_path / "e.jsonl"
    export_memory(store, "u1", p)
    lines = [json.loads(ln) for ln in p.read_text().splitlines()]
    assert lines[0]["version"] == FORMAT_VERSION   # de-pinned; ≥7 since 0016
    assert "source_type" not in p.read_text()     # no residual key anywhere
    store.close()


def _write_v6_file(path, edge, episode, origin):
    """A ≤6 export: both provenances CARRY the historical source_type key."""
    erec = json.loads(edge.model_dump_json())
    erec["provenance"]["source_type"] = "stated"
    erec["provenance"]["origin"] = origin
    eprec = json.loads(episode.model_dump_json())
    eprec["provenance"]["source_type"] = "inferred"
    eprec["provenance"]["origin"] = origin
    eprec.pop("consolidation_output_index", None)
    with open(path, "w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": 6,
                            "user_id": "u1", "exported_at": "x"}) + "\n")
        f.write(json.dumps({"record": "edge", **erec}) + "\n")
        f.write(json.dumps({"record": "episode", **eprec}) + "\n")


def test_v6_import_drops_the_key_and_keeps_the_record(tmp_path):
    """A3: a ≤6 file's provenance.source_type keys are DROPPED on import —
    with every other field of the record intact (restore path, so no trust
    cap masks the strip)."""
    dest = _store(tmp_path, "dst.db")
    edge = _edge(eid="e-v6", obj="Miso", conf=0.7)
    ep = Episode(id="ep-v6", user_id="u1", date="2026-08-01", summary="s",
                 provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                       evidence_ref="ev-ep"))
    p = str(tmp_path / "v6.jsonl")
    _write_v6_file(p, edge, ep, origin="STORE-A")
    result = import_memory(dest, p, restore=True)
    assert result["edges"] == 1 and result["episodes"] == 1
    got = [x for x in dest.edges("u1", active_only=True) if x.id == "e-v6"][0]
    assert "source_type" not in got.provenance.model_dump()
    # the rest of the record is intact
    assert got.object == "Miso"
    assert got.provenance.confidence == 0.7
    assert got.provenance.evidence_ref == "ev-1"
    assert got.provenance.origin == "STORE-A"
    gep = [x for x in dest.episodes("u1") if x.id == "ep-v6"][0]
    assert "source_type" not in gep.provenance.model_dump()
    assert gep.summary == "s"
    dest.close()


def test_a_7_file_round_trips(tmp_path):
    src = _store(tmp_path, "src.db")
    src.add_edge(_edge(eid="e-rt"))
    p = tmp_path / "rt.jsonl"
    export_memory(src, "u1", p)
    dest = _store(tmp_path, "dst2.db")
    import_memory(dest, p, restore=True)
    got = [x for x in dest.edges("u1", active_only=True) if x.id == "e-rt"]
    assert len(got) == 1
    src_edge = [x for x in src.edges("u1", active_only=True)
                if x.id == "e-rt"][0]
    gd, sd = got[0].model_dump(), src_edge.model_dump()
    # export MATERIALISES the source's origin (0006 I6); into a DIFFERENT
    # store it stays foreign (I2b) — everything else round-trips exactly
    assert gd["provenance"].pop("origin") == src.local_origin()
    assert sd["provenance"].pop("origin") is None
    assert gd == sd
    src.close(); dest.close()


def test_extractor_cannot_emit_provenance_fields(tmp_path):
    """§2c row 3 / §1b clause 2 (I8), the deletion's own regression: the
    extraction schema contains NO provenance field — a model emitting a
    `source_type` (or `evidence_basis`) key has it dropped by the parser with
    no code path that reads it. Provenance is attested at the host boundary
    or not at all."""
    from veracium import Memory, MemoryConfig

    class Adversarial:
        def __call__(self, prompt, *, system=None, role="compile",
                     json_schema=None):
            if role == "distill":
                return json.dumps({
                    "triples": [{"subject": "user", "relation": "works_as",
                                 "object": "chef",
                                 "source_type": "observed",
                                 "evidence_basis": "observed"}],
                    "episode": "User is a chef.",
                    "source_type": "observed"})
            return "ok"

    mem = Memory(llm=Adversarial(),
                 config=MemoryConfig(db_path=str(tmp_path / "i8.db"),
                                     wiki_recompile_after_writes=0))
    mem.remember("u", "USER: I'm a chef.", date="2026-06-01")
    edges = [e for e in mem.store.edges("u", active_only=True)
             if e.relation == "works_as"]
    assert len(edges) == 1
    dumped = edges[0].provenance.model_dump()
    assert "source_type" not in dumped and "evidence_basis" not in dumped
    # the model asserted nothing: authorship stayed the host-declared value
    assert edges[0].provenance.author_of_evidence == EvidenceAuthor.USER
    mem.close()


def test_a_newer_file_is_refused_by_the_version_gate(tmp_path):
    """The current importer's half of the old-build rule: a file claiming a
    version above FORMAT_VERSION refuses BEFORE validation — the same gate
    that makes an old build refuse a 7-file honestly."""
    dest = _store(tmp_path, "dst3.db")
    p = str(tmp_path / "v8.jsonl")
    with open(p, "w") as f:
        f.write(json.dumps({"kind": "veracium-export",
                            "version": FORMAT_VERSION + 1,
                            "user_id": "u1"}) + "\n")
    with pytest.raises(ValueError, match="newer"):
        import_memory(dest, p)
    dest.close()


def test_evidence_basis_contract_frozen():
    """0016 I10 — the §1b successor contract is TEXT-PINNED: its four
    clauses must remain verbatim (at the anchor-phrase level) until a
    first-consumer spec supersedes them. This test was named at D1 and is
    implemented here at D2 (the deletion is that spec's prerequisite —
    §1b clause 4)."""
    import pathlib
    spec = pathlib.Path(__file__).resolve().parents[1] / \
        "specs/0016-sourcetype-deletion.md"
    flat = " ".join(spec.read_text().split())
    anchors = (
        "The evidence_basis contract — FROZEN here, field NOT shipped",
        # clause 1 — semantics, no total order, unknown is the floor
        "NOT a total order",
        "unknown is a fourth state, stored absent (I8), and is the FLOOR",
        "the spec that ships the first consumer",
        # clause 2 — unforgeability: the extraction schema has NO field
        "the extraction schema must not contain a basis field at all",
        "attested at a host-controlled boundary or not at all",
        # clause 3 — optional, host-supplied, never required
        "never required when `source_id` is present",
        # clause 4 — trigger
        "a first consumer, in its own spec",
    )
    missing = [a for a in anchors if " ".join(a.split()) not in flat]
    assert not missing, f"§1b contract drifted — missing anchors: {missing}"
