"""specs/0037 §6 — every invariant's node, by the name the table cites, plus
the §6a acceptance corpus consumed WHOLE (972 cells, never sampled), the
named cells, and the frozen-text derivation for the recognition rule.

Oracles, frozen before any implementation line and cited by digest in the
implementing commit: `tests/eval/procedural_describe/MANIFEST.json` (the 972
cells, generated from §4a-ii's ordered predicate) and
`tests/eval/procedural_describe/FROZEN_TEXTS.json` (research, 2026-09-08: the
must-match procedure texts the rule's opener and step-marker sets are DERIVED
from at test time). The pin tests live in `test_0037_corpus_pin.py`.
"""
from __future__ import annotations

import ast
import collections
import json
import pathlib
import re
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from veracium import Memory, MemoryConfig
from veracium import gate, portability
from veracium.ingest import _disclosure_for
from veracium.procedures import (DescribeResult, ProcedureDescription, Withheld,
                                 matches_executable_detail)
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, Episode, EvidenceAuthor,
                             EvidenceContext, Provenance, Relation, is_procedural, utcnow)
from veracium.scope import Identity, validate_policy
from veracium.store.sqlite import SqliteStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
CORPUS = ROOT / "tests" / "eval" / "procedural_describe" / "MANIFEST.json"
TEXTS = ROOT / "tests" / "eval" / "procedural_describe" / "FROZEN_TEXTS.json"
U = "u"
NOW = utcnow()
D = timedelta(days=1)
PROC = "follows_procedure"
GONE = "follows_ritual"          # a procedural relation ABSENT from the active registry


def _llm(*a, **k):
    return json.dumps({"triples": [], "episode": "we talked", "instructions": []})


def _cfg(tmp_path, name="m.db", *, xv=False, cap=40, relations=None):
    kw = {} if relations is None else {"relations": relations}
    return MemoryConfig(db_path=str(tmp_path / name), wiki_recompile_after_writes=0,
                        scope_groups={}, cross_scope_visible=xv, max_subgraph_edges=cap, **kw)


def _mem(tmp_path, name="m.db", *, xv=False, cap=40, store=None, relations=None):
    return Memory(llm=_llm, store=store, config=_cfg(tmp_path, name, xv=xv, cap=cap,
                                                     relations=relations))


def _principal(store, xv: bool):
    return (Identity(origin=None, source_id="mb-a"),
            validate_policy({}, cross_scope_visible=xv, local_origin=store.local_origin()))


def _edge(obj, *, relation=PROC, author=EvidenceAuthor.USER, basis=None, record_kind=None,
          source="mb-a", valid_from=None, invalidated_at=None, eid=None, note="",
          disclosure=None):
    valid_from = valid_from or NOW - 10 * D
    prov = Provenance(author_of_evidence=author, evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                      disclosure=disclosure or _disclosure_for(author, relation, None),
                      source_id=source, observed_at=valid_from, basis=basis,
                      record_kind=record_kind)
    return Edge(id=eid or f"e-{uuid.uuid4().hex[:12]}", user_id=U, subject="user",
                relation=relation, object=obj, note=note, valid_from=valid_from,
                invalidated_at=invalidated_at,
                invalidation_reason="superseded" if invalidated_at else None,
                provenance=prov)


def _record(mem, summary="Rotate service credentials every quarter.", *, basis="stated",
            author=EvidenceAuthor.USER, derived=None, **kw):
    ctx = (EvidenceContext.direct(basis=basis) if derived is None
           else EvidenceContext.derived(derived, basis=basis))
    return mem.record_procedure(U, summary, author=author, context=ctx, **kw)


def _texts():
    return json.loads(TEXTS.read_text(encoding="utf-8"))


def _snapshot(store):
    return [r[0] for r in store._conn.execute(
        "SELECT json FROM edges ORDER BY id").fetchall()], store._conn.execute(
        "SELECT COUNT(*) FROM episodes").fetchone()[0]


# ------------------------------------------------------- the sibling's binding
def test_the_frozen_texts_are_bound_by_digest_from_the_spec_and_the_corpus():
    """The frozen texts are a SIBLING of the corpus (amendment 7): the file
    hashes to the digest §6a quotes AND to the digest the manifest records —
    data to data, both directions, so a text edited without its two lines
    cannot pass, and a spec whose sibling is unbound cannot either."""
    import hashlib
    digest = hashlib.sha256(TEXTS.read_bytes()).hexdigest()
    spec = (ROOT / "specs" / "0037-procedural-basis.md").read_text(encoding="utf-8")
    assert digest in spec, "§6a does not quote the sibling's digest"
    assert digest in CORPUS.read_text(encoding="utf-8"), "the manifest does not record the sibling's digest"
    t = _texts()
    assert t["counts"] == {"must_match": len(t["must_match"]),
                           "must_match_imperative": sum(1 for x in t["must_match"] if x.get("opener")),
                           "must_match_step_marker": sum(1 for x in t["must_match"] if not x.get("opener")),
                           "paraphrased_known_pass": len(t["paraphrased_known_pass"]),
                           "plain_declarative": len(t["plain_declarative"])}


# ------------------------------------------------------ V-DECLARATIVE-UNCHANGED
def test_every_pre_existing_edge_is_declarative_and_unchanged(tmp_path):
    """A declarative Provenance serializes to the pre-feature 8 keys with its
    three deliberate nulls — `record_kind`/`basis` ABSENT, not null — and the
    0029 pre-feature oracle (recall, context, export, MCP) replays
    byte-identically on this build; a procedural-free export stamps the
    pre-procedural version."""
    p = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev")
    d = json.loads(p.model_dump_json())
    assert list(d) == ["author_of_evidence", "evidence_ref", "observed_at", "disclosure",
                       "confidence", "derived_from", "source_id", "origin"]
    assert d["derived_from"] is None and d["source_id"] is None and d["origin"] is None
    assert "record_kind" not in p.model_dump() and "basis" not in p.model_dump()
    # every default-registry relation but the one procedural one is declarative
    assert [n for n, r in DEFAULT_RELATIONS.items() if r.relation_kind == "procedural"] == [PROC]
    # the 0029 pre-feature oracle — the same builder, the same fixed inputs
    import hashlib
    import importlib.util
    here = ROOT / "specs" / "evidence" / "0029" / "pre_feature_oracle"
    frozen = json.loads((here / "pre_feature_capture.json").read_text())
    spec = importlib.util.spec_from_file_location("oracle_0029", here / "generate_oracle.py")
    orc = importlib.util.module_from_spec(spec); spec.loader.exec_module(orc)
    store = orc.build_store(tmp_path / "oracle.db")
    try:
        got = orc.capture(store, tmp_path)
    finally:
        store.close()
    for surface in ("recall", "context", "export", "mcp"):
        assert got[surface] == frozen[surface], f"{surface} drifted from the pre-feature oracle"
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("Porto", relation="located_at"))
    out = tmp_path / "plain.jsonl"
    mem.export_memory(U, str(out))
    assert json.loads(out.read_text().splitlines()[0])["version"] == portability._PRE_AGREEMENT_VERSION


# ------------------------------------------------------------- V-KIND-STAMPED
def test_record_kind_is_stamped_at_write_and_read_from_the_record(tmp_path):
    """The stamp is the registry's declaration AT WRITE; every kind-dependent
    read reads the STAMP: reshaping the registry between write and read
    (reclassify the procedural relation declarative; drop another relation)
    moves no stored record's treatment; the read rule is stamp OR basis
    (a stripped basis moves nothing into a block); the conflict cell
    (None stamp WITH a basis) is `kind_conflict`, procedural by floor and
    COUNTED; the default serializer mutant would emit `"record_kind":null`."""
    mem = _mem(tmp_path)
    eid = _record(mem, "Credentials are rotated every quarter.", basis="stated")
    stored = next(e for e in mem.store.edges(U) if e.id == eid)
    assert stored.provenance.record_kind == "procedural" and stored.provenance.basis == "stated"
    assert '"record_kind":"procedural"' in stored.model_dump_json()
    # RESHAPE the registry: the procedural relation becomes declarative, and a
    # declarative one is dropped — nothing stored moves
    reshaped = {n: r for n, r in DEFAULT_RELATIONS.items() if n != "has_pet"}
    reshaped[PROC] = Relation(name=PROC, relation_kind="declarative", desc="x")
    mem2 = _mem(tmp_path, store=mem.store, relations=reshaped)
    mem2.store.add_edge(_edge("Ollie", relation="has_pet", eid="e-legacy-pet"))
    r = mem2.describe_procedures(U)
    assert r.total_describable == 1 and r.descriptions[0].edge_id == eid      # still procedural
    rc = mem2.recall(U, "rotate credentials pet ollie")
    assert eid not in {e.id for e in rc.edges} and "Ollie" in rc.context   # the legacy edge renders
    # a NEW write under the reshaped registry takes the NEW declaration: refused
    with pytest.raises(ValueError):
        _record(mem2, "Tag the release after CI passes on main.")
    # the read rule is stamp OR basis: strip the basis → still out of recall
    mem.store._conn.execute(
        "UPDATE edges SET json=json_remove(json, '$.provenance.basis') WHERE id=?", (eid,))
    mem.store._conn.commit()
    assert eid not in {e.id for e in mem.recall(U, "rotate credentials").edges}
    assert mem.describe_procedures(U).withheld == [Withheld(eid, "basis_unknown")]
    # the conflict cell: NO stamp, basis present — procedural by floor, counted
    tel = []
    mem.telemetry = type("T", (), {"record": lambda self, ev, f: tel.append((ev, f))})()
    mem.store.add_edge(_edge("Review dependency updates weekly.", basis="observed",
                             record_kind=None, eid="e-conflict"))
    r = mem.describe_procedures(U)
    assert Withheld("e-conflict", "kind_conflict") in r.withheld
    assert [f["kind_conflict"] for ev, f in tel if ev == "describe_procedures"][-1] == 1
    assert "e-conflict" not in {e.id for e in mem.recall(U, "review dependency").edges}


def test_the_four_state_table_matches_the_corpus_column(tmp_path):
    """The four stored states, in the field's own terms, produce the outcomes
    the corpus's `kind_state` column names — through a REAL Provenance."""
    for rk, basis, state in [(None, None, "declarative"), ("procedural", "stated", "procedural"),
                             ("procedural", None, "basis_unknown"), (None, "observed", "kind_conflict")]:
        p = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev",
                       record_kind=rk, basis=basis)
        assert p.procedural == (state != "declarative"), state


# ---------------------------------------------------------- V-PROVENANCE-AXES
def test_provenance_axes_are_independent(tmp_path):
    """Every cell of author × {direct, derived(X)} × basis is writable, each
    stored field equals its own input, disclosure is the three-axis rule,
    and no argument substitutes for another (author=SYSTEM with direct())."""
    mem = _mem(tmp_path)
    contexts = [("direct", None)] + [("derived", x) for x in EvidenceAuthor]
    n = 0
    for author in EvidenceAuthor:
        for kind, x in contexts:
            for basis in ("stated", "observed"):
                ctx = (EvidenceContext.direct(basis=basis) if kind == "direct"
                       else EvidenceContext.derived(x, basis=basis))
                eid = mem.record_procedure(U, f"Rotate credentials {n}.", author=author, context=ctx)
                e = next(e for e in mem.store.edges(U, active_only=False) if e.id == eid)
                p = e.provenance
                assert p.author_of_evidence == author and p.derived_from == x and p.basis == basis
                assert p.record_kind == "procedural"
                assert p.disclosure == _disclosure_for(author, PROC, x)
                n += 1
    assert n == len(EvidenceAuthor) * (1 + len(EvidenceAuthor)) * 2
    # the mutant's cell: SYSTEM-authored with direct() is representable as such
    eid = mem.record_procedure(U, "Verify the backup restores before trusting it.",
                               author=EvidenceAuthor.SYSTEM, context=EvidenceContext.direct(basis="observed"))
    e = next(e for e in mem.store.edges(U) if e.id == eid)
    assert e.provenance.author_of_evidence is EvidenceAuthor.SYSTEM and e.provenance.derived_from is None


# ---------------------------------------------------------- V-ARGS-VALIDATED
def test_record_procedure_validates_every_argument_and_writes_nothing(tmp_path):
    mem = _mem(tmp_path)
    ok = dict(author=EvidenceAuthor.USER, context=EvidenceContext.direct(basis="stated"))
    before = _snapshot(mem.store)
    cases = [
        (TypeError, dict(summary=5)), (TypeError, dict(summary=True)),
        (ValueError, dict(summary="   ")), (ValueError, dict(summary="x" * 600)),
        (TypeError, dict(note=3)), (TypeError, dict(evidence_ref=1)), (TypeError, dict(source_id=[])),
        (TypeError, dict(author="user")), (TypeError, dict(context=None)),
        (TypeError, dict(context="direct")), (ValueError, dict(context=EvidenceContext.direct())),
        (ValueError, dict(when="2026-01-01")), (ValueError, dict(when=datetime(2026, 1, 1))),
        (TypeError, dict(when=1700000000)), (ValueError, dict(when=NOW + 3 * D)),
        (TypeError, dict(relation=7)), (ValueError, dict(relation="works_as")),
        (ValueError, dict(relation="no_such_relation")),
    ]
    for exc, kw in cases:
        args = {"summary": "Rotate service credentials every quarter.", **ok, **kw}
        summary = args.pop("summary")
        with pytest.raises(exc):
            mem.record_procedure(U, summary, **args)
        assert _snapshot(mem.store) == before, kw
    # "" for the optional strings is None; a valid call writes exactly one edge
    eid = mem.record_procedure(U, "  Rotate   service credentials.  ", note="", evidence_ref="",
                               source_id="", **ok)
    e = next(e for e in mem.store.edges(U) if e.id == eid)
    assert e.object == "Rotate service credentials." and e.note == "" and e.provenance.source_id is None
    assert e.provenance.evidence_ref == f"procedure:{eid}"


def test_describe_limit_and_query_are_validated(tmp_path):
    mem = _mem(tmp_path, cap=5)
    for bad in (0, -1, 6, True, 2.0, "3"):
        with pytest.raises((TypeError, ValueError)):
            mem.describe_procedures(U, limit=bad)
    with pytest.raises(TypeError):
        mem.describe_procedures(U, query=5)
    assert mem.describe_procedures(U, limit=5, query="  Rotate   KEYS ").query == "rotate keys"
    assert mem.describe_procedures(U, query="   ").query is None


# --------------------------------------------------------- V-EXTRACTOR-BLIND
# ------------------------------------------------------------ V-TWO-PRODUCERS
def test_the_two_producers_are_exactly_the_host_surface_and_the_quote_gated_extractor():
    """The sweep basis is 0029's own write-site registry, every site
    classified; `record_kind="procedural"` is written at exactly TWO src
    sites — `procedures.py` (the host's declared basis) and `ingest.py`
    (0037 v16 §4a-iii, the quote-gated extractor path, derived basis); the
    CLI carries no basis option."""
    from veracium.store.sqlite import EDGE_WRITE_SITE_RULINGS
    classified = {
        "_upsert_edge_row": "the choke point every writer uses — stamps nothing; refuses a same-id marker change",
        "confirm_edge": "rewrites json in place — passes the stored stamp/basis through the same-id guard",
        "_invalidate_edge_row": "flips active; touches no provenance",
        "_reinstate_edge_row": "flips active; touches no provenance",
        "_recompute_edge_row": "rewrites valid_from/observed_at/confidence; not the markers",
        "commit_outcome_import_plan": "the import commit — the default path refused every procedural record before it; restore admits only what this store wrote",
        "forget_user": "erasure",
    }
    assert set(EDGE_WRITE_SITE_RULINGS) == set(classified)
    def _stamps(path):                       # a CALL passing record_kind="procedural" (not prose)
        tree = ast.parse(path.read_text())
        return any(isinstance(n, ast.Call) and any(
            k.arg == "record_kind" and isinstance(k.value, ast.Constant) and k.value.value == "procedural"
            for k in n.keywords) for n in ast.walk(tree))
    stampers = sorted(p.relative_to(SRC).as_posix() for p in SRC.rglob("*.py") if _stamps(p))
    assert stampers == ["ingest.py", "procedures.py"], stampers
    assert "--basis" not in (SRC / "cli.py").read_text() and "basis" not in (SRC / "cli.py").read_text()


# ------------------------------ V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE / V-OLD-READER
def _export_lines(mem, path):
    mem.export_memory(U, str(path))
    lines = path.read_text().splitlines()
    return json.loads(lines[0]), [json.loads(l) for l in lines[1:]]


def _write_file(path, header, recs):
    path.write_text("\n".join([json.dumps(header)] + [json.dumps(r) for r in recs]) + "\n")


def test_default_import_refuses_procedural_records_on_any_signal(tmp_path):
    """The six §2c cells and the format-10 8-cell raw matrix: the signals are
    evaluated on the RAW record before normalization; the first firing
    signal is named; refusal is per record; declarative records import."""
    src = _mem(tmp_path, "src.db")
    eid = _record(src, "Rotate service credentials every quarter.", basis="stated")
    src.store.add_edge(_edge("Porto", relation="located_at", eid="e-decl"))
    header, recs = _export_lines(src, tmp_path / "e.jsonl")
    assert header["version"] == 11
    proc = next(r for r in recs if r["id"] == eid)
    host = dict(DEFAULT_RELATIONS)
    host["runs_playbook"] = Relation(name="runs_playbook", relation_kind="procedural", desc="p")

    def run(rec_mut, *, version=11, relations=None):
        r = json.loads(json.dumps(proc)); rec_mut(r)
        f = tmp_path / f"c-{uuid.uuid4().hex[:6]}.jsonl"
        _write_file(f, {**header, "version": version}, [r, next(x for x in recs if x["id"] == "e-decl")])
        dst = _mem(tmp_path, f"d-{uuid.uuid4().hex[:6]}.db", relations=relations)
        rep = dst.import_memory(str(f))
        got = {e.id for e in dst.store.edges(U, active_only=False)}
        return rep, got

    def strip(k):
        def f(r): r["provenance"].pop(k, None)
        return f
    def both(r): r["provenance"].pop("record_kind"); r["provenance"].pop("basis")
    def relation(name):
        def f(r): r["relation"] = name; both(r)
        return f
    # the six cells
    for mut, signal in [(strip("record_kind"), "basis"), (strip("basis"), "stamp"),
                        (both, "registry"), (lambda r: None, "stamp")]:
        rep, got = run(mut)
        assert rep["procedural_refused"] == 1 and rep["procedural_refusals"][0]["signal"] == signal
        assert got == {"e-decl"}, signal
    rep, got = run(relation("no_such_relation"))        # both stripped, unknown relation: declarative
    assert rep["procedural_refused"] == 0 and got == {eid, "e-decl"}
    def foreign_stamp_declarative(r): r["relation"] = "located_at"; r["provenance"].pop("basis")
    rep, got = run(foreign_stamp_declarative)
    assert rep["procedural_refusals"][0]["signal"] == "stamp" and got == {"e-decl"}
    # the format-10 8-cell matrix, raw marker × receiving relation
    for marker, mut in [("stamp", strip("basis")), ("basis", strip("record_kind"))]:
        for rel in (PROC, "located_at", "no_such_relation"):
            def m(r, mut=mut, rel=rel): mut(r); r["relation"] = rel
            rep, got = run(m, version=10)
            assert rep["procedural_refusals"][0]["signal"] == marker and rep["procedural_refusals"][0]["raw"] is True, (marker, rel)
            assert got == {"e-decl"}
    rep, got = run(relation(PROC), version=10)
    assert rep["procedural_refusals"][0]["signal"] == "registry" and got == {"e-decl"}
    rep, got = run(relation("located_at"), version=10)
    assert rep["procedural_refused"] == 0 and got == {eid, "e-decl"}
    # the registry signal fires on the RECEIVING host's kinds
    rep, got = run(relation("runs_playbook"), relations=host)
    assert rep["procedural_refusals"][0]["signal"] == "registry"
    # no foreign basis reaches a stored record on the default path
    for dst in tmp_path.glob("d-*.db"):
        s = SqliteStore(str(dst)); assert all(not is_procedural(e) for e in s.edges(U, active_only=False)); s.close()


def test_restore_round_trips_procedural_records_with_basis(tmp_path):
    src = _mem(tmp_path, "src.db")
    eid = _record(src, "Rotate service credentials every quarter.", basis="observed")
    src.store.add_edge(_edge("Porto", relation="located_at", eid="e-decl"))
    header, recs = _export_lines(src, tmp_path / "e.jsonl")
    dst = _mem(tmp_path, "dst.db")
    rep = dst.import_memory(str(tmp_path / "e.jsonl"), restore=True)
    assert rep["procedural_refused"] == 0 and rep["edges"] == 2
    dst_e = next(e for e in dst.store.edges(U) if e.id == eid)
    assert dst_e.provenance.basis == "observed" and dst_e.provenance.record_kind == "procedural"
    # a store's OWN backup restores byte-identically: delete the row, restore it
    src_row = src.store._conn.execute("SELECT json FROM edges WHERE id=?", (eid,)).fetchone()[0]
    src.store._conn.execute("DELETE FROM edges WHERE id=?", (eid,)); src.store._conn.commit()
    rep = src.import_memory(str(tmp_path / "e.jsonl"), restore=True)
    assert rep["procedural_refused"] == 0
    assert src.store._conn.execute("SELECT json FROM edges WHERE id=?", (eid,)).fetchone()[0] == src_row
    # both absence dimensions are MALFORMED on restore, per record; the registry signal is silent
    proc = next(r for r in recs if r["id"] == eid)
    for k in ("record_kind", "basis"):
        r = json.loads(json.dumps(proc)); r["provenance"].pop(k); r["id"] = f"e-mal-{k}"
        f = tmp_path / f"m-{k}.jsonl"; _write_file(f, header, [r])
        d2 = _mem(tmp_path, f"m-{k}.db")
        rep = d2.import_memory(str(f), restore=True)
        assert rep["procedural_refused"] == 1 and rep["procedural_refusals"][0]["refusal"] == "malformed_procedural_marker"
    r = json.loads(json.dumps(proc)); r["provenance"]["basis"] = "guessed"; r["id"] = "e-mal-dom"
    f = tmp_path / "m-dom.jsonl"; _write_file(f, header, [r])
    assert _mem(tmp_path, "m-dom.db").import_memory(str(f), restore=True)["procedural_refused"] == 1
    reshaped = {n: r for n, r in DEFAULT_RELATIONS.items() if n != PROC}
    d3 = _mem(tmp_path, "reshaped.db", relations=reshaped)
    assert d3.import_memory(str(tmp_path / "e.jsonl"), restore=True)["procedural_refused"] == 0


def test_old_reader_refuses_a_procedural_export(tmp_path, monkeypatch):
    src = _mem(tmp_path, "src.db")
    _record(src, "Rotate service credentials every quarter.")
    src.store.add_edge(_edge("Porto", relation="located_at"))
    f = tmp_path / "p.jsonl"
    src.export_memory(U, str(f))
    assert json.loads(f.read_text().splitlines()[0])["version"] == 11
    monkeypatch.setattr(portability, "FORMAT_VERSION", 10)         # the shipped reader, held at 10
    dst = _mem(tmp_path, "old.db")
    with pytest.raises(ValueError, match="newer than this Veracium understands"):
        dst.import_memory(str(f))
    assert dst.store.edges(U, active_only=False) == []
    monkeypatch.undo()
    plain = _mem(tmp_path, "plain.db")
    plain.store.add_edge(_edge("Porto", relation="located_at"))
    g = tmp_path / "d.jsonl"; plain.export_memory(U, str(g))
    assert json.loads(g.read_text().splitlines()[0])["version"] < 11
    monkeypatch.setattr(portability, "FORMAT_VERSION", 10)
    assert _mem(tmp_path, "old2.db").import_memory(str(g))["edges"] == 1


# ------------------------------------------------ V-CORPUS-ROWS-IN-DOMAIN (real Provenance)
def test_every_corpus_row_constructs_a_real_provenance():
    cells = json.loads(CORPUS.read_text(encoding="utf-8"))["cells"]
    for c in cells:
        p = Provenance(author_of_evidence=EvidenceAuthor[c["author"]], evidence_ref="ev",
                       record_kind=c["record_kind"], basis=c["basis"])
        assert p.procedural == (c["kind_state"] != "declarative")


# ------------------------------------------------- V-OUT-OF-PATH / V-RENDER-SITES
def test_procedural_records_never_reach_model_context(tmp_path):
    """Every author × disclosure × basis cell, enumerated from the enums, is
    excluded at the choke point in NEITHER block, whatever the registry."""
    mem = _mem(tmp_path)
    for author in EvidenceAuthor:
        for disc in Disclosure:
            for basis in ("stated", "observed", None):
                for rk in ("procedural", None):
                    if basis is None and rk is None:
                        continue
                    e = _edge(f"Rotate {uuid.uuid4().hex[:4]}.", author=author, basis=basis,
                              record_kind=rk, disclosure=disc)
                    mem.store.add_edge(e)
                    g, u = gate.partition([e], [])
                    assert g == "" and u == ""
    for e in mem.store.edges(U, active_only=False):
        assert is_procedural(e)
    rc = mem.recall(U, "rotate")
    assert rc.edges == [] and "Rotate" not in rc.context
    assert "Rotate" not in mem.recall(U, None).context
    assert gate.PROCEDURAL_OUT_OF_SCOPE == "procedural_out_of_scope"


def test_assertable_is_untouched():
    src = (SRC / "schema.py").read_text()
    body = src[src.index("    def assertable(self) -> bool:"):]
    body = body[:body.index("\n\n\n")]
    assert ("return (self.active and not self.quarantined and not self.use_only\n"
            "                and self.valid_now)") in body
    assert "procedural" not in body and "basis" not in body


def test_every_model_context_site_excludes_by_kind():
    """DERIVED by sweep: every src module that renders records into model
    context (a `render_edges(`/`partition(`/`partition_parts(` call, or a
    store edge read feeding a prompt) reaches the one exclusion, directly or
    through its selection; a site absent from the classification fails."""
    reach = {
        "gate.py": "direct — partition_parts calls exclude_procedural",
        "__init__.py": "direct in _recall; selection through graph._lexical_scored",
        "graph.py": "direct — _lexical_scored skips is_procedural before scoring",
        "proactive.py": "direct — assemble calls exclude_procedural",
        "compile.py": "direct — compile_wiki's input calls exclude_procedural",
        "asof/recall.py": "through graph._lexical_scored (candidates are re-screened in its loop)",
        "introspect.py": "NOT model context — the operator's diagnostic listing renders every record by design (§4a: 'still in introspect')",
        "budgets.py": "a clamp over a render callable; it renders nothing of its own",
        "lifecycle.py": "operator maintenance; not model context",
    }
    sites = sorted(p.relative_to(SRC).as_posix() for p in SRC.rglob("*.py")
                   if re.search(r"(?<![.\w])(render_edges|partition_parts|partition)\(", p.read_text())
                   and p.name != "graph.py" or p.name in ("graph.py", "compile.py", "proactive.py"))
    unclassified = [s for s in sites if s not in reach]
    assert not unclassified, unclassified
    for mod, why in reach.items():
        text = (SRC / mod).read_text()
        if why.startswith("direct"):
            assert "exclude_procedural" in text or "is_procedural" in text, mod


# ---------------------------------------------- V-BASIS-POSITIVE / CLOSED / SCOPE / ABSENCE
def test_procedural_ingest_requires_a_declared_basis(tmp_path):
    mem = _mem(tmp_path)
    before = _snapshot(mem.store)
    with pytest.raises(ValueError, match="basis"):
        mem.record_procedure(U, "Rotate keys.", author=EvidenceAuthor.USER,
                             context=EvidenceContext.direct())
    with pytest.raises(ValueError):
        mem.record_procedure(U, "Rotate keys.", author=EvidenceAuthor.USER,
                             context=EvidenceContext.derived(EvidenceAuthor.SYSTEM))
    assert _snapshot(mem.store) == before


def test_basis_domain_is_closed_and_refuses_at_construction(tmp_path):
    for bad in ("guessed", "", "Stated", 1, True, [], {}, {"stated"}, object()):
        with pytest.raises((TypeError, ValueError)):
            EvidenceContext.direct(basis=bad)
        with pytest.raises((TypeError, ValueError)):
            EvidenceContext.derived(EvidenceAuthor.USER, basis=bad)
    assert EvidenceContext.direct(basis="stated").basis == "stated"
    assert EvidenceContext.direct() != EvidenceContext.direct(basis="stated")
    with pytest.raises(AttributeError):
        EvidenceContext.direct(basis="stated").basis = "observed"


def test_basis_on_a_declarative_event_is_refused(tmp_path):
    mem = _mem(tmp_path)
    before = _snapshot(mem.store)
    for ctx in (EvidenceContext.direct(basis="stated"),
                EvidenceContext.derived(EvidenceAuthor.SYSTEM, basis="observed")):
        with pytest.raises(ValueError, match="not applicable"):
            mem.remember(U, "I live in Porto.", context=ctx)
    assert _snapshot(mem.store) == before


def test_procedural_record_without_basis_is_a_named_non_allow(tmp_path):
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("Rotate service credentials every quarter.", record_kind="procedural",
                             basis=None, eid="e-nobasis"))
    r = mem.describe_procedures(U)
    assert r.descriptions == [] and r.withheld == [Withheld("e-nobasis", "basis_unknown")]
    assert "e-nobasis" not in {e.id for e in mem.recall(U, "rotate").edges}


# ------------------------------------------- V-BASIS-CAP-ONLY / V-BASIS-IMMUTABLE
def test_basis_can_only_subtract(tmp_path):
    """Same-id replace, absorption (the whole-set minimum), confirm and
    reinforcement never move a record from `observed` to `stated`."""
    from veracium.graph import _min_basis
    assert _min_basis("stated", "observed") == "observed" == _min_basis("observed", "stated")
    assert _min_basis("stated", "stated") == "stated" and _min_basis(None, None) is None
    assert _min_basis(None, "observed") == "observed"
    mem = _mem(tmp_path)
    eid = _record(mem, "Rotate service credentials every quarter.", basis="observed")
    e = next(x for x in mem.store.edges(U) if x.id == eid)
    with pytest.raises(ValueError, match="immutable"):
        mem.store.add_edge(e.model_copy(update={"provenance": e.provenance.model_copy(update={"basis": "stated"})}))
    assert next(x for x in mem.store.edges(U) if x.id == eid).provenance.basis == "observed"
    # absorption: a SUBSUMING restatement (one extra token, in order) declared
    # `stated` absorbs the `observed` prior — the survivor carries the minimum
    prior = _record(mem, "Credentials are rotated quarterly.", basis="observed")
    eid2 = _record(mem, "Service credentials are rotated quarterly.", basis="stated")
    rows = {x.id: x for x in mem.store.edges(U, active_only=False)}
    assert rows[prior].invalidation_reason == "absorbed_duplicate" and rows[eid2].active
    assert rows[eid2].provenance.basis == "observed", [(i, x.provenance.basis, x.active) for i, x in rows.items()]


def test_stored_basis_is_immutable(tmp_path):
    mem = _mem(tmp_path)
    eid = _record(mem, "Rotate service credentials every quarter.", basis="stated")
    e = next(x for x in mem.store.edges(U) if x.id == eid)
    for update in ({"basis": "observed"}, {"basis": None}, {"record_kind": None}):
        with pytest.raises(ValueError, match="immutable"):
            mem.store.add_edge(e.model_copy(update={"provenance": e.provenance.model_copy(update=update)}))
    assert next(x for x in mem.store.edges(U) if x.id == eid).provenance.basis == "stated"


# --------------------------------------------- V-DESCRIBE-CONJUNCTION / RESULT-SCHEMA / ORDER
def test_describe_outcomes_are_named_and_total(tmp_path):
    """The 0013-style oracle: the FIRST failing conjunct names the outcome,
    over every constructible combination, and the outcome set is closed."""
    from veracium.procedures import WITHHELD_OUTCOMES, describe_outcome
    seen = set()
    for rk in ("procedural", None):
        for rel in (PROC, GONE):
            for state in ("active", "future", "inactive"):
                for disc in Disclosure:
                    for basis in ("stated", "observed", None):
                        for text in ("Run the formatter before committing.", "The repository uses a formatter."):
                            if rk is None and basis is None:
                                continue
                            e = _edge(text, relation=rel, record_kind=rk, basis=basis, disclosure=disc,
                                      valid_from=(NOW + 5 * D if state == "future" else NOW - 5 * D),
                                      invalidated_at=(NOW - D if state == "inactive" else None))
                            out = describe_outcome(e, DEFAULT_RELATIONS)
                            expected = ("kind_conflict" if rk is None else "relation_unregistered" if rel == GONE
                                        else "inactive" if state == "inactive" else "not_yet_valid" if state == "future"
                                        else "quarantined" if disc is Disclosure.QUARANTINED
                                        else "use_only" if disc is Disclosure.USE_ONLY
                                        else "basis_unknown" if basis is None
                                        else "executable_detail" if text.startswith("Run") else None)
                            assert out == expected, (rk, rel, state, disc, basis, text, out)
                            seen.add(out)
    assert seen == set(WITHHELD_OUTCOMES) | {None}


def test_describe_result_schema_accounts_for_every_visible_record(tmp_path):
    """On a store ABOVE the cap: total_describable + len(withheld) is the
    visible population, len(descriptions) == min(total, limit), truncated
    iff a cut happened; no field carries the note or raw JSON."""
    cap = 5
    mem = _mem(tmp_path, cap=cap)
    ids = [_record(mem, f"The team rotates credential set {i}.", note="step 1: secret") for i in range(8)]
    mem.store.add_edge(_edge("Rotate keys now.", record_kind="procedural", basis="stated", note="step 2: secret"))
    mem.store.add_edge(_edge("Porto", relation="located_at"))
    r = mem.describe_procedures(U)
    assert r.total_describable == 8 and len(r.descriptions) == cap and r.truncated
    assert [w.outcome for w in r.withheld] == ["executable_detail"]
    assert r.total_describable + len(r.withheld) == 9
    r2 = _mem(tmp_path, store=mem.store, cap=10).describe_procedures(U, limit=8)
    assert len(r2.descriptions) == 8 and not r2.truncated
    blob = json.dumps(r.to_dict())
    assert "secret" not in blob and "step" not in blob and '"note"' not in blob
    assert all(isinstance(d, ProcedureDescription) for d in r.descriptions)
    assert mem.describe_procedures(U, query="  Rotate ").query == "rotate"


def test_describe_orders_by_relevance_above_the_cap_and_is_stable(tmp_path):
    mem = _mem(tmp_path, cap=4)
    t = NOW - 30 * D
    for i, (obj, when) in enumerate([("The team archives audit logs weekly.", t + 1 * D),
                                     ("Credentials are rotated every quarter.", t + 5 * D),
                                     ("The audit log is archived and rotated.", t + 2 * D),
                                     ("Backups are verified monthly.", t + 9 * D),
                                     ("Audit findings are triaged on Mondays.", t + 5 * D),
                                     ("The rota is reviewed weekly.", t + 4 * D)]):
        _record(mem, obj, when=when)
    runs = [mem.describe_procedures(U, query="audit log rotated") for _ in range(10)]
    assert all(r.to_dict() == runs[0].to_dict() for r in runs)
    got = [d.edge_id for d in runs[0].descriptions]
    # the §4a-ii order, computed independently: relevance desc (query tokens
    # present in subject/relation/object tokens), valid_from desc, edge_id asc
    q = set(re.findall(r"[a-z0-9]+", "audit log rotated"))
    every = _mem(tmp_path, store=mem.store, cap=10).describe_procedures(U, limit=6).descriptions
    def rel(d): return len(q & set(re.findall(r"[a-z0-9]+", f"user {d.relation} {d.summary}".lower())))
    expected = [d.edge_id for d in sorted(every, key=lambda d: (-rel(d), -d.valid_from.timestamp(), d.edge_id))]
    assert got == expected[:4]
    assert [d.summary for d in runs[0].descriptions][0] == "The audit log is archived and rotated."   # relevance 3
    assert runs[0].truncated and runs[0].total_describable == 6 and len(got) == 4
    null = mem.describe_procedures(U)
    assert [d.valid_from for d in null.descriptions] == sorted((d.valid_from for d in null.descriptions), reverse=True)
    # ties: valid_from desc then edge_id asc
    tied = [d for d in every if d.valid_from == t + 5 * D]
    assert [d.edge_id for d in tied] == sorted(d.edge_id for d in tied)


# --------------------------------------------------- V-NO-IMPLICIT-RECOMMEND
def test_describe_withholds_the_frozen_rule_and_never_renders_the_note(tmp_path):
    """Openers and step markers are DERIVED from the frozen texts at test
    time; the rule fires on every must-match and on none of the paraphrased,
    plain, or must-not-match-named texts (the homographs by name); the
    paraphrase boundary is asserted as a KNOWN PASS; the note appears in no
    field."""
    texts = _texts()
    must = [t["text"] for t in texts["must_match"]]
    openers = {t["opener"] for t in texts["must_match"] if t.get("opener")}
    markers = {re.match(r"^\s*(\S+)", t["text"]).group(1) for t in texts["must_match"] if not t.get("opener")}
    assert len(openers) == 16 and markers                     # derived, not hand-listed
    from veracium.procedures import IMPERATIVE_OPENERS, SUBORDINATORS
    assert openers <= (IMPERATIVE_OPENERS | SUBORDINATORS), sorted(openers - IMPERATIVE_OPENERS - SUBORDINATORS)
    assert all(matches_executable_detail(t) for t in must), [t for t in must if not matches_executable_detail(t)]
    para = [t["text"] for t in texts["paraphrased_known_pass"]]
    plain = [t["text"] for t in texts["plain_declarative"]]
    assert not any(matches_executable_detail(t) for t in para + plain), \
        [t for t in para + plain if matches_executable_detail(t)]
    named = json.loads(CORPUS.read_text(encoding="utf-8"))["recognition_rule"]["must_not_match_named"]
    for group, spec in named.items():
        for t in spec["examples"]:
            assert not matches_executable_detail(t), (group, t)
    assert "archive" not in IMPERATIVE_OPENERS and "email" not in IMPERATIVE_OPENERS and "store" not in IMPERATIVE_OPENERS
    # through the surface: the note is in NO field, the imperative is withheld by name
    mem = _mem(tmp_path)
    imp = _record(mem, must[0], note="step 1: run it; step 2: commit")
    par = _record(mem, para[0], note="step 1: SECRET")
    r = mem.describe_procedures(U)
    assert r.withheld == [Withheld(imp, "executable_detail")]
    assert [d.edge_id for d in r.descriptions] == [par]           # the KNOWN PASS
    assert "SECRET" not in json.dumps(r.to_dict()) and "step" not in json.dumps(r.to_dict())


# ---------------------------------------- V-SCOPE-OUTERMOST / V-WITHHELD-QUERY-BLIND
def _two_principal_store(tmp_path, name, *, hidden=True):
    store = SqliteStore(str(tmp_path / name))
    store.add_edge(_edge("Porto", relation="located_at", eid="e-ctl-decl", source="mb-a"))
    if hidden:
        store.add_edge(_edge("Credentials are rotated quarterly.", record_kind="procedural",
                             basis="stated", source="other-mailbox", eid="e-foreign"))
    return store


def test_hidden_is_indistinguishable_from_no_match(tmp_path):
    with_ = _two_principal_store(tmp_path, "with.db", hidden=True)
    without = _two_principal_store(tmp_path, "without.db", hidden=False)
    B = _principal(with_, xv=False)
    r1 = _mem(tmp_path, store=with_).describe_procedures(U, principal=B[0])
    r2 = _mem(tmp_path, store=without).describe_procedures(U, principal=B[0])
    assert r1 == r2 and r1.to_dict() == r2.to_dict()              # byte-identical as WHOLE results
    assert r1.descriptions == [] and r1.withheld == []
    A = _principal(with_, xv=True)
    ra = _mem(tmp_path, store=with_, xv=True).describe_procedures(U, principal=A[0])
    assert ra.withheld == [Withheld("e-foreign", "use_only")] and ra.descriptions == []


def test_use_only_is_named_not_described(tmp_path):
    mem = _mem(tmp_path)
    eid = _record(mem, "Credentials are rotated quarterly.", author=EvidenceAuthor.THIRD_PARTY)
    r = mem.describe_procedures(U)
    assert r.withheld == [Withheld(eid, "use_only")] and r.descriptions == []
    assert "rotated" not in json.dumps(r.to_dict())


def test_withheld_membership_is_independent_of_the_query(tmp_path):
    mem = _mem(tmp_path)
    a = _record(mem, "The audit log is archived weekly.", author=EvidenceAuthor.THIRD_PARTY)
    b = _record(mem, "Run the formatter before committing.", when=NOW - 3 * D)
    c = _record(mem, "Backups are verified monthly.", author=EvidenceAuthor.ASSISTANT, when=NOW - 2 * D)
    results = [mem.describe_procedures(U, query=q) for q in (None, "audit log", "formatter", "zzz")]
    assert all(r.withheld == results[0].withheld for r in results)
    assert [w.edge_id for w in results[0].withheld] == [w.edge_id for w in sorted(
        results[0].withheld, key=lambda w: (-next(e for e in mem.store.edges(U) if e.id == w.edge_id).valid_from.timestamp(), w.edge_id))]
    assert {w.edge_id for w in results[0].withheld} == {a, b, c}


# ------------------------------------------------- V-BIRTH-QUARANTINE-HOLDS
def test_record_procedure_honours_quarantine_at_birth(tmp_path):
    from veracium.scope_linkage import identity_digest_of
    sites = sorted(p.relative_to(SRC).as_posix() for p in SRC.rglob("*.py")
                   if "standing_revocations(" in p.read_text())
    assert "procedures.py" in sites, sites
    mem = _mem(tmp_path)
    tel = []
    mem.telemetry = type("T", (), {"record": lambda self, ev, f: tel.append((ev, f))})()
    control = _record(mem, "Backups are verified monthly.", source_id="clean-box")
    assert next(e for e in mem.store.edges(U) if e.id == control).provenance.disclosure is Disclosure.MENTIONABLE
    from veracium.store import revocation as rv
    rv.revoke_source(mem.store, U, identity_digest_of(None, "bad-box", mem.store.local_origin()),
                     "revoke", "operator", "2026-08-21T00:00:00Z")
    eid = _record(mem, "Credentials are rotated quarterly.", source_id="bad-box")
    e = next(x for x in mem.store.edges(U, active_only=False) if x.id == eid)
    assert e.provenance.disclosure is Disclosure.QUARANTINED
    assert [f["quarantined_at_birth"] for ev, f in tel if ev == "record_procedure"][-1] == 1
    assert Withheld(eid, "quarantined") in mem.describe_procedures(U).withheld


# ------------------------------- V-RELATION-VALID / V-RELATION-UNREGISTERED / V-HOST-DECLARED
def test_record_procedure_requires_a_registered_procedural_relation(tmp_path):
    mem = _mem(tmp_path)
    before = _snapshot(mem.store)
    for rel in ("no_such", "works_as", 7, None):
        with pytest.raises((TypeError, ValueError)):
            _record(mem, "Rotate keys.", relation=rel)
        assert _snapshot(mem.store) == before
    assert _record(mem, "Rotate keys.", relation=PROC)


def test_unregistered_procedural_stamp_is_named_and_unregistered_declarative_is_unchanged(tmp_path):
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("Credentials are rotated quarterly.", relation=GONE,
                             record_kind="procedural", basis="stated", eid="e-gone"))
    mem.store.add_edge(_edge("Ollie", relation="had_pet", eid="e-legacy"))   # an unstamped legacy row
    r = mem.describe_procedures(U)
    assert r.withheld == [Withheld("e-gone", "relation_unregistered")]
    rc = mem.recall(U, "ollie credentials")
    assert "e-legacy" in {e.id for e in rc.edges} and "e-gone" not in {e.id for e in rc.edges}
    assert "Ollie" in rc.context and "rotated" not in rc.context
    assert "e-gone" in {e.id for e in mem.store.edges(U, active_only=False)}   # still in the store
    assert mem.introspect(U)                                                   # and the diagnostic surface runs
    host = dict(DEFAULT_RELATIONS); host[GONE] = Relation(name=GONE, relation_kind="procedural", desc="g")
    assert _mem(tmp_path, store=mem.store, relations=host).describe_procedures(U).total_describable == 1


def test_mcp_record_procedure_is_the_host_declared_procedural_write_path(tmp_path):
    """The MCP `record_procedure` tool: capability-gated, argument-validated,
    and `remember` refuses a caller-declared basis. (v16: `remember` under
    `direct` can also capture a procedure through the quote gate — tested in
    test_0037_capture.py; this tool remains the host-DECLARED path.)"""
    from veracium import mcp_server as m
    mem = _mem(tmp_path)
    r = m.record_procedure_impl(mem, U, "Credentials are rotated quarterly.", "stated", capability=None)
    assert r == {"ok": False, "refusal": "attempted_elevation"}
    assert m.record_procedure_report(mem, U, "x", "stated", capability=None)["provenance_raises_discarded"] == 1
    assert mem.store.edges(U, active_only=False) == []
    r = m.record_procedure_impl(mem, U, "Credentials are rotated quarterly.", "stated",
                                author="assistant", derived_from="third_party", capability="direct")
    assert r["ok"] and "edge_id" in r
    e = next(x for x in mem.store.edges(U) if x.id == r["edge_id"])
    assert e.provenance.author_of_evidence is EvidenceAuthor.ASSISTANT
    assert e.provenance.derived_from is EvidenceAuthor.THIRD_PARTY and e.provenance.basis == "stated"
    for kw in (dict(relation="works_as"), dict(basis="guessed"), dict(author="system"), dict(summary="")):
        args = dict(summary="Backups are verified monthly.", basis="observed", capability="direct"); args.update(kw)
        s = args.pop("summary"); b = args.pop("basis")
        rr = m.record_procedure_impl(mem, U, s, b, **args)
        assert rr["ok"] is False and rr["refusal"], kw
    assert m.remember_impl(mem, U, "I live in Porto.", capability="direct", basis="stated") == \
        {"ok": False, "refusal": "basis_not_applicable"}
    assert len(mem.store.edges(U, active_only=False)) == 1
    d = m.describe_procedures_impl(mem, U)
    assert d["ok"] and d["withheld"] == [{"edge_id": r["edge_id"], "outcome": "use_only"}]
    assert m.describe_procedures_impl(mem, U, limit=0)["ok"] is False
    src = (SRC / "mcp_server.py").read_text()
    assert "def remember(text: str, author: Optional[str] = None" in src and "basis" not in src[src.index("def remember(text"):src.index("def recall(")]


# ------------------------------------------------------------- V-NO-EPISODE
def test_record_procedure_writes_no_episode(tmp_path):
    mem = _mem(tmp_path)
    before = mem.store.episodes(U)
    _record(mem, "Credentials are rotated quarterly.", note="step 1: rotate")
    after = mem.store.episodes(U)
    assert len(after) == len(before) == 0
    mem.remember(U, "Credentials are rotated quarterly.", context=EvidenceContext.direct())
    assert len(mem.store.episodes(U)) == 1
    assert all("rotate" not in ep.summary.lower() or ep.summary == "we talked" for ep in mem.store.episodes(U))


# -------------------------------------------------------------- V-CARRIERS
def test_basis_reaches_every_carrier():
    """The sweep basis is DERIVED: every `Provenance(` constructor site,
    every `provenance.model_copy(update=` site and every `provenance.`
    reader in src, classified per module; a module absent from the
    classification fails."""
    classified = {
        "ingest.py": "constructs declarative provenance (markers absent by omission); reads disclosure/derived_from",
        "procedures.py": "the ONE carrier that writes both markers; reads both",
        "graph.py": "absorption carries the whole-set minimum basis; readers of observed_at/confidence/disclosure",
        "portability.py": "the raw boundary reads both markers; the capped copy passes them through",
        "schema.py": "the definition; properties",
        "store/sqlite.py": "the same-id immutability guard reads both",
        "__init__.py": "readers (disclosure/author); record_procedure delegates construction",
        "scope_read.py": "shaping copies provenance with disclosure/derived_from narrowed; markers pass through",
        "scope.py": "readers of source_id/origin",
        "scope_linkage.py": "readers of source_id/origin/evidence_ref",
        "source_identity.py": "readers of origin/source_id",
        "gate.py": "readers of third_party_influenced",
        "compile.py": "readers of author/disclosure",
        "proactive.py": "readers of author/disclosure",
        "lifecycle.py": "readers of observed_at",
        "combining.py": "readers",
        "selfcheck.py": "readers",
        "introspect.py": "readers",
        "diagnostics.py": "readers",
        "semantic.py": "readers",
        "agreement.py": "readers",
        "asof/adapter.py": "the raw adapter tolerates the markers as unknown keys",
        "asof/classify.py": "readers via the adapter",
        "asof/resolve.py": "readers",
        "asof/recall.py": "readers",
        "store/current_state.py": "readers",
        "store/base.py": "readers",
        "mcp_server.py": "adapts the tool arguments to a context carrying basis",
        "budgets.py": "readers",
        "authority.py": "readers",
        "cli.py": "readers",
        "contribution.py": "readers of source_id/origin/evidence_ref (the ledger)",
        "store/migration.py": "the on-disk migration rewrites provenance keys of older eras; markers absent by construction on every pre-feature row",
        "store/revocation.py": "readers of source identity",
        "why.py": "readers of author/disclosure/confidence/observed_at/evidence_ref/origin/source_id/record_kind/basis for the biography; the row dump passes both markers through",
    }
    pattern = re.compile(r"Provenance\(|provenance\.model_copy\(update=|\.provenance\.")
    sites = sorted(p.relative_to(SRC).as_posix() for p in SRC.rglob("*.py")
                   if pattern.search(p.read_text()))
    unclassified = [s for s in sites if s not in classified]
    assert not unclassified, unclassified
    stale = [m for m in classified if not (SRC / m).exists()]
    assert not stale, stale


# ---------------------------------------------------- the §6a acceptance corpus
def _cell_edge(cell, texts, eid):
    fx = texts["cell_fixtures"]
    by_id = {t["id"]: t["text"] for k in ("must_match", "paraphrased_known_pass", "plain_declarative")
             for t in texts[k]}
    text = {"imperative": by_id[fx["imperative_executable_detail_x2"][0]],
            "paraphrased": by_id[fx["paraphrased_described_x2"][0]],
            "plain": by_id[fx["plain_described_x2"][0]]}[cell["summary_shape"]]
    relation = PROC if cell["relation"] == "registered" else GONE
    author = EvidenceAuthor[cell["author"]]
    source = "mb-a" if cell["visibility"] == "visible" else "other-mailbox"
    vf = NOW + 10 * D if cell["state"] == "future_valid_from" else NOW - 10 * D
    ia = NOW - D if cell["state"] == "inactive" else None
    return _edge(text, relation=relation, author=author, basis=cell["basis"],
                 record_kind=cell["record_kind"], source=source, valid_from=vf,
                 invalidated_at=ia, eid=eid)


def test_the_frozen_corpus_holds_on_every_cell(tmp_path):
    """The 972 cells CONSUMED WHOLE — every cell constructed with a text of
    its shape, evaluated through the shipped surface under the principal its
    visibility names, its expected list membership and named outcome
    asserted exactly, and its absence from BOTH recall blocks. Pass = 100%."""
    manifest = json.loads(CORPUS.read_text(encoding="utf-8"))
    texts = _texts()
    cells = manifest["cells"]
    assert len(cells) == 972
    store = SqliteStore(str(tmp_path / "corpus.db"))
    ids = {}
    for i, cell in enumerate(cells):
        eid = f"e-cell-{i:04d}"
        store.add_edge(_cell_edge(cell, texts, eid))
        ids[eid] = cell
        # the COMPUTED column: the three-axis rule, then 0020's cross-scope shaping
        derived = _disclosure_for(EvidenceAuthor[cell["author"]], PROC, None).value
        if cell["visibility"] == "cross_scope_visible":
            derived = "use_only"
        assert derived == cell["disclosure_derived"], cell
    memA = _mem(tmp_path, "a.db", xv=True, store=store, cap=2000)
    memB = _mem(tmp_path, "b.db", xv=False, store=store, cap=2000)
    A, B = _principal(store, True), _principal(store, False)
    rA = memA.describe_procedures(U, principal=A[0])
    rB = memB.describe_procedures(U, principal=B[0])
    def membership(r, eid):
        if any(d.edge_id == eid for d in r.descriptions):
            return "descriptions", None
        w = next((w for w in r.withheld if w.edge_id == eid), None)
        return ("withheld", w.outcome) if w else ("neither", None)
    failures = []
    for eid, cell in ids.items():
        r = rA if cell["visibility"] == "cross_scope_visible" else rB
        got = membership(r, eid)
        want = (cell["expect_list"], cell["expect_outcome"])
        if got != want:
            failures.append((eid, cell["summary_shape"], cell["visibility"], cell["kind_state"], want, got))
    assert not failures, f"{len(failures)} of 972 cells failed, e.g. {failures[:5]}"
    # (2) the DERIVED `recall_expectation` (amendment 7, 2026-09-08 — the
    # boolean it replaced was hand-filled and wrong for the declarative
    # control; the field is derived from kind_state × visibility, and each
    # value is asserted FOR ITS OWN REASON): `absent_by_kind` (810) — never at
    # the choke point, under every principal and unscoped; `absent_by_visibility`
    # (54 hidden declaratives) — no principal sees them; and
    # `renders_as_today_when_visible` (108) — the control, rendered exactly
    # as any declarative edge for a principal who can see it.
    edges = {e.id: e for e in store.edges(U, active_only=False, include_quarantined=True)}
    by_value = collections.Counter(c["recall_expectation"] for c in ids.values())
    assert by_value == {"absent_by_kind": 810, "absent_by_visibility": 54,
                        "renders_as_today_when_visible": 108}, by_value
    kind_ids = {i for i, c in ids.items() if c["recall_expectation"] == "absent_by_kind"}
    hidden_ids = {i for i, c in ids.items() if c["recall_expectation"] == "absent_by_visibility"}
    today_ids = {i for i, c in ids.items() if c["recall_expectation"] == "renders_as_today_when_visible"}
    g, u = gate.partition([edges[i] for i in kind_ids], [])
    assert g == "" and u == ""                                  # by KIND: even unscoped
    assert all(not is_procedural(edges[i]) for i in hidden_ids | today_ids)
    for mem, pr, sees in ((memA, A[0], True), (memB, B[0], False), (memA, None, True)):
        for q in ("formatter commit", "repository", None):
            rc = mem.recall(U, q, principal=pr) if q else mem.recall(U, None, principal=pr)
            got = {e.id for e in rc.edges}
            assert not (got & kind_ids)
            if pr is not None:
                assert not (got & hidden_ids) if not sees else True
    # the control renders as today for a principal who can see it: the
    # visible-source declaratives under B, the foreign ones under A
    active_today = [edges[i] for i in today_ids if edges[i].active and edges[i].valid_now]
    rcB = memB.recall(U, "formatter repository", principal=B[0])
    rcA = memA.recall(U, "formatter repository", principal=A[0])
    seen_today = ({e.id for e in rcB.edges} | {e.id for e in rcA.edges}) & today_ids
    assert seen_today, "the declarative control must render as today for a principal who can see it"
    assert not ({e.id for e in rcB.edges} & hidden_ids)       # hidden: B never sees them
    # (5) the accounting identity on a population ABOVE the cap
    memC = _mem(tmp_path, "c.db", xv=False, store=store, cap=3)
    rC = memC.describe_procedures(U, principal=B[0])
    assert len(rC.descriptions) == min(rC.total_describable, 3) and rC.truncated
    assert rC.total_describable + len(rC.withheld) == rB.total_describable + len(rB.withheld)
    # the declarative controls: registered and unregistered, neither list, not counted
    store.add_edge(_edge("Porto", relation="located_at", eid="e-ctl-1"))
    store.add_edge(_edge("Ollie", relation="had_pet", eid="e-ctl-2"))
    r2 = memB.describe_procedures(U, principal=B[0])
    assert (r2.total_describable, len(r2.withheld)) == (rB.total_describable, len(rB.withheld))
    store.close()


def test_the_named_cells_hold(tmp_path):
    """The named cells the product cells cannot catch: existence oracle,
    declarative control, revoked-source-at-write, stamp-survives-registry-
    change, kind_conflict_counted, declarative_bytes_unchanged,
    withheld_query_blind, accounting_above_the_cap — each exercised by the
    node named for it; this test proves the manifest's list is covered."""
    named = json.loads(CORPUS.read_text(encoding="utf-8"))["named_cells"]
    covered = {
        "existence_oracle": test_hidden_is_indistinguishable_from_no_match,
        "declarative_control": test_the_frozen_corpus_holds_on_every_cell,
        "revoked_source_at_write": test_record_procedure_honours_quarantine_at_birth,
        "stamp_survives_registry_change": test_record_kind_is_stamped_at_write_and_read_from_the_record,
        "kind_conflict_counted": test_record_kind_is_stamped_at_write_and_read_from_the_record,
        "declarative_bytes_unchanged": test_every_pre_existing_edge_is_declarative_and_unchanged,
        "withheld_query_blind": test_withheld_membership_is_independent_of_the_query,
        "accounting_above_the_cap": test_describe_result_schema_accounts_for_every_visible_record,
        "import_three_signal_refusal": test_default_import_refuses_procedural_records_on_any_signal,
        "import_format10_marker_x_registry_matrix": test_default_import_refuses_procedural_records_on_any_signal,
        "restore_both_absence_dimensions": test_restore_round_trips_procedural_records_with_basis,
    }
    assert set(named) == set(covered), set(named) ^ set(covered)
