"""specs/0021 §7b / specs/0020 §4a-iii — the FORMAT-7 `absorbed_by_id`
rider and the pre-commit import reconstruction through the amended 0009
§4c primitive.

Covers: the native-chain export carrying the structured field on both
absorbed records; the destination import persisting the reconstructed
rows (direct `imported-absorption` links + `scope-attribution`
transitive copies) atomically with the records; idempotent re-import
(rows skip, counted existing); conflicting-history refusal
(`DESTINATION_CHANGED` at the primitive; a clean whole-import refusal at
the importer); the PRE-COMMIT refusal cells (ambiguous legacy note
universe, missing tag, unresolvable tag, cyclic structured linkage,
structured-dangling) each leaving the destination's logical state
unchanged; the legacy note rule for files without the field; the
NULL-contributor_ref legacy store exporting with the field omitted; the
corrupt double-canonical ledger refusing the whole export; mid-plan
failure rolling the whole commit back; concurrent same-plan commits
linearizing at the primitive (one winner, no duplicates); and PARITY — the production reconstruction's row
multisets equal the normative reference's
(specs/evidence/0020/reference_scope.py; tests may import specs,
production never does).
"""

from __future__ import annotations

import json
import pathlib
import sys
import threading
from datetime import datetime, timezone

import pytest

from veracium import portability
from veracium.graph import DEFAULT_RELATIONS, apply_supersession
from veracium.schema import Edge, EvidenceAuthor, Provenance
from veracium.scope_linkage import (ExportLinkageError, ImportLinkageError,
                                    construct_plan_row, plan_row_id,
                                    reconstruct_absorption_rows)
from veracium.store.base import DESTINATION_CHANGED
from veracium.store.sqlite import SqliteStore

REFDIR = pathlib.Path(__file__).resolve().parents[1] / "specs" / "evidence" / "0020"

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _edge(obj, *, eid, sid, conf=0.9, rel="pet", note=""):
    return Edge(id=eid, user_id="u1", subject="user", relation=rel,
                object=obj, valid_from=NOW, note=note,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{eid}", source_id=sid,
                                      observed_at=NOW, confidence=conf))


def _chain_store(path):
    """A REAL A→B→C absorption chain via apply_supersession — the slice-1
    contributor columns populated by the shipped store.

    All three hops are WITHIN ONE SCOPE since specs/0021 §4c landed: the
    absorption partition refuses a cross-scope prior outright, so a
    cross-digest chain can no longer be built through the native writer at
    all (it only arrives as legacy or imported state — which is what the
    §4d/W13 cells build directly). These tests are about the LINKAGE
    carriers, and the linkage is identical either way."""
    s = SqliteStore(path)
    apply_supersession(s, _edge("Miso", eid="A", sid="agent-a", conf=0.2),
                       DEFAULT_RELATIONS)
    apply_supersession(s, _edge("cat Miso", eid="B", sid="agent-a", conf=0.5),
                       DEFAULT_RELATIONS)
    apply_supersession(s, _edge("small cat Miso", eid="C", sid="agent-a",
                               conf=0.9), DEFAULT_RELATIONS)
    return s


def _edge_records(path):
    out = {}
    for line in pathlib.Path(path).read_text().splitlines():
        rec = json.loads(line)
        if rec.get("record") == "edge":
            out[rec["id"]] = rec
    return out


def _logical_state(store, user_id):
    """The destination-unchanged fingerprint: full logical edge state plus
    every edge's contribution-row projection."""
    return sorted(
        (e.id, e.object, e.invalidation_reason or "", e.note or "",
         tuple(sorted((c.id, c.site, c.identity_digest or "",
                       c.contributor_ref or "")
                      for c in store.contributions(user_id, "edge", e.id))))
        for e in store.edges(user_id, active_only=False,
                             include_quarantined=True))


def _write_export(path, records, *, version=7, user="u1"):
    with open(path, "w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": version,
                            "user_id": user}) + "\n")
        for r in records:
            f.write(json.dumps(r) + "\n")


def _rec(eid, *, obj, reason=None, note=None, absorbed_by=None,
         sid=None, version7=True):
    r = {"record": "edge", "id": eid, "user_id": "u1", "subject": "user",
         "relation": "pet", "object": obj, "valid_from": NOW.isoformat(),
         "note": note or "", "invalidation_reason": reason,
         "provenance": {"author_of_evidence": "user",
                        "evidence_ref": f"ev-{eid}",
                        "source_id": sid or f"agent-{eid}",
                        "origin": "org-x", "observed_at": NOW.isoformat(),
                        "confidence": 0.5}}
    if absorbed_by is not None:
        r["absorbed_by_id"] = absorbed_by
    return r


# ---------------------------------------------------------------------------
# EXPORT: the structured reverse link
# ---------------------------------------------------------------------------

def test_native_chain_export_carries_absorbed_by_id_on_both_absorbed(tmp_path):
    s = _chain_store(tmp_path / "s.db")
    exp = tmp_path / "u.jsonl"
    portability.export_memory(s, "u1", exp)
    recs = _edge_records(exp)
    assert recs["A"]["invalidation_reason"] == "absorbed_duplicate"
    assert recs["A"]["absorbed_by_id"] == "B"
    assert recs["B"]["invalidation_reason"] == "absorbed_duplicate"
    assert recs["B"]["absorbed_by_id"] == "C"
    # present IFF absorbed_duplicate with a canonical row: the survivor
    # never carries the field
    assert "absorbed_by_id" not in recs["C"]
    s.close()


def test_null_contributor_ref_legacy_store_exports_field_omitted(tmp_path):
    """Rows written before slice 1 carry NULL contributor_ref — they
    contribute nothing and the record exports LEGACY (field omitted)."""
    s = _chain_store(tmp_path / "s.db")
    s._conn.execute("UPDATE contribution_ledger SET contributor_ref=NULL, "
                    "contributor_type=NULL")
    s._conn.commit()
    exp = tmp_path / "legacy.jsonl"
    portability.export_memory(s, "u1", exp)
    recs = _edge_records(exp)
    assert recs["A"]["invalidation_reason"] == "absorbed_duplicate"
    assert "absorbed_by_id" not in recs["A"]
    assert "absorbed_by_id" not in recs["B"]
    s.close()


def test_double_canonical_ledger_refuses_the_whole_export(tmp_path):
    """>1 canonical rows naming one contributor is corrupt linkage — the
    export refuses WHOLE, before the file is even created."""
    s = _chain_store(tmp_path / "s.db")
    # forge a second canonical (direct-site) row naming A under survivor C
    row = s._conn.execute(
        "SELECT user_id,survivor_type,site,identity_digest,"
        "evidence_ref_digest,payload,created_at,contributor_type,"
        "contributor_ref FROM contribution_ledger WHERE contributor_ref='A' "
        # the CANONICAL row specifically: since 0021 §4c, C also carries a
        # flattened scope-attribution COPY naming A, and that one is not
        # canonical — forging a duplicate of it would prove nothing
        "AND site='absorption'"
    ).fetchone()
    assert row is not None
    s._conn.execute(
        "INSERT INTO contribution_ledger(id,user_id,survivor_type,"
        "survivor_id,site,identity_digest,evidence_ref_digest,payload,"
        "op_key,created_at,contributor_type,contributor_ref) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        ("forged-dup", row[0], row[1], "C", row[2], row[3], row[4], row[5],
         None, row[6], row[7], row[8]))
    s._conn.commit()
    exp = tmp_path / "corrupt.jsonl"
    with pytest.raises(ExportLinkageError, match="canonical absorber rows"):
        portability.export_memory(s, "u1", exp)
    assert not exp.exists(), "a refused export must not leave a partial file"
    s.close()


# ---------------------------------------------------------------------------
# IMPORT: the reconstructed rows ride the atomic commit
# ---------------------------------------------------------------------------

def test_import_persists_direct_and_transitive_rows_and_reads_back(tmp_path):
    s = _chain_store(tmp_path / "s.db")
    exp = tmp_path / "u.jsonl"
    portability.export_memory(s, "u1", exp)
    s.close()
    dest = SqliteStore(tmp_path / "dest.db")
    r = portability.import_memory(dest, exp, restore=True)
    assert r["edges"] == 3 and r["contributions"] == 3
    assert r["contributions_existing"] == 0
    # membership-style reads via store.contributions(): C carries the
    # DIRECT link to B and the TRANSITIVE scope-attribution copy of A
    c_rows = {(c.site, c.contributor_ref):
              (c.payload, c.identity_digest, c.evidence_ref_digest, c.op_key)
              for c in dest.contributions("u1", "edge", "C")}
    assert set(c_rows) == {("imported-absorption", "B"),
                           ("scope-attribution", "A")}
    assert c_rows[("imported-absorption", "B")][0] == {"reconstructed": True}
    assert c_rows[("scope-attribution", "A")][0] == \
        {"flattened": True, "reconstructed": True}
    for payload, ident, ev, op_key in c_rows.values():
        assert ident and ev and op_key      # complete rows (R8-3)
    b_rows = dest.contributions("u1", "edge", "B")
    assert [(c.site, c.contributor_ref, c.payload) for c in b_rows] == \
        [("imported-absorption", "A", {"reconstructed": True})]
    # one minted op governs every row; per-row keys are distinct
    keys = [c.op_key for c in dest.contributions("u1", "edge", "C")] + \
           [c.op_key for c in b_rows]
    assert len(set(keys)) == 3
    assert len({k.split(":", 1)[0] for k in keys}) == 1
    dest.close()


def test_reimport_is_idempotent_rows_skip_counted_existing(tmp_path):
    s = _chain_store(tmp_path / "s.db")
    exp = tmp_path / "u.jsonl"
    portability.export_memory(s, "u1", exp)
    s.close()
    dest = SqliteStore(tmp_path / "dest.db")
    portability.import_memory(dest, exp, restore=True)
    before = _logical_state(dest, "u1")
    again = portability.import_memory(dest, exp, restore=True)
    assert again["edges"] == 0 and again["contributions"] == 0
    assert again["contributions_existing"] == 3
    assert _logical_state(dest, "u1") == before
    n = dest._conn.execute(
        "SELECT COUNT(*) FROM contribution_ledger").fetchone()[0]
    assert n == 3, "re-import duplicated ledger rows"
    dest.close()


def test_remapped_import_keys_rows_to_postremap_ids(tmp_path):
    s = _chain_store(tmp_path / "s.db")
    exp = tmp_path / "u.jsonl"
    portability.export_memory(s, "u1", exp)
    s.close()
    dest = SqliteStore(tmp_path / "dest.db")
    r = portability.import_memory(dest, exp, user_id="u2")
    assert r["contributions"] == 3
    by_obj = {e.object: e.id for e in dest.edges("u2", active_only=False)}
    surv = by_obj["small cat Miso"]
    rows = dest.contributions("u2", "edge", surv)
    assert {(c.site, c.contributor_ref) for c in rows} == \
        {("imported-absorption", by_obj["cat Miso"]),
         ("scope-attribution", by_obj["Miso"])}
    dest.close()


def test_conflicting_history_primitive_returns_destination_changed(tmp_path):
    """A survivor whose current rows are neither absent nor plan-row-equal
    is a DIFFERENT history: the primitive returns DESTINATION_CHANGED and
    writes NOTHING — records included."""
    s = _chain_store(tmp_path / "s.db")
    exp = tmp_path / "u.jsonl"
    portability.export_memory(s, "u1", exp)
    s.close()
    dest = SqliteStore(tmp_path / "dest.db")
    portability.import_memory(dest, exp, restore=True)
    before = _logical_state(dest, "u1")
    current = sorted(c.id for c in dest.contributions("u1", "edge", "C"))
    # a CONFLICTING history for C: one direct row from a different
    # contributor, built through the operation-aware constructor
    op = "op-1234abcd5678"
    row = construct_plan_row(
        "import", op, "C", site="imported-absorption",
        identity_digest="a" * 64, evidence_ref_digest=None,
        contributor_ref="elsewhere", payload={"reconstructed": True})
    plan_row = {"id": plan_row_id("u1", "edge", "C", row, "import", op=op),
                "user_id": "u1", "survivor_type": "edge",
                "survivor_id": "C", **row}
    out = dest.commit_outcome_import_plan(
        "u1", {"edges": [], "episodes": [], "contributions": [plan_row]},
        {"edge_ids": {}, "episode_records": {}, "chain_heads": {},
         "contribution_state": {"C": current}})
    assert out is DESTINATION_CHANGED
    assert _logical_state(dest, "u1") == before, "DESTINATION_CHANGED wrote"
    dest.close()


def test_conflicting_history_reimport_refuses_whole_writing_nothing(tmp_path):
    """import_memory-level: a destination survivor carrying extra recorded
    rows (a different history shape) refuses the WHOLE re-import cleanly."""
    s = _chain_store(tmp_path / "s.db")
    exp = tmp_path / "u.jsonl"
    portability.export_memory(s, "u1", exp)
    s.close()
    dest = SqliteStore(tmp_path / "dest.db")
    portability.import_memory(dest, exp, restore=True)
    # an extra ledger row lands on C outside the import (a different
    # recorded history)
    dest._conn.execute(
        "INSERT INTO contribution_ledger(id,user_id,survivor_type,"
        "survivor_id,site,identity_digest,evidence_ref_digest,payload,"
        "op_key,created_at,contributor_type,contributor_ref) "
        "VALUES('extra-row','u1','edge','C','imported-absorption',?,"
        "NULL,'{\"reconstructed\":true}',NULL,'2026-08-16T00:00:00Z',"
        "'edge','other')", ("b" * 64,))
    dest._conn.commit()
    before = _logical_state(dest, "u1")
    with pytest.raises(ValueError, match="DIFFERENT recorded absorption"):
        portability.import_memory(dest, exp, restore=True)
    assert _logical_state(dest, "u1") == before
    dest.close()


def test_midplan_failure_rolls_back_the_whole_commit(tmp_path):
    """Contribution rows ride the ONE atomic commit: a failure after the
    record inserts leaves NOTHING durable (edges included)."""
    dest = SqliteStore(tmp_path / "dest.db")
    e = _edge("Rex", eid="R", sid="agent-r")
    op = "op-1234abcd5678"
    row = construct_plan_row(
        "import", op, "R", site="imported-absorption",
        identity_digest=None, evidence_ref_digest=None,
        contributor_ref="gone", payload={"reconstructed": True})
    plan_row = {"id": plan_row_id("u1", "edge", "R", row, "import", op=op),
                "user_id": "u1", "survivor_type": "edge",
                "survivor_id": "R", **row}
    with pytest.raises(Exception):
        # the duplicated plan row violates the ledger PRIMARY KEY on the
        # SECOND insert — after the edge was already written in-tx
        dest.commit_outcome_import_plan(
            "u1", {"edges": [e], "episodes": [],
                   "contributions": [plan_row, plan_row]},
            {"edge_ids": {}, "episode_records": {}, "chain_heads": {},
             "contribution_state": {"R": []}})
    assert dest.edges("u1", active_only=False) == []
    assert dest._conn.execute(
        "SELECT COUNT(*) FROM contribution_ledger").fetchone()[0] == 0
    dest.close()


def test_concurrent_same_plan_commits_linearize_no_duplicates(tmp_path):
    """The 0009-amendment concurrency cell AT THE PRIMITIVE (which is what
    linearizes — every destination read/write under one lock): two threads
    committing the SAME plan produce ONE winner; the loser's atomic
    revalidation sees the winner's rows (its expected state is stale) and
    returns DESTINATION_CHANGED writing nothing — no duplicates, no partial
    state. The loser's re-preflight then sees the rows as plan-row-equal
    and SKIPS (the import_memory retry loop's path, exercised here as the
    follow-up commit)."""
    dest = SqliteStore(tmp_path / "dest.db")
    e = _edge("Rex", eid="R", sid="agent-r")
    op = "op-1234abcd5678"
    rows = []
    for cref in ("gone-a", "gone-b", "gone-c"):
        row = construct_plan_row(
            "import", op, "R", site="imported-absorption",
            identity_digest=None, evidence_ref_digest=None,
            contributor_ref=cref, payload={"reconstructed": True})
        rows.append({"id": plan_row_id("u1", "edge", "R", row, "import",
                                       op=op),
                     "user_id": "u1", "survivor_type": "edge",
                     "survivor_id": "R", **row})
    plan = {"edges": [e], "episodes": [], "contributions": rows}
    expected = {"edge_ids": {"R": False}, "episode_records": {},
                "chain_heads": {}, "contribution_state": {"R": []}}
    results, errors = [], []

    def work():
        try:
            results.append(
                dest.commit_outcome_import_plan("u1", plan, expected))
        except BaseException as exc:            # pragma: no cover
            errors.append(exc)

    ts = [threading.Thread(target=work) for _ in range(2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert not errors
    wins = [r for r in results if r is not DESTINATION_CHANGED]
    assert len(wins) == 1 and wins[0]["contributions"] == 3
    assert results.count(DESTINATION_CHANGED) == 1
    assert dest._conn.execute(
        "SELECT COUNT(*) FROM contribution_ledger").fetchone()[0] == 3
    # the loser's re-preflight (the import_memory retry path): expected
    # re-read as current -> plan-row-equal -> SKIP, nothing rewritten
    current = sorted(c.id for c in dest.contributions("u1", "edge", "R"))
    again = dest.commit_outcome_import_plan(
        "u1", {"edges": [], "episodes": [], "contributions": rows},
        {"edge_ids": {"R": True}, "episode_records": {}, "chain_heads": {},
         "contribution_state": {"R": current}})
    assert again["contributions"] == 0
    assert again["contributions_existing"] == 3
    assert dest._conn.execute(
        "SELECT COUNT(*) FROM contribution_ledger").fetchone()[0] == 3
    dest.close()


def test_primitive_refuses_caller_selected_ids_keys_and_split_ops(tmp_path):
    """R13-1/R9-3: op keys and row ids are DERIVED in-primitive — a
    caller-selected id, a mis-derived key, a foreign tenant, and a
    two-op plan all refuse before any write."""
    dest = SqliteStore(tmp_path / "dest.db")
    op = "op-1234abcd5678"
    row = construct_plan_row(
        "import", op, "R", site="imported-absorption",
        identity_digest=None, evidence_ref_digest=None,
        contributor_ref="gone", payload={"reconstructed": True})
    good = {"id": plan_row_id("u1", "edge", "R", row, "import", op=op),
            "user_id": "u1", "survivor_type": "edge",
            "survivor_id": "R", **row}
    expected = {"edge_ids": {}, "episode_records": {}, "chain_heads": {},
                "contribution_state": {"R": []}}
    e = _edge("Rex", eid="R", sid="agent-r")

    def attempt(mutate):
        bad = dict(good)
        mutate(bad)
        with pytest.raises(ValueError):
            dest.commit_outcome_import_plan(
                "u1", {"edges": [e], "episodes": [],
                       "contributions": [bad]}, expected)

    attempt(lambda b: b.update(id="f" * 64))            # caller-selected id
    attempt(lambda b: b.update(                          # mis-derived key
        op_key=f"{op}:imported-absorption:" + "0" * 64))
    attempt(lambda b: b.update(user_id="intruder"))      # foreign tenant
    attempt(lambda b: b.pop("op_key"))                   # absent key (R11-2)
    other = construct_plan_row(                          # a SECOND op id
        "import", "op-aaaaaaaaaaaa", "R", site="imported-absorption",
        identity_digest=None, evidence_ref_digest=None,
        contributor_ref="gone2", payload={"reconstructed": True})
    other_plan = {"id": plan_row_id("u1", "edge", "R", other, "import",
                                    op="op-aaaaaaaaaaaa"),
                  "user_id": "u1", "survivor_type": "edge",
                  "survivor_id": "R", **other}
    with pytest.raises(ValueError, match="TWO operation ids"):
        dest.commit_outcome_import_plan(
            "u1", {"edges": [e], "episodes": [],
                   "contributions": [good, other_plan]}, expected)
    # a survivor naming neither a plan record nor a present record refuses
    with pytest.raises(ValueError, match="neither a plan record"):
        dest.commit_outcome_import_plan(
            "u1", {"edges": [], "episodes": [], "contributions": [good]},
            expected)
    assert dest.edges("u1", active_only=False) == []
    assert dest._conn.execute(
        "SELECT COUNT(*) FROM contribution_ledger").fetchone()[0] == 0
    dest.close()


# ---------------------------------------------------------------------------
# the PRE-COMMIT refusal cells — destination unchanged
# ---------------------------------------------------------------------------

def _refusal_file(tmp_path, name):
    if name == "ambiguous-legacy":
        # id universe {"w", "w; q"}: the note remainder "w; q" matches BOTH
        recs = [_rec("w", obj="x"), _rec("w; q", obj="y"),
                _rec("l", obj="z", reason="absorbed_duplicate",
                     note="absorbed_by:w; q")]
    elif name == "missing-tag":
        recs = [_rec("w", obj="x"),
                _rec("l", obj="z", reason="absorbed_duplicate",
                     note="retired")]
    elif name == "unresolvable-tag":
        recs = [_rec("w", obj="x"),
                _rec("l", obj="z", reason="absorbed_duplicate",
                     note="absorbed_by:ghost")]
    elif name == "cyclic-structured":
        recs = [_rec("a", obj="x", reason="absorbed_duplicate",
                     absorbed_by="b"),
                _rec("b", obj="y", reason="absorbed_duplicate",
                     absorbed_by="a")]
    elif name == "structured-dangling":
        recs = [_rec("w", obj="x"),
                _rec("l", obj="z", reason="absorbed_duplicate",
                     absorbed_by="ghost")]
    elif name == "structured-contradictory":
        # absorbed_by_id on a record that is NOT absorbed_duplicate
        recs = [_rec("w", obj="x", absorbed_by="l"), _rec("l", obj="z")]
    else:                                        # pragma: no cover
        raise AssertionError(name)
    p = tmp_path / f"{name}.jsonl"
    _write_export(p, recs)
    return p


@pytest.mark.parametrize("cell", ["ambiguous-legacy", "missing-tag",
                                  "unresolvable-tag", "cyclic-structured",
                                  "structured-dangling",
                                  "structured-contradictory"])
def test_refusal_cell_leaves_destination_unchanged(tmp_path, cell):
    dest = SqliteStore(tmp_path / f"{cell}.db")
    dest.add_edge(_edge("sentinel", eid="pre", sid="agent-s", rel="fish"))
    before = _logical_state(dest, "u1")
    with pytest.raises(ImportLinkageError):
        portability.import_memory(dest, _refusal_file(tmp_path, cell))
    assert _logical_state(dest, "u1") == before, \
        f"{cell}: destination changed on a PRE-COMMIT refusal"
    assert dest.contributions("u1", "edge", "pre") == []
    dest.close()


# ---------------------------------------------------------------------------
# legacy files and version gates
# ---------------------------------------------------------------------------

def _strip_structured(path):
    lines = []
    for line in pathlib.Path(path).read_text().splitlines():
        rec = json.loads(line)
        rec.pop("absorbed_by_id", None)
        lines.append(json.dumps(rec))
    pathlib.Path(path).write_text("\n".join(lines) + "\n")
    return path


def test_legacy_file_without_field_takes_the_note_rule(tmp_path):
    s = _chain_store(tmp_path / "s.db")
    exp = tmp_path / "u.jsonl"
    portability.export_memory(s, "u1", exp)
    s.close()
    _strip_structured(exp)
    dest = SqliteStore(tmp_path / "dest.db")
    r = portability.import_memory(dest, exp, restore=True)
    assert r["contributions"] == 3
    assert {(c.site, c.contributor_ref)
            for c in dest.contributions("u1", "edge", "C")} == \
        {("imported-absorption", "B"), ("scope-attribution", "A")}
    dest.close()


def test_pre_v7_envelope_absorbed_by_id_is_stripped_never_trusted(tmp_path):
    """0006 I10: a v6 file cannot legitimately carry the FORMAT-7 rider
    field — a DANGLING absorbed_by_id in a v6 envelope is stripped and the
    valid note rule governs instead (the field is never even read)."""
    recs = [_rec("w", obj="x"),
            _rec("l", obj="z", reason="absorbed_duplicate",
                 note="absorbed_by:w", absorbed_by="ghost")]
    p = tmp_path / "v6.jsonl"
    _write_export(p, recs, version=6)
    dest = SqliteStore(tmp_path / "dest.db")
    r = portability.import_memory(dest, p)
    assert r["contributions"] == 1
    rows = dest.contributions(r["user_id"], "edge", "w")
    assert [(c.site, c.contributor_ref) for c in rows] == \
        [("imported-absorption", "l")]
    dest.close()


# ---------------------------------------------------------------------------
# PARITY with the normative reference (tests may import specs/)
# ---------------------------------------------------------------------------

def _reference():
    sys.path.insert(0, str(REFDIR))
    try:
        import reference_scope
    finally:
        sys.path.remove(str(REFDIR))
    return reference_scope


def _parse_for_linkage(path):
    out = []
    for rec in _edge_records(path).values():
        prov = rec.get("provenance") or {}
        out.append({"id": rec["id"],
                    "invalidation_reason": rec.get("invalidation_reason"),
                    "note": rec.get("note"),
                    "absorbed_by_id": rec.get("absorbed_by_id"),
                    "origin": prov.get("origin"),
                    "source_id": prov.get("source_id"),
                    "evidence_ref": prov.get("evidence_ref")})
    return out


def test_production_reconstruction_matches_the_reference(tmp_path):
    """Over real fixture files (structured AND legacy-note), production's
    rows EQUAL the reference's — every field including the derived op_key —
    and the plan_row_id projections agree."""
    ref = _reference()
    s = _chain_store(tmp_path / "s.db")
    structured = tmp_path / "structured.jsonl"
    portability.export_memory(s, "u1", structured)
    s.close()
    legacy = tmp_path / "legacy.jsonl"
    legacy.write_text(structured.read_text())
    _strip_structured(legacy)
    op = "op-feedbeef0042"
    for fixture in (structured, legacy):
        records = _parse_for_linkage(fixture)
        mine = reconstruct_absorption_rows(records, "org-dest-1",
                                           import_op=op)
        theirs = ref.reconstruct_absorption_rows(records, "org-dest-1",
                                                 import_op=op)
        assert set(mine) == set(theirs), fixture.name
        for surv in mine:
            key = lambda r: r["op_key"]                     # noqa: E731
            assert sorted(mine[surv], key=key) == \
                sorted(theirs[surv], key=key), (fixture.name, surv)
            for m, t in zip(sorted(mine[surv], key=key),
                            sorted(theirs[surv], key=key)):
                assert (m["site"], m["identity_digest"],
                        m["contributor_ref"], m["payload"]) == \
                       (t["site"], t["identity_digest"],
                        t["contributor_ref"], t["payload"])
                assert plan_row_id("u1", "edge", surv, m, "import", op=op) \
                    == ref.plan_row_id("u1", "edge", surv, t, "import",
                                       op=op)


def test_refusal_parity_with_the_reference(tmp_path):
    """The refusal cells refuse in BOTH implementations."""
    ref = _reference()
    for cell in ("ambiguous-legacy", "missing-tag", "unresolvable-tag",
                 "cyclic-structured", "structured-dangling",
                 "structured-contradictory"):
        records = _parse_for_linkage(_refusal_file(tmp_path, cell))
        with pytest.raises(ImportLinkageError):
            reconstruct_absorption_rows(records, "org-dest-1",
                                        import_op="op-feedbeef0042")
        with pytest.raises(ref.ImportLinkageError):
            ref.reconstruct_absorption_rows(records, "org-dest-1",
                                            import_op="op-feedbeef0042")
