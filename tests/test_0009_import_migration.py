"""specs/0009 §4c/§4f import + migration invariants — H4, H5, H12, H13, H14.

The runtime append-only chain (H1–H3) is tested in test_outcomes.py; this file
covers the two ways an outcome chain crosses a boundary — a portable import and an
on-disk v2→v3 migration — plus the H14 fence that keeps the generic mutators out of
the outcome-chain business. The rule everywhere is the same: **validate or refuse,
never repair; commit the whole thing atomically or nothing at all.**
"""
import json
from datetime import datetime, timezone

import pytest

from veracium.portability import FORMAT_VERSION, export_memory, import_memory
from veracium.schema import (Edge, Episode, EvidenceAuthor, Outcome,
                             OutcomeJudgmentDraft, Provenance, SourceType)
from veracium.store.base import DESTINATION_CHANGED
from veracium.store.migration import DuplicateOutcomeChainError, migrate_store
from veracium.store.schema_version import SCHEMA_V2
from veracium.store.sqlite import SqliteStore

JAN = datetime(2026, 1, 1, tzinfo=timezone.utc)


# --- fixtures ---------------------------------------------------------------

def _edge(eid="e1", uid="u"):
    return Edge(id=eid, user_id=uid, subject="user", relation="prefers", object="o",
                valid_from=JAN, active=True,
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=eid, observed_at=JAN))


def _outcome(*, eid="e1", evref="run-1", seq=1, supersedes=None,
             author=EvidenceAuthor.SYSTEM, outcome=Outcome.CONCURRED, jtk=True,
             oid=None, uid="u", summary="s", date="2026-01-01"):
    return Episode(
        id=oid or f"o-{eid}-{evref}-{seq}", user_id=uid, date=date, summary=summary,
        kind="outcome", edge_id=eid, outcome=outcome, seq=seq,
        supersedes_episode=supersedes, judgment_time_known=jtk,
        provenance=Provenance(
            source_type=SourceType.INFERRED if author == EvidenceAuthor.SYSTEM
            else SourceType.STATED,
            author_of_evidence=author, evidence_ref=evref))


def _write_export(path, records, *, uid="u", version=3, origin=None):
    # specs/0006: a v4 export materialises a resolved origin on every record; pass
    # `origin` to stamp one (a v4 record with an absent origin is rejected on import, I14).
    with open(path, "w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": version,
                            "user_id": uid,
                            "exported_at": "2026-01-01T00:00:00+00:00"}) + "\n")
        for marker, model in records:
            rec = json.loads(model.model_dump_json())
            # mirror the real exporter (specs/0014 §4c R7-3): the index is
            # emitted with exclude-none semantics — a well-formed v5 file
            # OMITS None, and an explicit null is malformed on import.
            if rec.get("consolidation_output_index") is None:
                rec.pop("consolidation_output_index", None)
            if origin is not None and isinstance(rec.get("provenance"), dict):
                rec["provenance"]["origin"] = origin
            f.write(json.dumps({"record": marker, **rec}) + "\n")


def _src_with_chain(path, *, evref="run-1", links=2):
    """A source store with edge e1 and a real `links`-long outcome chain on
    (e1, evref), built through the sanctioned CAS writer."""
    s = SqliteStore(path)
    s.add_edge(_edge("e1"))
    head_id = None
    pairs = [(EvidenceAuthor.SYSTEM, Outcome.CONCURRED),
             (EvidenceAuthor.USER, Outcome.CONFIRMED),
             (EvidenceAuthor.SYSTEM, Outcome.CHALLENGED)]
    for i in range(links):
        author, outcome = pairs[i % len(pairs)]
        ep = s.append_outcome_if_head(
            "u", "e1", evref, head_id,
            OutcomeJudgmentDraft(author=author, event_timestamp=f"2026-01-0{i+1}",
                                 outcome=outcome, summary=f"j{i}"))
        head_id = ep.id
    return s


def _outcomes(store, uid="u", key=None):
    outs = [ep for ep in store.episodes(uid) if ep.kind == "outcome"]
    if key is not None:
        outs = [ep for ep in outs
                if (ep.edge_id, ep.provenance.evidence_ref) == key]
    return outs


# --- H4: a valid chain imports preserved -----------------------------------

def test_import_preserves_the_outcome_chain(tmp_path):
    src = _src_with_chain(str(tmp_path / "src.db"), links=3)
    exp = str(tmp_path / "e.jsonl")
    export_memory(src, "u", exp)
    # specs/0006 I6: export MATERIALISES the source store's resolved origin onto every
    # record, so the imported copy carries src's origin where src stored it absent. The
    # chain is otherwise byte-for-byte preserved.
    src_origin = src.local_origin()
    before = {ep.id: ep.model_dump() for ep in _outcomes(src)}
    for d in before.values():
        d["provenance"]["origin"] = src_origin

    dst = SqliteStore(str(tmp_path / "dst.db"))
    # specs/0005 §7b: byte-preservation of the chain (trust fields included) is
    # the RESTORE path's contract; the default import caps trust by design.
    r = import_memory(dst, exp, restore=True)
    after = {ep.id: ep.model_dump() for ep in _outcomes(dst)}
    assert before == after, "the chain must import preserved (origin materialised to src)"
    # head re-derivable, contiguous, single leaf
    seqs = sorted(ep.seq for ep in _outcomes(dst))
    assert seqs == [1, 2, 3]
    assert r["episodes"] >= 3


def test_cross_user_import_remaps_supersedes_episode(tmp_path):
    src = _src_with_chain(str(tmp_path / "src.db"), links=2)
    exp = str(tmp_path / "e.jsonl")
    export_memory(src, "u", exp)

    dst = SqliteStore(str(tmp_path / "dst.db"))
    import_memory(dst, exp, user_id="v")
    outs = sorted(_outcomes(dst, uid="v"), key=lambda e: e.seq)
    assert len(outs) == 2
    root, child = outs
    # ids are freshly minted (not the source ids) AND the child's back-reference
    # points at the REMAPPED root, not the source store's episode id
    assert child.supersedes_episode == root.id
    assert not root.id.startswith("o-"), "cross-user import must mint fresh ids"
    assert child.provenance.evidence_ref == "run-1"


def test_two_valid_chains_same_identity_refuses(tmp_path):
    # two individually-valid roots for ONE (edge_id, evidence_ref) — combining them
    # would branch the destination; refuse before any write.
    recs = [("edge", _edge("e1")),
            ("episode", _outcome(seq=1, oid="a")),
            ("episode", _outcome(seq=1, oid="b"))]
    exp = str(tmp_path / "e.jsonl")
    _write_export(exp, recs)
    dst = SqliteStore(str(tmp_path / "dst.db"))
    with pytest.raises(ValueError):
        import_memory(dst, exp)
    assert _outcomes(dst) == [] and dst.edges("u", active_only=False) == []


def test_import_refuses_missing_or_foreign_edge(tmp_path):
    # an outcome chain whose edge_id resolves to no Edge in the file or the store
    recs = [("episode", _outcome(seq=1, oid="a", eid="ghost"))]
    exp = str(tmp_path / "e.jsonl")
    _write_export(exp, recs)
    dst = SqliteStore(str(tmp_path / "dst.db"))
    with pytest.raises(ValueError, match="missing or foreign"):
        import_memory(dst, exp)
    assert _outcomes(dst) == []


def test_same_id_different_author_refuses_whole_import(tmp_path):
    # a colliding id is NOT proof of the same historical fact (§4c record equality)
    dst = _src_with_chain(str(tmp_path / "dst.db"), links=1)
    root = _outcomes(dst)[0]
    forged = _outcome(seq=1, oid=root.id, author=EvidenceAuthor.USER,
                      outcome=Outcome.CONFIRMED)
    exp = str(tmp_path / "e.jsonl")
    _write_export(exp, [("edge", _edge("e1")), ("episode", forged)])
    with pytest.raises(ValueError, match="different content"):
        import_memory(dst, exp)


def test_same_id_different_outcome_refuses(tmp_path):
    dst = _src_with_chain(str(tmp_path / "dst.db"), links=1)
    root = _outcomes(dst)[0]
    forged = _outcome(seq=1, oid=root.id, author=EvidenceAuthor.SYSTEM,
                      outcome=Outcome.CHALLENGED)   # same author, different outcome
    exp = str(tmp_path / "e.jsonl")
    _write_export(exp, [("edge", _edge("e1")), ("episode", forged)])
    with pytest.raises(ValueError, match="different content"):
        import_memory(dst, exp)


def test_same_user_reimport_is_idempotent(tmp_path):
    src = _src_with_chain(str(tmp_path / "src.db"), links=2)
    exp = str(tmp_path / "e.jsonl")
    export_memory(src, "u", exp)
    before = {ep.id: ep.model_dump() for ep in _outcomes(src)}
    # specs/0005 §7b: an own-store re-import is the restore path — the default
    # path refuses it (stored originals differ from the capped incoming form).
    r2 = import_memory(src, exp, restore=True)   # re-import into itself
    assert r2["episodes"] == 0 and r2["skipped"] >= 2
    assert {ep.id: ep.model_dump() for ep in _outcomes(src)} == before


def test_import_extends_the_destination_head(tmp_path):
    # destination is an exact prefix of the incoming chain → the suffix extends head
    src = _src_with_chain(str(tmp_path / "src.db"), links=3)
    exp = str(tmp_path / "e.jsonl")
    export_memory(src, "u", exp)
    # destination already has the first two links (export from a 2-link store)
    dst = _src_from_prefix(tmp_path, src, prefix=2)
    import_memory(dst, exp)
    seqs = sorted(ep.seq for ep in _outcomes(dst))
    assert seqs == [1, 2, 3], "the third link must extend, not branch"
    assert len({ep.id for ep in _outcomes(dst)}) == 3


def _src_from_prefix(tmp_path, full_store, prefix):
    """A store holding the first `prefix` links of full_store's chain, by importing
    a truncated export."""
    outs = sorted(_outcomes(full_store), key=lambda e: e.seq)[:prefix]
    recs = [("edge", _edge("e1"))] + [("episode", ep) for ep in outs]
    p = str(tmp_path / "pfx.jsonl")
    # seed with the SAME materialised origin the real v4 export of full_store carries, so
    # the incoming suffix extends idempotently rather than looking like a different source
    _write_export(p, recs, version=FORMAT_VERSION, origin=full_store.local_origin())
    dst = SqliteStore(str(tmp_path / "pfx.db"))
    import_memory(dst, p)
    return dst


# --- H5: malformed OR raced import refuses, persisting NOTHING --------------

def _valid_two_link():
    return [("edge", _edge("e1")),
            ("episode", _outcome(seq=1, oid="r")),
            ("episode", _outcome(seq=2, oid="c", supersedes="r",
                                 author=EvidenceAuthor.USER, outcome=Outcome.CONFIRMED))]


def _case_branch():
    recs = _valid_two_link()
    recs.append(("episode", _outcome(seq=2, oid="c2", supersedes="r",
                                     author=EvidenceAuthor.USER,
                                     outcome=Outcome.CONFIRMED)))
    return recs


def _case_cycle():
    return [("edge", _edge("e1")),
            ("episode", _outcome(seq=1, oid="r", supersedes="c")),
            ("episode", _outcome(seq=2, oid="c", supersedes="r"))]


def _case_missing_parent():
    return [("edge", _edge("e1")),
            ("episode", _outcome(seq=2, oid="c", supersedes="gone"))]


def _case_cross_chain_link():
    # child in run-1 supersedes a link that belongs to a different evidence_ref
    return [("edge", _edge("e1")),
            ("episode", _outcome(seq=1, oid="r1", evref="run-1")),
            ("episode", _outcome(seq=1, oid="r2", evref="run-2")),
            ("episode", _outcome(seq=2, oid="c", evref="run-1", supersedes="r2"))]


def _case_non_increasing_seq():
    return [("edge", _edge("e1")),
            ("episode", _outcome(seq=1, oid="r")),
            ("episode", _outcome(seq=1, oid="c", supersedes="r"))]


def _case_no_root():
    return [("edge", _edge("e1")),
            ("episode", _outcome(seq=2, oid="a", supersedes="b")),
            ("episode", _outcome(seq=3, oid="b", supersedes="a"))]


def _case_two_leaves():
    # root with two independent children handled by branch; here: two disjoint roots
    return [("edge", _edge("e1")),
            ("episode", _outcome(seq=1, oid="r")),
            ("episode", _outcome(seq=1, oid="r2"))]


def _case_non_1_root():
    return [("edge", _edge("e1")),
            ("episode", _outcome(seq=7, oid="r"))]


def _case_seq_gap():
    return [("edge", _edge("e1")),
            ("episode", _outcome(seq=1, oid="r")),
            ("episode", _outcome(seq=3, oid="c", supersedes="r"))]


@pytest.mark.parametrize("builder", [
    _case_branch, _case_cycle, _case_missing_parent, _case_cross_chain_link,
    _case_non_increasing_seq, _case_no_root, _case_two_leaves, _case_non_1_root,
    _case_seq_gap,
], ids=lambda b: b.__name__)
def test_malformed_import_refuses_atomically(tmp_path, builder):
    exp = str(tmp_path / "e.jsonl")
    _write_export(exp, builder())
    dst = SqliteStore(str(tmp_path / "dst.db"))
    with pytest.raises(ValueError):
        import_memory(dst, exp)
    # H5: NOTHING persisted — not the valid edge, not any chain prefix
    assert _outcomes(dst) == []
    assert dst.edges("u", active_only=False) == []


def test_competing_destination_root_refuses(tmp_path):
    dst = _src_with_chain(str(tmp_path / "dst.db"), links=1)  # dest root on (e1,run-1)
    incoming = [("edge", _edge("e1")), ("episode", _outcome(seq=1, oid="other"))]
    exp = str(tmp_path / "e.jsonl")
    _write_export(exp, incoming)
    n_before = len(_outcomes(dst))
    with pytest.raises(ValueError):
        import_memory(dst, exp)
    assert len(_outcomes(dst)) == n_before   # unchanged


def test_divergent_suffix_refuses(tmp_path):
    # destination root R (head R). Incoming: R (equal) + child C superseding R.
    # Then move the destination head to B first, so C no longer extends the head.
    dst = _src_with_chain(str(tmp_path / "dst.db"), links=1)
    root = _outcomes(dst)[0]
    # export a divergent chain: same root record + a child hanging off it
    child = _outcome(seq=2, oid="c", supersedes=root.id,
                     author=EvidenceAuthor.USER, outcome=Outcome.CONFIRMED)
    root_rec = Episode.model_validate(root.model_dump())
    exp = str(tmp_path / "e.jsonl")
    _write_export(exp, [("edge", _edge("e1")),
                        ("episode", root_rec), ("episode", child)])
    # move the real head forward so the incoming child would branch
    dst.append_outcome_if_head("u", "e1", "run-1", root.id,
                               OutcomeJudgmentDraft(author=EvidenceAuthor.USER,
                                                    event_timestamp="2026-02-02",
                                                    outcome=Outcome.CONFIRMED,
                                                    summary="B"))
    with pytest.raises(ValueError):
        import_memory(dst, exp)
    # single leaf: the real append won; the import branch never landed
    outs = _outcomes(dst, key=("e1", "run-1"))
    referenced = {o.supersedes_episode for o in outs}
    leaves = [o for o in outs if o.id not in referenced]
    assert len(leaves) == 1


def test_lost_race_on_chain_B_does_not_leave_chain_A_persisted(tmp_path):
    # One plan spans two chains: "chain A" = a NEW edge e2 with its own outcome root,
    # "chain B" = an extension of e1's existing chain. A concurrent append moves e1's
    # head so chain B loses its race — the WHOLE atomic plan must refuse, so chain A
    # (e2) is NEVER left persisted (specs/0009 §4c/H5, round-5 finding 1).
    s = _src_with_chain(str(tmp_path / "s.db"), links=1)
    root = _outcomes(s)[0]
    e2 = _edge("e2")
    e1_ext = _outcome(seq=2, oid="e1c", supersedes=root.id,
                      author=EvidenceAuthor.USER, outcome=Outcome.CONFIRMED)
    e2_root = _outcome(seq=1, oid="e2r", eid="e2", evref="run-2")
    plan = {"edges": [e2], "episodes": [e1_ext, e2_root]}
    expected = {
        "edge_ids": {"e2": False, "e1": True},
        "episode_records": {"e1c": None, "e2r": None},
        "chain_heads": {("e1", "run-1"): root.id, ("e2", "run-2"): None},
    }
    # concurrent append moves e1's head
    s.append_outcome_if_head("u", "e1", "run-1", root.id,
                             OutcomeJudgmentDraft(author=EvidenceAuthor.USER,
                                                  event_timestamp="2026-03-03",
                                                  outcome=Outcome.CONFIRMED,
                                                  summary="raced"))
    result = s.commit_outcome_import_plan("u", plan, expected)
    assert result is DESTINATION_CHANGED
    # nothing from the plan persisted
    assert "e2" not in {e.id for e in s.edges("u", active_only=False)}
    assert _outcomes(s, key=("e2", "run-2")) == []
    assert "e1c" not in {ep.id for ep in _outcomes(s)}


def test_import_racing_a_concurrent_append_never_branches(tmp_path):
    # A store subclass that fires one concurrent append the first time the import
    # commit runs, forcing the DESTINATION_CHANGED path — the chain must not branch.
    class RacingStore(SqliteStore):
        _raced = False

        def commit_outcome_import_plan(self, user_id, plan, expected):
            if not self._raced:
                self._raced = True
                head = self._chain_head("u", "e1", "run-1")
                self.append_outcome_if_head(
                    "u", "e1", "run-1", head.id if head else None,
                    OutcomeJudgmentDraft(author=EvidenceAuthor.USER,
                                         event_timestamp="2026-04-04",
                                         outcome=Outcome.CONFIRMED, summary="B"))
            return super().commit_outcome_import_plan(user_id, plan, expected)

    dst = RacingStore(str(tmp_path / "dst.db"))
    dst.add_edge(_edge("e1"))
    root = dst.append_outcome_if_head(
        "u", "e1", "run-1", None,
        OutcomeJudgmentDraft(author=EvidenceAuthor.SYSTEM,
                             event_timestamp="2026-01-01",
                             outcome=Outcome.CONCURRED, summary="root"))
    # incoming: the same root (idempotent) + a child C extending it
    child = _outcome(seq=2, oid="C", supersedes=root.id,
                     author=EvidenceAuthor.USER, outcome=Outcome.CONFIRMED)
    root_rec = Episode.model_validate(root.model_dump())
    exp = str(tmp_path / "e.jsonl")
    _write_export(exp, [("edge", _edge("e1")),
                        ("episode", root_rec), ("episode", child)])
    # the import refuses (C no longer extends the moved head) — the essential
    # guarantee is only that the chain never branches.
    with pytest.raises(ValueError):
        import_memory(dst, exp)
    outs = _outcomes(dst, key=("e1", "run-1"))
    referenced = {o.supersedes_episode for o in outs}
    leaves = [o for o in outs if o.id not in referenced]
    assert len(leaves) == 1, "the chain branched under a race"


# --- H12: on-disk v2→v3 migration is honest + refuses duplicates ------------

def _v2_store_with_legacy_outcome(path, *, duplicate=False):
    """A stamped v2 store holding legacy outcome episode(s) written the pre-0009
    way — no seq / supersedes_episode / judgment_time_known."""
    import sqlite3
    conn = sqlite3.connect(path)
    for o in SCHEMA_V2:
        conn.execute(o.ddl)
    legacy = {
        "id": "leg-1", "user_id": "u", "date": "2026-05-05",
        "summary": "legacy use", "kind": "outcome", "edge_id": "e1",
        "outcome": "concurred",
        "provenance": {"source_type": "inferred",
                       "author_of_evidence": "system", "evidence_ref": "run-1"}}
    conn.execute("INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                 ("leg-1", "u", "2026-05-05", json.dumps(legacy)))
    if duplicate:
        dup = dict(legacy, id="leg-2", summary="legacy use 2")
        conn.execute("INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)",
                     ("leg-2", "u", "2026-05-05", json.dumps(dup)))
    conn.execute("PRAGMA user_version = 2")
    conn.commit()
    conn.close()


def test_legacy_outcome_becomes_root_with_unknown_judgment_time(tmp_path):
    p = str(tmp_path / "legacy.db")
    _v2_store_with_legacy_outcome(p)
    migrate_store(p)
    s = SqliteStore(p)
    outs = _outcomes(s)
    assert len(outs) == 1
    root = outs[0]
    assert root.seq == 1 and root.supersedes_episode is None
    assert root.judgment_time_known is False
    assert root.date == "2026-05-05", "the use date must NOT be relabelled"


def test_migration_refuses_duplicate_chain_identity(tmp_path):
    p = str(tmp_path / "dup.db")
    _v2_store_with_legacy_outcome(p, duplicate=True)
    with pytest.raises(DuplicateOutcomeChainError):
        migrate_store(p)
    # nothing partially converted: the store is still at its prior version and the
    # legacy rows are untouched (no seq stamped)
    import sqlite3
    conn = sqlite3.connect(p)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
    for (blob,) in conn.execute("SELECT json FROM episodes"):
        assert json.loads(blob).get("seq") is None
    conn.close()


# --- H13: legacy portable import gets the same honest conversion ------------

def test_legacy_portable_outcome_import(tmp_path):
    # a FORMAT_VERSION-2 export whose outcome record carries none of the v3 fields
    legacy_ep = {
        "id": "leg-1", "user_id": "u", "date": "2026-06-06", "summary": "legacy",
        "kind": "outcome", "edge_id": "e1", "outcome": "concurred",
        "provenance": {"source_type": "inferred",
                       "author_of_evidence": "system", "evidence_ref": "run-1"}}
    exp = str(tmp_path / "v2.jsonl")
    with open(exp, "w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": 2,
                            "user_id": "u", "exported_at": "x"}) + "\n")
        f.write(json.dumps({"record": "edge",
                            **json.loads(_edge("e1").model_dump_json())}) + "\n")
        f.write(json.dumps({"record": "episode", **legacy_ep}) + "\n")
    dst = SqliteStore(str(tmp_path / "dst.db"))
    import_memory(dst, exp)
    root = _outcomes(dst)[0]
    assert root.seq == 1 and root.supersedes_episode is None
    assert root.judgment_time_known is False


def test_v2_duplicate_identity_import_refuses(tmp_path):
    base = {"user_id": "u", "date": "2026-06-06", "summary": "legacy",
            "kind": "outcome", "edge_id": "e1", "outcome": "concurred",
            "provenance": {"source_type": "inferred",
                           "author_of_evidence": "system", "evidence_ref": "run-1"}}
    exp = str(tmp_path / "v2.jsonl")
    with open(exp, "w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": 2,
                            "user_id": "u", "exported_at": "x"}) + "\n")
        f.write(json.dumps({"record": "edge",
                            **json.loads(_edge("e1").model_dump_json())}) + "\n")
        f.write(json.dumps({"record": "episode", "id": "a", **base}) + "\n")
        f.write(json.dumps({"record": "episode", "id": "b", **base}) + "\n")
    dst = SqliteStore(str(tmp_path / "dst.db"))
    with pytest.raises(ValueError, match="refuse rather than branch"):
        import_memory(dst, exp)
    assert _outcomes(dst) == []


def test_v3_import_requires_explicit_judgment_time_known(tmp_path):
    # a v3 outcome record that omits judgment_time_known must be refused, not
    # silently read as "known"
    ep = {"id": "x", "user_id": "u", "date": "2026-06-06", "summary": "s",
          "kind": "outcome", "edge_id": "e1", "outcome": "concurred",
          "seq": 1, "supersedes_episode": None,
          "provenance": {"source_type": "inferred",
                         "author_of_evidence": "system", "evidence_ref": "run-1"}}
    exp = str(tmp_path / "v3.jsonl")
    with open(exp, "w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": 3,
                            "user_id": "u", "exported_at": "x"}) + "\n")
        f.write(json.dumps({"record": "edge",
                            **json.loads(_edge("e1").model_dump_json())}) + "\n")
        f.write(json.dumps({"record": "episode", **ep}) + "\n")
    dst = SqliteStore(str(tmp_path / "dst.db"))
    with pytest.raises(ValueError, match="judgment_time_known"):
        import_memory(dst, exp)


# --- H14: outcome-chain state cannot bypass the CAS/import path -------------

def test_generic_add_of_a_caller_seq_outcome_is_refused(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    with pytest.raises(ValueError, match="H14"):
        s.add_episode(_outcome(seq=1, oid="x"))


def test_generic_add_sibling_of_a_head_is_refused(tmp_path):
    s = _src_with_chain(str(tmp_path / "s.db"), links=1)
    root = _outcomes(s)[0]
    sibling = _outcome(seq=2, oid="sib", supersedes=root.id,
                       author=EvidenceAuthor.USER, outcome=Outcome.CONFIRMED)
    with pytest.raises(ValueError, match="H14"):
        s.add_episode(sibling)


def test_generic_delete_of_an_outcome_link_is_refused(tmp_path):
    s = _src_with_chain(str(tmp_path / "s.db"), links=1)
    root = _outcomes(s)[0]
    with pytest.raises(ValueError, match="H14"):
        s.delete_episode(root.id)
    assert _outcomes(s), "the link must still be there"


def test_insert_or_replace_of_an_existing_outcome_id_is_refused(tmp_path):
    s = _src_with_chain(str(tmp_path / "s.db"), links=1)
    root = _outcomes(s)[0]
    # try to overwrite the existing outcome id with a forged record via the generic
    # replace-capable mutator — H14 refuses even a same-id "update"
    forged = _outcome(seq=1, oid=root.id, author=EvidenceAuthor.USER,
                      outcome=Outcome.CORRECTED)
    with pytest.raises(ValueError, match="H14"):
        s.add_episode(forged)
    assert _outcomes(s)[0].outcome is Outcome.CONCURRED, "the original stands"
