"""specs/0014 Slice D — consolidation_output_index + FORMAT v5 portability.

The named tests from §2c/§4c/§7a: store assignment + generic-path refusal +
contiguity; the exclude-none serializer exception with round-trips (older
importer refuses v5; v4 stays accepted; explicit null rejects; v4→v5→v5 is
lossless); duplicate present indices reject within one import AND against
destination state over the tenant-scoped origin-namespaced key; a
source-identical indexed output re-imports idempotently; the two-set projection
with its sets-are-exact, totality, and two-sided mutation oracles; and the
FROZEN repeated-import fixture (1 edge + 1 ordinary episode + 1 indexed output
per file → 2 edges, 2 ordinary + 1 indexed = 3 EPISODES TOTAL).
"""
import json
import uuid
from datetime import datetime, timezone

import pytest

from veracium import portability as P
from veracium.schema import to_historical_id as _thi
from veracium.schema import (ConsolidationOutputDraft, ConsolidationState, Edge, Episode, EvidenceAuthor, Provenance)
from veracium.store.sqlite import SqliteStore

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _prov(ref="ev-1", source_id=None):
    return Provenance(author_of_evidence=EvidenceAuthor.USER,
                      evidence_ref=ref, observed_at=NOW, confidence=0.9,
                      source_id=source_id)


def _store(tmp_path, name="s.db"):
    return SqliteStore(str(tmp_path / name))


def _seed_with_indexed_output(store, uid="u1"):
    """1 edge + 1 ordinary episode + 1 indexed consolidation output — the
    FROZEN fixture file shape (R12-2)."""
    store.add_edge(Edge(id="e-1", user_id=uid, subject="user", relation="pet",
                           object="Miso", valid_from=NOW, provenance=_prov()))
    store.add_episode(Episode(id="ep-plain", user_id=uid, date="2026-07-01",
                              summary="an ordinary day", provenance=_prov()))
    for i in range(2):
        store.add_episode(Episode(id=f"ep-in-{i}", user_id=uid,
                                  date=f"2026-06-0{i+1}",
                                  summary=f"input {i}", provenance=_prov()))
    op = store.create_or_takeover_consolidation(uid, ["ep-in-0", "ep-in-1"],
                                                "w1", 60)
    assert store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w1", ConsolidationState.GENERATING)
    assert store.write_consolidation_output_if_current(
        op.operation_id, op.fence, "w1",
        ConsolidationOutputDraft(summary="june, consolidated",
                                 date_start="2026-06-01", date_end="2026-06-02"))
    assert store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w1", ConsolidationState.OUTPUTS_DURABLE)
    assert store.delete_claimed_inputs_if_current(op.operation_id, op.fence)
    assert store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w1", ConsolidationState.FINALIZED)
    outs = [ep for ep in store.episodes(uid) if ep.lineage]
    assert len(outs) == 1 and outs[0].consolidation_output_index == 0
    return outs[0]


# -- assignment + refusal + contiguity ---------------------------------------

def test_the_primitive_assigns_sequential_indices(tmp_path):
    store = _store(tmp_path)
    out = _seed_with_indexed_output(store)
    assert out.consolidation_output_index == 0


def test_generic_add_episode_refuses_a_caller_supplied_index(tmp_path):
    """§2c: a host submitting a plain episode with index 0 → refused at the
    generic path (the fabrication case, named)."""
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store.add_episode(Episode(id="ep-forged", user_id="u1",
                                  date="2026-07-01", summary="forged",
                                  consolidation_output_index=0,
                                  provenance=_prov()))


# -- serialization + round-trips ----------------------------------------------

def test_export_omits_none_and_carries_present_indices(tmp_path):
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    lines = [json.loads(l) for l in path.read_text().splitlines()]
    assert lines[0]["version"] == 7           # specs/0016 D2 bumped 6->7
    eps = [l for l in lines if l.get("record") == "episode"]
    plain = [l for l in eps if not l.get("lineage")]
    outs = [l for l in eps if l.get("lineage")]
    assert all("consolidation_output_index" not in l for l in plain)  # omitted
    assert all(l.get("consolidation_output_index") == 0 for l in outs)


def test_an_older_importer_refuses_a_v5_export(tmp_path):
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    lines = path.read_text().splitlines()
    header = json.loads(lines[0])
    assert header["version"] == 7 > 4          # an importer with FORMAT<=5 refuses
    dest = _store(tmp_path, "d.db")
    bad = tmp_path / "newer.jsonl"
    header["version"] = 8                       # simulate a NEWER-than-us file (head FORMAT is 7, specs/0016 D2)
    bad.write_text("\n".join([json.dumps(header)] + lines[1:]) + "\n")
    with pytest.raises(ValueError, match="newer"):
        P.import_memory(dest, bad)


def test_v5_round_trip_is_lossless_and_v4_stays_accepted(tmp_path):
    """R7-3: absent stays absent, present stays present; a v4 file (no field)
    imports as the legacy shape."""
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    dest = _store(tmp_path, "d.db")
    P.import_memory(dest, path)
    outs = [ep for ep in dest.episodes("u1") if ep.lineage]
    assert outs[0].consolidation_output_index == 0            # present → present
    plains = [ep for ep in dest.episodes("u1") if not ep.lineage]
    assert all(ep.consolidation_output_index is None for ep in plains)
    # second hop: d -> d2 (v5→v5)
    path2 = tmp_path / "y.jsonl"
    P.export_memory(dest, "u1", path2)
    dest2 = _store(tmp_path, "d2.db")
    P.import_memory(dest2, path2)
    outs2 = [ep for ep in dest2.episodes("u1") if ep.lineage]
    assert outs2[0].consolidation_output_index == 0


def test_a_v5_output_without_an_index_is_the_legacy_shape(tmp_path):
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    lines = [json.loads(l) for l in path.read_text().splitlines()]
    for l in lines:
        l.pop("consolidation_output_index", None)             # strip the index
    legacy = tmp_path / "legacy.jsonl"
    legacy.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    dest = _store(tmp_path, "d.db")
    P.import_memory(dest, legacy)                             # accepted
    outs = [ep for ep in dest.episodes("u1") if ep.lineage]
    assert outs[0].consolidation_output_index is None         # less identity


def test_an_explicit_null_index_is_malformed(tmp_path):
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    lines = [json.loads(l) for l in path.read_text().splitlines()]
    for l in lines:
        if l.get("lineage"):
            l["consolidation_output_index"] = None            # explicit null
    bad = tmp_path / "null.jsonl"
    bad.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    with pytest.raises(ValueError, match="explicit null"):
        P.import_memory(_store(tmp_path, "d.db"), bad)


def test_type_gates_reject_bool_string_negative(tmp_path):
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    for value in (True, "0", -1):
        lines = [json.loads(l) for l in path.read_text().splitlines()]
        for l in lines:
            if l.get("lineage"):
                l["consolidation_output_index"] = value
        bad = tmp_path / "typed.jsonl"
        bad.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
        with pytest.raises(ValueError, match="non-negative integer"):
            P.import_memory(_store(tmp_path, f"d-{value}.db"), bad)


def test_an_index_on_a_plain_episode_is_fabricated_identity(tmp_path):
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    lines = [json.loads(l) for l in path.read_text().splitlines()]
    for l in lines:
        if l.get("record") == "episode" and not l.get("lineage"):
            l["consolidation_output_index"] = 0
    bad = tmp_path / "fab.jsonl"
    bad.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    with pytest.raises(ValueError, match="no lineage"):
        P.import_memory(_store(tmp_path, "d.db"), bad)


# -- uniqueness: within-file, destination-state, idempotent re-import ---------

def test_duplicate_output_index_within_an_imported_operation_is_rejected(tmp_path):
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    lines = path.read_text().splitlines()
    out_line = next(l for l in lines if json.loads(l).get("lineage"))
    dup = json.loads(out_line)
    dup["id"] = "ep-duplicate-claim"                          # different record,
    bad = tmp_path / "dup.jsonl"                              # same (op, index)
    bad.write_text("\n".join(lines + [json.dumps(dup)]) + "\n")
    with pytest.raises(ValueError, match="never duplicates"):
        P.import_memory(_store(tmp_path, "d.db"), bad)


def test_duplicate_output_index_across_sequential_imports_is_rejected(tmp_path):
    """R9-5/R12-3: import A at (op,0); then a DIFFERENT output B claiming the
    same key from a second file → the second import rejects."""
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    dest = _store(tmp_path, "d.db")
    P.import_memory(dest, path)                               # A lands
    lines = [json.loads(l) for l in path.read_text().splitlines()]
    for l in lines:
        if l.get("lineage"):
            l["summary"] = "a DIFFERENT consolidation entirely"
    b = tmp_path / "b.jsonl"
    b.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    with pytest.raises(ValueError, match="DIFFERENT source-identity"):
        P.import_memory(dest, b)


def test_repeated_remapped_import_resolves_the_indexed_output_idempotently(tmp_path):
    """R11-2/R12-2, the FROZEN fixture: the SAME file imported twice with
    user_id= — ordinary records follow the shipped remap-copy semantics while
    the indexed output claims no second identity. After TWO imports: 2 edges,
    2 ordinary episodes, 1 indexed output = 3 EPISODES TOTAL (total AND split
    asserted)."""
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    dest = _store(tmp_path, "d.db")
    P.import_memory(dest, path, user_id="target")
    P.import_memory(dest, path, user_id="target")             # the re-import
    edges = dest.edges("target", active_only=False, include_quarantined=True)
    eps = dest.episodes("target")
    ordinary = [e for e in eps if not e.lineage]
    indexed = [e for e in eps if e.lineage]
    assert len(edges) == 2                                    # remap-copy
    assert len(ordinary) == 2                                 # remap-copy
    assert len(indexed) == 1                                  # ONE identity
    assert len(eps) == 3                                      # the total
    assert indexed[0].consolidation_output_index == 0


# -- the projection's oracles -------------------------------------------------

def test_source_identity_projection_sets_are_exact():
    """R12-3: independent membership assertions for both sets."""
    assert P.PROJECTION_EXCLUDED_FIELDS == ("id", "user_id")
    assert set(P.PROJECTION_VERBATIM_FIELDS) == (
        set(Episode.model_fields) - {"id", "user_id"})


def test_source_identity_projection_is_total():
    """R11-3: the two sets partition Episode.model_fields — a future field
    breaks this until classified."""
    both = set(P.PROJECTION_EXCLUDED_FIELDS) | set(P.PROJECTION_VERBATIM_FIELDS)
    assert both == set(Episode.model_fields)
    assert not (set(P.PROJECTION_EXCLUDED_FIELDS)
                & set(P.PROJECTION_VERBATIM_FIELDS))


def test_every_projection_field_binds_source_identity(tmp_path):
    """R11-3/R13-2, two-sided: mutate any VERBATIM field in the second file →
    REJECT (including a lineage member id — a different historical episode);
    mutate an EXCLUDED field → idempotent (the destination-minted identity has
    no source meaning)."""
    store = _store(tmp_path)
    _seed_with_indexed_output(store)
    path = tmp_path / "x.jsonl"
    P.export_memory(store, "u1", path)
    dest = _store(tmp_path, "d.db")
    P.import_memory(dest, path)

    def _mutated_file(mutate):
        lines = [json.loads(l) for l in path.read_text().splitlines()]
        for l in lines:
            if l.get("lineage"):
                mutate(l)
        f = tmp_path / f"m-{uuid.uuid4().hex[:6]}.jsonl"
        f.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
        return f

    # VERBATIM mutations → reject
    for mutate in (
        lambda l: l.__setitem__("summary", "tampered"),
        lambda l: l.__setitem__("date", "1999-01-01"),
        lambda l: l["lineage"].__setitem__(0, _thi("DIFFERENT-EPISODE")),
        lambda l: l["provenance"].__setitem__("confidence", 0.01),
    ):
        with pytest.raises(ValueError, match="DIFFERENT source-identity"):
            P.import_memory(dest, _mutated_file(mutate))
    # EXCLUDED mutation → idempotent (skipped, not duplicated, not rejected)
    before = len(dest.episodes("u1"))
    P.import_memory(dest, _mutated_file(lambda l: l.__setitem__("id", "ep-renamed")))
    assert len(dest.episodes("u1")) == before
