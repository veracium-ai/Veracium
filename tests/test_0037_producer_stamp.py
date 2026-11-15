"""specs/0037 v23 / specs/0006 v10 — the store boundary STATED, `Provenance`
FROZEN, and the PRODUCER stamp (the owner's word, dev session 2026-09-14:
"Confirm as relayed", on research's recommendation ruled 02:06Z).

Three facts this file binds, each with the mutant the reviewer would try:

1. `Provenance` is frozen: no ordinary assignment changes a built stamp, so
   the attribute-chain route V-TWO-PRODUCERS' sweep could not see
   (`prov.record_kind = "procedural"` on an already-built model) no longer
   exists — the sweep's grammar is now the WHOLE grammar (V-PROVENANCE-FROZEN).
2. Every procedural record written by this version carries WHICH product path
   minted it — `producer="host"` from `record_procedure`, `"extractor"` from
   the quote-gated capture — a write-time fact absorption never touches,
   immutable on same-id replace, inherited across a supersession, absent on
   every declarative record (bytes unchanged) and on procedural records from
   before the stamp (V-PRODUCER-STAMPED / -IMMUTABLE / -INHERITED).
3. The doctor's procedural tripwire no longer merges the two populations it
   exists to separate: declared, captured and unstamped are three numbers,
   never added (research's finding, 2026-09-14).

The boundary statement itself (`Store.add_edge` is an interface a host
IMPLEMENTS, not a write API it CALLS; a record written through it carries what
the caller minted) is a carrier check here — the sentence must stand in
0006, 0037 and the host documentation — and a stated limit, not a gate.
"""
from __future__ import annotations
import ast
import importlib.util
import json
import pathlib
import uuid
from datetime import timedelta

import pytest
from pydantic import ValidationError

from veracium import Memory, MemoryConfig, doctor, portability
from veracium.contribution import EXACT_EQUAL_PROV_FIELDS, RECOMPUTED_PROV_FIELDS
from veracium.ingest import _disclosure_for
from veracium.schema import Edge, EvidenceAuthor, EvidenceContext, Provenance, utcnow

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
U = "u"
NOW = utcnow()
D = timedelta(days=1)
PROC = "follows_procedure"
TEXT = ("Any tips for keeping a repo tidy? "                       # v24.1: the routine follows a `?` (an established boundary)
        "I run the formatter before committing, every time.")
QUOTE = "I run the formatter before committing, every time"


def _cfg(tmp_path, name="m.db"):
    return MemoryConfig(db_path=str(tmp_path / name), wiki_recompile_after_writes=0,
                        scope_groups={}, require_source_id=False)


def _llm_emitting(triples):
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return json.dumps({"triples": triples, "episode": "The user described a routine.",
                               "instructions": []})
        if role == "distill-retry":
            return json.dumps({"triples": []})
        return "## USER MODEL\n- test wiki"
    return llm


def _quiet(prompt, *, system=None, role="compile", json_schema=None):
    return json.dumps({"triples": [], "episode": "we talked", "instructions": []})


def _capture(tmp_path, name="c.db"):
    """One extractor-captured procedure through the real path: the quote is a
    whole sentence of the event, the user is the author."""
    mem = Memory(llm=_llm_emitting([{"subject": "user", "relation": PROC,
                                     "object": "Runs the formatter", "quote": QUOTE}]),
                 config=_cfg(tmp_path, name))
    r = mem.remember(U, TEXT, context=EvidenceContext.direct(), date="2026-09-01")
    assert r["procedures"] == 1 and r["procedural_refused"] == 0, r
    return mem


def _declare(mem, summary="Rotate service credentials every quarter."):
    return mem.record_procedure(U, summary, author=EvidenceAuthor.USER,
                                context=EvidenceContext.direct(basis="stated"))


def _edge(obj, *, relation=PROC, record_kind=None, basis=None, producer=None, eid=None,
          supersedes=None):
    """A hand-minted edge: exactly what a host reaches by calling `add_edge`
    directly — the boundary this change states rather than gates."""
    prov = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                      disclosure=_disclosure_for(EvidenceAuthor.USER, relation, None),
                      source_id="mb-a", observed_at=NOW - 10 * D, record_kind=record_kind,
                      basis=basis, producer=producer)
    return Edge(id=eid or f"e-{uuid.uuid4().hex[:12]}", user_id=U, subject="user",
                relation=relation, object=obj, valid_from=NOW - 10 * D, supersedes=supersedes,
                provenance=prov)


# ------------------------------------------------------------ V-PROVENANCE-FROZEN
def test_provenance_is_frozen_after_construction():
    """Every field, including the two procedural markers and the producer:
    ordinary assignment raises; the value is unchanged; a copy with an update
    is the only way to a different stamp, and it is a NEW object."""
    p = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev")
    for field in Provenance.model_fields:
        with pytest.raises(ValidationError):
            setattr(p, field, "procedural" if field in ("record_kind",) else "host")
    assert p.record_kind is None and p.producer is None and p.basis is None
    q = p.model_copy(update={"confidence": 0.5})
    assert q is not p and p.confidence == 0.9 and q.confidence == 0.5
    # the negative control: the OTHER frozen model in schema behaves the same,
    # and an unfrozen model would not — a frozen config is what the test reads
    assert Provenance.model_config.get("frozen") is True


def test_no_src_site_assigns_to_a_provenance_attribute():
    """The eight sites the freeze converted (graph absorption ×3, the store's
    confirmation ×2 and recompute ×2, the decay path's augmented assignment —
    the one a `=`-only regex missed) and any future one: an AST sweep of src
    for every `<expr>.provenance.<field> = / op= …` form finds nothing — a test
    now, not a grep."""
    hits = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            targets = (n.targets if isinstance(n, ast.Assign)
                       else [n.target] if isinstance(n, (ast.AugAssign, ast.AnnAssign)) else [])
            for t in targets:
                if (isinstance(t, ast.Attribute) and isinstance(t.value, ast.Attribute)
                        and t.value.attr == "provenance"):
                    hits.append(f"{path.relative_to(SRC)}:{n.lineno}")
    assert hits == [], hits
    # the control: the sweep sees the shape when it exists
    planted = ast.parse("e.provenance.confidence = 1.0")
    assign = next(n for n in ast.walk(planted) if isinstance(n, ast.Assign))
    t = assign.targets[0]
    assert isinstance(t, ast.Attribute) and t.value.attr == "provenance"


# ------------------------------------------------------------ V-PRODUCER-STAMPED
def test_the_producer_stamp_is_written_at_exactly_the_two_producer_sites():
    """The same two files V-TWO-PRODUCERS names, each with its literal: the
    host surface writes `producer="host"`, the quote-gated extractor path
    writes `producer="extractor"`; no other src site passes the keyword, and
    no site passes it as a non-literal."""
    found, suspicious = {}, []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                for k in n.keywords:
                    if k.arg == "producer":
                        if isinstance(k.value, ast.Constant):
                            found[path.relative_to(SRC).as_posix()] = k.value.value
                        else:
                            suspicious.append(f"{path.name}:{n.lineno}")
    assert found == {"procedures.py": "host", "ingest.py": "extractor"}, found
    assert suspicious == [], suspicious


def test_record_procedure_stamps_host_and_the_capture_path_stamps_extractor(tmp_path):
    mem = _capture(tmp_path)
    pid = _declare(mem)
    edges = {e.id: e for e in mem.store.edges(U, active_only=False)}
    captured = [e for e in edges.values() if e.id != pid and e.provenance.procedural]
    assert len(captured) == 1
    assert captured[0].provenance.producer == "extractor"
    assert captured[0].provenance.record_kind == "procedural" and captured[0].provenance.basis == "stated"
    assert edges[pid].provenance.producer == "host"
    # round-trips the store: what was read back is what was stamped
    assert json.loads(mem.store.export_edge_json(pid) if hasattr(mem.store, "export_edge_json")
                      else edges[pid].model_dump_json())["provenance"]["producer"] == "host"
    mem.close()


def test_a_declarative_record_carries_no_producer_and_a_legacy_procedural_record_needs_none():
    """Absent on every declarative record — the key is OMITTED, so declarative
    bytes are the pre-feature 8 keys (V-DECLARATIVE-UNCHANGED) — and refused
    on one at construction; a procedural record from before the stamp
    validates with producer None (the unstamped era), and the model
    validator refuses nothing else."""
    decl = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev")
    assert "producer" not in decl.model_dump() and "producer" not in decl.model_dump_json()
    assert sorted(decl.model_dump()) == ["author_of_evidence", "confidence", "derived_from",
                                         "disclosure", "evidence_ref", "observed_at", "origin",
                                         "source_id"]
    with pytest.raises(ValidationError, match="producer is set only on a procedural record"):
        Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev", producer="host")
    legacy = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev",
                        record_kind="procedural", basis="stated")
    assert legacy.producer is None and legacy.procedural
    assert "producer" not in legacy.model_dump()
    with pytest.raises(ValidationError):
        Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev",
                   record_kind="procedural", basis="stated", producer="model")


def test_the_0014_partition_places_the_producer_with_the_kind_stamp():
    """EXACT_EQUAL, beside `record_kind`: a write-time fact the raw submission
    carries and absorption never recomputes; the totality test in
    test_0014_receipt_split.py is the gate that would have failed unclassified."""
    assert "producer" in EXACT_EQUAL_PROV_FIELDS and "producer" not in RECOMPUTED_PROV_FIELDS
    assert "record_kind" in EXACT_EQUAL_PROV_FIELDS


# --------------------------------------- V-PRODUCER-IMMUTABLE / V-PRODUCER-INHERITED
def test_producer_is_immutable_on_same_id_replace_and_inherited_across_a_supersession(tmp_path):
    mem = Memory(llm=_quiet, config=_cfg(tmp_path))
    st = mem.store
    st.add_edge(_edge("Rotate keys quarterly.", record_kind="procedural", basis="stated",
                      producer="host", eid="e-host"))
    for other in ("extractor", None):
        with pytest.raises(ValueError, match="cannot change producer"):
            st.add_edge(_edge("Rotate keys quarterly.", record_kind="procedural", basis="stated",
                              producer=other, eid="e-host"))
    # a legacy unstamped record cannot GAIN a producer on replace either
    st.add_edge(_edge("Archive receipts weekly.", record_kind="procedural", basis="stated",
                      eid="e-legacy"))
    with pytest.raises(ValueError, match="cannot change producer"):
        st.add_edge(_edge("Archive receipts weekly.", record_kind="procedural", basis="stated",
                          producer="host", eid="e-legacy"))
    # the successor of a producer-stamped record carries the SAME producer
    with pytest.raises(ValueError, match="V-PRODUCER-INHERITED"):
        st.add_edge(_edge("Rotate keys monthly.", record_kind="procedural", basis="stated",
                          producer="extractor", supersedes="e-host"))
    with pytest.raises(ValueError, match="V-PRODUCER-INHERITED"):
        st.add_edge(_edge("Rotate keys monthly.", record_kind="procedural", basis="stated",
                          producer=None, supersedes="e-host"))
    st.add_edge(_edge("Rotate keys monthly.", record_kind="procedural", basis="stated",
                      producer="host", supersedes="e-host", eid="e-host-2"))
    # a legacy predecessor constrains nothing about the producer (it has none)
    st.add_edge(_edge("Archive receipts monthly.", record_kind="procedural", basis="stated",
                      producer="host", supersedes="e-legacy", eid="e-legacy-2"))
    ids = {e.id: e.provenance.producer for e in st.edges(U, active_only=False)}
    assert ids == {"e-host": "host", "e-legacy": None, "e-host-2": "host", "e-legacy-2": "host"}
    mem.close()


# ---------------------------------------------------- the export era (0037 v23 §4e)
def _export(mem, path):
    mem.export_memory(U, str(path))
    lines = path.read_text().splitlines()
    return json.loads(lines[0]), [json.loads(l) for l in lines[1:]]


def _write(path, header, recs):
    path.write_text("\n".join([json.dumps(header)] + [json.dumps(r) for r in recs]) + "\n")


def test_the_export_stamps_12_only_for_a_producer_bearing_store_and_old_readers_refuse(tmp_path, monkeypatch):
    # a store whose only procedural record predates the stamp exports 11, as before
    legacy = Memory(llm=_quiet, config=_cfg(tmp_path, "legacy.db"))
    legacy.store.add_edge(_edge("Rotate keys quarterly.", record_kind="procedural", basis="stated"))
    h, _ = _export(legacy, tmp_path / "legacy.jsonl")
    assert h["version"] == 11
    legacy.close()
    # a host-declared record carries the producer → 12; the 0.24.0 reader refuses it outright
    mem = Memory(llm=_quiet, config=_cfg(tmp_path, "new.db"))
    pid = _declare(mem)
    h, recs = _export(mem, tmp_path / "new.jsonl")
    # 0041 tranche 4b (2026-09-20): the reader's head moved to 13 (the redaction era); 0044 T11a to 14 (the arity
    # era); the producer era stays 12
    assert h["version"] == 12 and portability._PRODUCER_VERSION == 12 and portability.FORMAT_VERSION == 15  # specs/0031 v23.1: 14->15, the call-path era, conditionally stamped the same way
    assert next(r for r in recs if r["id"] == pid)["provenance"]["producer"] == "host"
    mem.close()
    monkeypatch.setattr(portability, "FORMAT_VERSION", 11)
    old = Memory(llm=_quiet, config=_cfg(tmp_path, "old.db"))
    with pytest.raises(ValueError, match="newer than this Veracium understands"):
        old.import_memory(str(tmp_path / "new.jsonl"))
    assert old.store.edges(U, active_only=False) == []
    old.close()
    monkeypatch.undo()
    # restore round-trips the producer verbatim
    back = Memory(llm=_quiet, config=_cfg(tmp_path, "back.db"))
    rep = back.import_memory(str(tmp_path / "new.jsonl"), restore=True)
    assert rep["edges"] == 1
    assert back.store.edges(U, active_only=False)[0].provenance.producer == "host"
    back.close()


def test_a_producer_in_a_pre_12_envelope_is_stripped_and_a_raw_producer_is_a_refusal_signal(tmp_path):
    mem = Memory(llm=_quiet, config=_cfg(tmp_path, "src.db"))
    pid = _declare(mem)
    h, recs = _export(mem, tmp_path / "e.jsonl")
    mem.close()
    # (a) an envelope that declares 11 but carries the producer: I10 — the field is
    # newer than the declared version, never trusted; the record restores UNSTAMPED
    below = dict(h, version=11)
    _write(tmp_path / "below.jsonl", below, recs)
    dst = Memory(llm=_quiet, config=_cfg(tmp_path, "below.db"))
    assert dst.import_memory(str(tmp_path / "below.jsonl"), restore=True)["edges"] == 1
    got = dst.store.edges(U, active_only=False)[0].provenance
    assert got.procedural and got.producer is None
    dst.close()
    # (b) on the default path a raw producer is the FOURTH independent signal, named
    stripped = json.loads(json.dumps(recs))
    for r in stripped:
        r["provenance"].pop("record_kind", None); r["provenance"].pop("basis", None)
        r["relation"] = "likes"                     # off the registry's procedural kinds
    _write(tmp_path / "prod-only.jsonl", h, stripped)
    dst2 = Memory(llm=_quiet, config=_cfg(tmp_path, "prod.db"))
    rep = dst2.import_memory(str(tmp_path / "prod-only.jsonl"))
    assert rep["edges"] == 0 and rep["procedural_refused"] == 1
    assert rep["procedural_refusals"][0]["signal"] == "producer"
    # (c) on restore a producer without the stamp is MALFORMED, named by its signal
    rep2 = dst2.import_memory(str(tmp_path / "prod-only.jsonl"), restore=True)
    assert rep2["edges"] == 0 and rep2["procedural_refusals"][0]["refusal"] == "malformed_procedural_marker"
    assert rep2["procedural_refusals"][0]["signal"] == "producer"
    # (d) a producer outside the domain is malformed too
    bad = json.loads(json.dumps(recs))
    bad[0]["provenance"]["producer"] = "model"
    _write(tmp_path / "bad.jsonl", h, bad)
    rep3 = dst2.import_memory(str(tmp_path / "bad.jsonl"), restore=True)
    assert rep3["edges"] == 0 and rep3["procedural_refusals"][0]["signal"] == "producer"
    dst2.close()


# ------------------------------------------------------ the doctor's split
def test_the_doctor_reports_declared_captured_and_unstamped_as_three_numbers_never_merged(tmp_path):
    mem = _capture(tmp_path, "d.db")                       # one captured
    pid = _declare(mem)                                     # one declared
    # one unstamped — here a record hand-minted at Store.add_edge with no
    # producer; a restored older export or a sub-12 envelope produces the same
    # count (round-5 finding 4), so the count says "producer unknown", not why
    mem.store.add_edge(_edge("Archive receipts weekly.", record_kind="procedural", basis="stated"))
    db = mem.config.db_path
    mem.close()
    rep = doctor.diagnose(db)
    f = [x for x in rep.findings if x.check == "procedural"]
    assert len(f) == 1 and f[0].level == "info" and rep.exit_code == 0
    assert (rep.counts["procedural_declared"], rep.counts["procedural_captured"],
            rep.counts["procedural_unstamped"]) == (1, 1, 1)
    assert rep.counts["procedural_shaped"] == 0
    for phrase in ("procedural_declared 1", "procedural_captured 1", "procedural_unstamped 1",
                   "cannot be told apart", "a path other than Memory", "restored from an older export",
                   "producer is unknown", "never merged"):
        assert phrase in f[0].message, phrase
    assert pid not in f[0].ids                                       # ids: the shaped screen only
    # the negative control for the split: a store with only legacy procedural
    # records reports the unstamped bucket and zeros elsewhere — nothing is guessed
    m2 = Memory(llm=_quiet, config=_cfg(tmp_path, "d2.db"))
    m2.store.add_edge(_edge("Rotate keys quarterly.", record_kind="procedural", basis="stated"))
    db2 = m2.config.db_path
    m2.close()
    rep2 = doctor.diagnose(db2)
    assert (rep2.counts["procedural_declared"], rep2.counts["procedural_captured"],
            rep2.counts["procedural_unstamped"]) == (0, 0, 1)


# ------------------------------------- the boundary STATEMENT (0006 v10, 0037 v23)
BOUNDARY = "an interface a host IMPLEMENTS, not a write API a host CALLS"


def test_the_store_boundary_is_stated_in_both_specs_and_the_host_documentation():
    """The ruling gives the `require_source_id` bypass at `add_edge` a
    STATEMENT and no gate: the sentence must stand, verbatim, where a host
    reads (docs/api.md, "Providing a store") and in the two accepted specs
    that carry the invariants it bounds."""
    for rel in ("docs/api.md", "specs/0006-source-identity.md", "specs/0037-procedural-basis.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert BOUNDARY in text, rel
    docs = (ROOT / "docs" / "api.md").read_text(encoding="utf-8")
    section = docs[docs.index("## Providing a store"):]
    section = section[:section.index("\n## ", 1)]
    assert BOUNDARY in section and "add_edge" in section


# ------------------------------------ v24.1 (round-5 finding 3): inheritance on import
def _proc_edge(obj, eid, producer, supersedes=None):
    return _edge(obj, record_kind="procedural", basis="stated", producer=producer, eid=eid, supersedes=supersedes)


def _file_from(mem, path):
    mem.export_memory(U, str(path))
    lines = path.read_text().splitlines()
    return json.loads(lines[0]), [json.loads(l) for l in lines[1:]]


def _write_lines(path, header, recs):
    path.write_text("\n".join([json.dumps(header)] + [json.dumps(r) for r in recs]) + "\n")


@pytest.mark.parametrize("order", ["predecessor first", "successor first"])
def test_restore_applies_the_inheritance_rules_the_store_applies_to_a_write(tmp_path, order):
    """The round-5 reviewer: a format-12 file with a `host` predecessor and an
    `extractor` successor linked through `supersedes` restored both, and so did
    a successor with no producer, while a direct write refuses both — the
    restore commit wrote rows directly. Now the boundary applies V-PRODUCER-
    INHERITED and V-STAMP-INHERITED to every incoming record against its
    predecessor, incoming or existing, in either file order; the violating
    successor is refused per record and counted, the predecessor restores."""
    src = Memory(llm=_quiet, config=_cfg(tmp_path, "src.db"))
    src.store.add_edge(_proc_edge("Rotate keys.", "e-pred", "host"))
    src.store.add_edge(_proc_edge("Rotate keys monthly.", "e-succ", "host", supersedes="e-pred"))
    header, recs = _file_from(src, tmp_path / "e.jsonl")
    src.close()
    assert header["version"] == 12
    if order == "successor first":
        recs = sorted(recs, key=lambda r: r["id"] != "e-succ")
    for case, mutate, signal in [
        ("a different producer", lambda r: r["provenance"].__setitem__("producer", "extractor"), "producer"),
        ("no producer", lambda r: r["provenance"].pop("producer"), "producer"),
        ("the markers dropped", lambda r: (r["provenance"].pop("record_kind"), r["provenance"].pop("basis"),
                                           r["provenance"].pop("producer"), r.__setitem__("relation", "located_at")), "stamp"),
    ]:
        bad = json.loads(json.dumps(recs))
        mutate(next(r for r in bad if r["id"] == "e-succ"))
        f = tmp_path / f"{case}-{order}.jsonl"
        _write_lines(f, header, bad)
        dst = Memory(llm=_quiet, config=_cfg(tmp_path, f"dst-{case}-{order}.db"))
        rep = dst.import_memory(str(f), restore=True)
        got = {e.id: e.provenance.producer for e in dst.store.edges(U, active_only=False)}
        assert got == {"e-pred": "host"}, (case, order, got)
        assert rep["procedural_refused"] == 1 and rep["procedural_refusals"][0] == {
            "id": "e-succ", "refusal": "inheritance_violation", "signal": signal, "predecessor": "e-pred", "raw": False}, (case, order, rep)
        dst.close()
    # matching producers restore in either order
    f = tmp_path / f"ok-{order}.jsonl"
    _write_lines(f, header, recs)
    ok = Memory(llm=_quiet, config=_cfg(tmp_path, f"ok-{order}.db"))
    rep = ok.import_memory(str(f), restore=True)
    assert rep["edges"] == 2 and rep["procedural_refused"] == 0
    assert {e.id: e.provenance.producer for e in ok.store.edges(U, active_only=False)} == {"e-pred": "host", "e-succ": "host"}
    ok.close()


def test_inheritance_is_checked_against_an_existing_destination_predecessor_on_both_paths(tmp_path):
    """The predecessor already in the destination: a restored successor naming
    another producer is refused; on the DEFAULT path a declarative successor of
    an existing procedural predecessor — the only successor shape that path
    admits — is refused as a marker drop (V-STAMP-INHERITED reaches the import
    commit); a declarative successor of a declarative predecessor imports."""
    dst = Memory(llm=_quiet, config=_cfg(tmp_path, "dst.db"))
    dst.store.add_edge(_proc_edge("Rotate keys.", "e-pred", "host"))
    dst.store.add_edge(_edge("Porto", relation="located_at", eid="e-decl"))
    src = Memory(llm=_quiet, config=_cfg(tmp_path, "src.db"))
    src.store.add_edge(_proc_edge("Rotate keys.", "e-pred", "host"))
    src.store.add_edge(_proc_edge("Rotate keys monthly.", "e-succ", "host", supersedes="e-pred"))   # the store refuses a direct mismatch; the FILE is where it is forged
    header, recs = _file_from(src, tmp_path / "s.jsonl")
    src.close()
    only_succ = [r for r in recs if r["id"] == "e-succ"]
    only_succ[0]["provenance"]["producer"] = "extractor"
    _write_lines(tmp_path / "succ.jsonl", header, only_succ)
    rep = dst.import_memory(str(tmp_path / "succ.jsonl"), restore=True)
    assert rep["edges"] == 0 and rep["procedural_refusals"][0]["refusal"] == "inheritance_violation"
    assert rep["procedural_refusals"][0]["signal"] == "producer" and rep["procedural_refusals"][0]["predecessor"] == "e-pred"
    # the default path: a declarative successor of the existing procedural predecessor
    decl_succ = json.loads(json.dumps(only_succ[0]))
    decl_succ["provenance"].pop("record_kind"); decl_succ["provenance"].pop("basis"); decl_succ["provenance"].pop("producer")
    decl_succ["relation"] = "located_at"; decl_succ["id"] = "e-decl-succ"
    _write_lines(tmp_path / "decl.jsonl", header, [decl_succ])
    rep2 = dst.import_memory(str(tmp_path / "decl.jsonl"))
    assert rep2["edges"] == 0 and rep2["procedural_refusals"][0]["signal"] == "stamp"
    # the control: a declarative successor of a declarative predecessor imports on the default path
    ctrl = json.loads(json.dumps(decl_succ)); ctrl["supersedes"] = "e-decl"; ctrl["id"] = "e-decl-2"
    _write_lines(tmp_path / "ctrl.jsonl", header, [ctrl])
    rep3 = dst.import_memory(str(tmp_path / "ctrl.jsonl"))
    assert rep3["edges"] == 1 and rep3["procedural_refused"] == 0
    assert {e.id for e in dst.store.edges(U, active_only=False)} == {"e-pred", "e-decl", "e-decl-2"}
    dst.close()


# ------------------------------ v24.2 (round-6 finding 2): the lookup sees REFUSED predecessors
@pytest.mark.parametrize("order", ["predecessor first", "successors first"])
def test_the_default_path_keeps_a_refused_predecessor_for_its_successors_inheritance(tmp_path, order):
    """The round-6 reviewer: on the default path a procedural predecessor was refused
    (as procedural) and its marker-stripped declarative successor imported, reaching
    model context as `use_only` — the inheritance lookup was built from the records
    that SURVIVED the procedural filter. Now the lookup is built from the RAW records
    before any refusal, procedural-ness is by LINEAGE (a chain that drops the markers
    one hop later is refused one hop later too), and the result is the same in either
    file order: nothing of the lineage imports, each successor refused and counted."""
    src = Memory(llm=_quiet, config=_cfg(tmp_path, "src.db"))
    src.store.add_edge(_proc_edge("Rotate keys.", "e-pred", "host"))
    src.store.add_edge(_proc_edge("Rotate keys monthly.", "e-succ", "host", supersedes="e-pred"))
    src.store.add_edge(_proc_edge("Rotate keys yearly.", "e-succ2", "host", supersedes="e-succ"))
    header, recs = _file_from(src, tmp_path / "e.jsonl")
    src.close()
    for r in recs:
        if r["id"] in ("e-succ", "e-succ2"):                 # the markers stripped, the relation declarative
            r["provenance"].pop("record_kind"); r["provenance"].pop("basis"); r["provenance"].pop("producer")
            r["relation"] = "located_at"
    if order == "successors first":
        recs = list(reversed(recs))
    f = tmp_path / f"chain-{order}.jsonl"
    _write_lines(f, header, recs)
    dst = Memory(llm=_quiet, config=_cfg(tmp_path, f"dst-{order}.db"))
    rep = dst.import_memory(str(f))
    assert [e.id for e in dst.store.edges(U, active_only=False)] == []
    got = {x["id"]: (x["refusal"], x["signal"]) for x in rep["procedural_refusals"]}
    assert got == {"e-pred": ("procedural_import_refused", "stamp"),
                   "e-succ": ("inheritance_violation", "stamp"),
                   "e-succ2": ("inheritance_violation", "stamp")}, got
    assert rep["procedural_refused"] == 3
    # the control: a declarative lineage imports whole on the default path
    ok = Memory(llm=_quiet, config=_cfg(tmp_path, f"ok-{order}.db"))
    ok.store.add_edge(_edge("Porto", relation="located_at", eid="d-1"))
    ok.store.add_edge(_edge("Lisbon", relation="located_at", eid="d-2", supersedes="d-1"))
    header2, recs2 = _file_from(ok, tmp_path / "decl.jsonl")
    ok.close()
    dst2 = Memory(llm=_quiet, config=_cfg(tmp_path, f"dst2-{order}.db"))
    rep2 = dst2.import_memory(str(tmp_path / "decl.jsonl"))
    assert rep2["edges"] == 2 and rep2["procedural_refused"] == 0
    dst2.close()


# ---------------- v24.3 (round-7 finding 2): the lineage helper reads the filter's signals and validates inheritance
@pytest.mark.parametrize("order", ["predecessor first", "successors first"])
def test_lineage_reads_every_import_signal_and_carries_validated_inheritance(tmp_path, order):
    """The round-7 reviewer, both orders: a REGISTRY-only predecessor (procedural
    relation, no markers) was refused but its marker-free successors imported — the
    lineage helper read stamp and basis only; a PRODUCER-only predecessor's grandchild
    imported; and on restore a `host` lineage with an intermediate changed to
    `extractor` (refused) let a further `extractor` successor restore — the raw
    field of a rejected intermediate stood in for validated inheritance. Now the
    helper reads the filter's four signals (stamp, basis, producer, the registry on
    the default path) and the inherited producer is VALIDATED down the chain: a
    rejected intermediate's constraint carries on unchanged."""
    src = Memory(llm=_quiet, config=_cfg(tmp_path, "src.db"))
    src.store.add_edge(_proc_edge("Rotate keys.", "e-pred", "host"))
    src.store.add_edge(_proc_edge("Rotate keys monthly.", "e-succ", "host", supersedes="e-pred"))
    src.store.add_edge(_proc_edge("Rotate keys yearly.", "e-succ2", "host", supersedes="e-succ"))
    header, base = _file_from(src, tmp_path / "e.jsonl")
    src.close()

    def strip(r):
        for k in ("record_kind", "basis", "producer"):
            r["provenance"].pop(k, None)

    def run(recs, name, restore=False):
        recs = list(recs) if order == "predecessor first" else list(reversed(recs))
        f = tmp_path / f"{name}-{order}.jsonl"
        _write_lines(f, header, recs)
        m = Memory(llm=_quiet, config=_cfg(tmp_path, f"{name}-{order}.db"))
        rep = m.import_memory(str(f), restore=restore)
        got = (sorted(e.id for e in m.store.edges(U, active_only=False)),
               sorted((x["id"], x["refusal"], x["signal"]) for x in rep["procedural_refusals"]))
        m.close()
        return got
    # registry-only predecessor: procedural by the receiving registry's kind, no markers
    a = json.loads(json.dumps(base))
    for r in a:
        strip(r)
        if r["id"] != "e-pred":
            r["relation"] = "located_at"
    assert run(a, "registry") == ([], [("e-pred", "procedural_import_refused", "registry"),
                                        ("e-succ", "inheritance_violation", "stamp"),
                                        ("e-succ2", "inheritance_violation", "stamp")])
    # producer-only predecessor
    b = json.loads(json.dumps(base))
    for r in b:
        strip(r)
        if r["id"] == "e-pred":
            r["provenance"]["producer"] = "host"
        else:
            r["relation"] = "located_at"
    assert run(b, "producer") == ([], [("e-pred", "procedural_import_refused", "producer"),
                                        ("e-succ", "inheritance_violation", "stamp"),
                                        ("e-succ2", "inheritance_violation", "stamp")])
    # restore: a host lineage with the intermediate AND its successor changed to extractor
    c = json.loads(json.dumps(base))
    for r in c:
        if r["id"] in ("e-succ", "e-succ2"):
            r["provenance"]["producer"] = "extractor"
    assert run(c, "changed", restore=True) == (["e-pred"], [("e-succ", "inheritance_violation", "producer"),
                                                             ("e-succ2", "inheritance_violation", "producer")])
    # the control: the intact lineage restores whole
    assert run(base, "intact", restore=True) == (["e-pred", "e-succ", "e-succ2"], [])


@pytest.mark.parametrize("order", ["predecessor first", "successor first"])
def test_conflicting_ids_are_resolved_before_lineage_in_both_orders(tmp_path, order):
    """The round-8 reviewer (0037 v24.4 — the contract frozen at round 8, this is
    its implementation): `raw_by_id` kept the LAST incoming record per id and the
    lineage helper preferred it over the stored record, so (a) a REFUSED
    incomplete copy of a stored procedural predecessor (stamp only — no basis, no
    producer) hid the stored `host` producer and an `extractor` successor
    restored; (b) a file naming `P` twice (procedural and ordinary) plus an
    ordinary successor gave a file-order-dependent disposition. Now every copy of
    a duplicated id is refused (`duplicate_id`), the lineage helper reads the
    stored record FIRST and every copy together (a copy adds procedural-ness,
    never removes a stored constraint), and copies that disagree about a
    constraint leave it unresolved, which no successor satisfies. Both orders,
    the same disposition and the same stored rows; the reviewer's valid
    re-import control restores."""
    src = Memory(llm=_quiet, config=_cfg(tmp_path, "src.db"))
    src.store.add_edge(_proc_edge("Rotate keys.", "e-pred", "host"))
    src.store.add_edge(_proc_edge("Rotate keys monthly.", "e-succ", "host", supersedes="e-pred"))
    header, base = _file_from(src, tmp_path / "e.jsonl")
    src.close()
    by = {r["id"]: r for r in base}

    def copy(rid, **prov):
        r = json.loads(json.dumps(by[rid]))
        for k, v in prov.items():
            if v is None:
                r["provenance"].pop(k, None)
            else:
                r["provenance"][k] = v
        return r

    def ordinary(rid):
        r = copy(rid, record_kind=None, basis=None, producer=None)
        r["relation"] = "located_at"
        return r

    def run(recs, name, restore=False, first=None):
        """`first` restores a seed file into the destination before `recs`."""
        recs = list(recs) if order == "predecessor first" else list(reversed(recs))
        m = Memory(llm=_quiet, config=_cfg(tmp_path, f"{name}-{order}.db"))
        if first is not None:
            f0 = tmp_path / f"{name}-seed-{order}.jsonl"
            _write_lines(f0, header, first)
            m.import_memory(str(f0), restore=True)
        f = tmp_path / f"{name}-{order}.jsonl"
        _write_lines(f, header, recs)
        rep = m.import_memory(str(f), restore=restore)
        got = ({e.id: (e.provenance.procedural, e.provenance.producer, e.supersedes)
                for e in m.store.edges(U, active_only=False)},
               sorted((x["id"], x["refusal"], x["signal"]) for x in rep["procedural_refusals"]))
        m.close()
        return got

    P = by["e-pred"]; S_host = by["e-succ"]
    S_ext = copy("e-succ", producer="extractor")
    stored_P = {"e-pred": (True, "host", None)}
    # (a) the reviewer's first form: stored P (host); the file's copy of P is stamp-only
    # (refused as malformed) and S carries `extractor` — S is REFUSED on the stored producer
    P_incomplete = copy("e-pred", basis=None, producer=None)
    assert run([P_incomplete, S_ext], "a", restore=True, first=[P]) == (
        stored_P, [("e-pred", "malformed_procedural_marker", "stamp"),
                   ("e-succ", "inheritance_violation", "producer")])
    # (b) the reviewer's second form: P twice (procedural, ordinary) + an ordinary successor,
    # default path — both copies refused as duplicates, S refused on the procedural reading
    assert run([P, ordinary("e-pred"), ordinary("e-succ")], "b") == (
        {}, [("e-pred", "duplicate_id", "id"), ("e-pred", "duplicate_id", "id"),
             ("e-succ", "inheritance_violation", "stamp")])
    # the reviewer's valid re-import control: the identical P already stored, the file
    # carries P and its host successor — S restores, nothing refused
    assert run([P, S_host], "control", restore=True, first=[P]) == (
        {**stored_P, "e-succ": (True, "host", "e-pred")}, [])
    # ...and the same control with the successor's producer changed refuses it
    assert run([P, S_ext], "control-x", restore=True, first=[P]) == (
        stored_P, [("e-succ", "inheritance_violation", "producer")])
    # copies that AGREE are still duplicates (refused), and the constraint they agree on holds
    assert run([P, copy("e-pred"), S_host], "agree", restore=True) == (
        {"e-succ": (True, "host", "e-pred")},
        [("e-pred", "duplicate_id", "id"), ("e-pred", "duplicate_id", "id")])
    # copies that DISAGREE on the producer leave it unresolved: no successor satisfies it
    assert run([P, copy("e-pred", producer="extractor"), S_host], "disagree", restore=True) == (
        {}, [("e-pred", "duplicate_id", "id"), ("e-pred", "duplicate_id", "id"),
             ("e-succ", "inheritance_violation", "producer")])
    # with P STORED, disagreeing copies cannot move the stored constraint: host restores, extractor refuses
    assert run([P, copy("e-pred", producer="extractor"), S_host], "stored-agree", restore=True, first=[P]) == (
        {**stored_P, "e-succ": (True, "host", "e-pred")},
        [("e-pred", "duplicate_id", "id"), ("e-pred", "duplicate_id", "id")])
    assert run([P, copy("e-pred", producer="extractor"), S_ext], "stored-x", restore=True, first=[P]) == (
        stored_P, [("e-pred", "duplicate_id", "id"), ("e-pred", "duplicate_id", "id"),
                   ("e-succ", "inheritance_violation", "producer")])
    # a duplicated INTERMEDIATE (S twice, host and extractor) under a stored host P: the
    # grandchild inherits host through the refused intermediate and its `extractor` refuses
    S2 = copy("e-succ", producer="extractor"); S2["id"] = "e-succ2"; S2["supersedes"] = "e-succ"
    assert run([S_host, S_ext, S2], "intermediate", restore=True, first=[P]) == (
        stored_P, [("e-succ", "duplicate_id", "id"), ("e-succ", "duplicate_id", "id"),
                   ("e-succ2", "inheritance_violation", "producer")])
    # ordinary duplicates carry no constraint: the copies are refused, the ordinary successor imports
    P_ord, P_ord2 = ordinary("e-pred"), ordinary("e-pred"); P_ord2["object"] = "other text"
    assert run([P_ord, P_ord2, ordinary("e-succ")], "ordinary") == (
        {"e-succ": (False, None, "e-pred")},
        [("e-pred", "duplicate_id", "id"), ("e-pred", "duplicate_id", "id")])


@pytest.mark.parametrize("order", ["predecessor first", "successor first"])
def test_stored_and_incoming_custody_read_one_procedural_signal_set(tmp_path, order):
    """Research's pre-seal red team of v24.4 (2026-09-14), two findings in the
    lineage helper, reproduced before the fix. A: the stored record's own-ness
    read `Provenance.procedural` (stamp-or-basis only), so a REGISTRY-only
    procedural predecessor got opposite dispositions by custody — refused with
    its successor when incoming, its marker-free successor LANDING when stored.
    C: `own` unioned stored and incoming readings but the predecessor set was
    REPLACED by the stored record's, so a stored declarative X with no
    predecessor shadowed an incoming X claiming a procedural predecessor and
    X's own successor inherited from the shadow. Now one helper reads the four
    signals for both custody states, and the predecessor set adds and never
    removes. B (not a finding): the unresolved sentinel is a unique object, not
    a value a record could carry."""
    src = Memory(llm=_quiet, config=_cfg(tmp_path, "src.db"))
    src.store.add_edge(_edge("Rotate keys.", relation=PROC, eid="e-pred"))                 # registry-only: no markers
    src.store.add_edge(_edge("Porto", relation="located_at", eid="e-succ", supersedes="e-pred"))
    header, base = _file_from(src, tmp_path / "a.jsonl")
    src.close()
    by = {r["id"]: r for r in base}

    def run(recs, name, seed=(), restore=False):
        recs = list(recs) if order == "predecessor first" else list(reversed(recs))
        m = Memory(llm=_quiet, config=_cfg(tmp_path, f"{name}-{order}.db"))
        for e in seed:
            m.store.add_edge(e)
        f = tmp_path / f"{name}-{order}.jsonl"
        _write_lines(f, header, recs)
        rep = m.import_memory(str(f), restore=restore)
        got = (sorted(e.id for e in m.store.edges(U, active_only=False, include_quarantined=True)),
               sorted((x["id"], x["refusal"], x["signal"]) for x in rep["procedural_refusals"]))
        m.close()
        return got

    # A — the predecessor incoming (round 7's fixed path) and STORED give the same answer
    assert run([by["e-pred"], by["e-succ"]], "a-incoming") == (
        [], [("e-pred", "procedural_import_refused", "registry"), ("e-succ", "inheritance_violation", "stamp")])
    assert run([by["e-succ"]], "a-stored", seed=[_edge("Rotate keys.", relation=PROC, eid="e-pred")]) == (
        ["e-pred"], [("e-succ", "inheritance_violation", "stamp")])
    # C — a procedural P, its successor X and X's successor Y in the file; a stored
    # declarative X with no predecessor must not shadow the file's chain
    chain = Memory(llm=_quiet, config=_cfg(tmp_path, "chain.db"))
    chain.store.add_edge(_proc_edge("Rotate keys.", "e-P", "host"))
    chain.store.add_edge(_edge("Porto", relation="located_at", eid="e-X"))
    chain.store.add_edge(_edge("Lisbon", relation="located_at", eid="e-Y", supersedes="e-X"))
    header2, base2 = _file_from(chain, tmp_path / "c.jsonl")
    chain.close()
    recs = json.loads(json.dumps(base2))
    for r in recs:
        if r["id"] == "e-X":
            r["supersedes"] = "e-P"                       # forged in the file: add_edge refuses to build it
    header = header2
    expect_refused = [("e-P", "procedural_import_refused", "stamp"), ("e-X", "inheritance_violation", "stamp"),
                      ("e-Y", "inheritance_violation", "stamp")]
    assert run(recs, "c-empty") == ([], expect_refused)                                  # the control
    assert run(recs, "c-shadow", seed=[_edge("Porto", relation="located_at", eid="e-X")]) == (["e-X"], expect_refused)
    # B — the sentinel is not a value; a successor carrying the old string is refused by the lexicon anyway
    from veracium import portability as _p
    src_text = pathlib.Path(_p.__file__).read_text()
    assert "_UNRESOLVED = object()" in src_text and '_UNRESOLVED = "unresolved"' not in src_text


@pytest.mark.parametrize("order", ["predecessor first", "successor first"])
@pytest.mark.parametrize("q_where", ["stored", "incoming"])
def test_a_persisted_producer_is_never_replaced_by_claimed_ancestry(tmp_path, order, q_where):
    """The round-9 reviewer (0037 v24.5, the contract frozen at round 8): stored P
    (`host`, no predecessor) and Q (`extractor`); the file carries a copy of P
    CLAIMING Q as its predecessor (refused) and S (`extractor`, supersedes P). S
    restored, because the lineage helper preserved P's stored producer and then
    replaced it with the producer derived from the claimed chain. Now a
    persisted producer IS the constraint: a claimed ancestry — from an admitted
    or a refused copy — can add procedural-ness and never replace it. Q stored
    or arriving in the file, both orders; the control without the copy; the
    mutants: an agreeing claim lets a `host` successor restore, and an
    UNSTAMPED stored predecessor takes the claimed chain's producer (a claim can
    only add a constraint)."""
    src = Memory(llm=_quiet, config=_cfg(tmp_path, "src.db"))
    src.store.add_edge(_proc_edge("Rotate keys.", "e-P", "host"))
    src.store.add_edge(_proc_edge("Rotate keys often.", "e-Q", "extractor"))
    src.store.add_edge(_proc_edge("Rotate keys monthly.", "e-S", "host", supersedes="e-P"))
    header, base = _file_from(src, tmp_path / "e.jsonl")
    src.close()
    by = {r["id"]: r for r in base}

    def copy(rid, **over):
        r = json.loads(json.dumps(by[rid]))
        for k, v in over.items():
            if k == "producer":
                r["provenance"]["producer"] = v
            else:
                r[k] = v
        return r

    def run(recs, name, seed):
        recs = list(recs) if order == "predecessor first" else list(reversed(recs))
        m = Memory(llm=_quiet, config=_cfg(tmp_path, f"{name}-{order}-{q_where}.db"))
        for e in seed:
            m.store.add_edge(e)
        f = tmp_path / f"{name}-{order}-{q_where}.jsonl"
        _write_lines(f, header, recs)
        rep = m.import_memory(str(f), restore=True)
        got = ({e.id: (e.provenance.producer, e.supersedes) for e in m.store.edges(U, active_only=False)},
               sorted((x["id"], x["refusal"], x["signal"]) for x in rep["procedural_refusals"]))
        m.close()
        return got

    P_host, Q_ext = _proc_edge("Rotate keys.", "e-P", "host"), _proc_edge("Rotate keys often.", "e-Q", "extractor")
    seed = [P_host, Q_ext] if q_where == "stored" else [P_host]
    file_q = [] if q_where == "stored" else [by["e-Q"]]
    P_claim = copy("e-P", supersedes="e-Q")                       # forged ancestry: P claims Q
    S_ext = copy("e-S", producer="extractor")                     # forged in the file: the store refuses to build it
    stored = {"e-P": ("host", None), "e-Q": ("extractor", None)}
    # the reviewer's case: the copy is refused AND S is refused on the PERSISTED producer
    assert run(file_q + [P_claim, S_ext], "f1", seed) == (
        stored, [("e-P", "inheritance_violation", "producer"), ("e-S", "inheritance_violation", "producer")])
    # the control: without the copy, S is refused the same way
    assert run(file_q + [S_ext], "ctl", seed) == (stored, [("e-S", "inheritance_violation", "producer")])
    # mutant: a claim that AGREES with the persisted producer passes the lineage check and
    # then meets the store's same-id rule at commit — the copy's content differs from the
    # stored row by its link, so the WHOLE import refuses (0009 §4c), loudly, nothing written
    Q2 = _proc_edge("Rotate keys often.", "e-Q2", "host")
    with pytest.raises(ValueError, match="already exists with different content"):
        run(file_q + [copy("e-P", supersedes="e-Q2"), by["e-S"]], "agree", seed + [Q2])
    # mutant: an UNSTAMPED stored predecessor (no producer) takes the claimed chain's producer —
    # a claim can only ADD a constraint: the extractor successor restores, the host one refuses
    P_unstamped = _proc_edge("Rotate keys.", "e-P", None)
    seed3 = [P_unstamped] + ([Q_ext] if q_where == "stored" else [])
    P_claim_unstamped = copy("e-P", supersedes="e-Q"); P_claim_unstamped["provenance"].pop("producer", None)
    assert run(file_q + [P_claim_unstamped, S_ext], "unstamped-x", seed3) == (
        {"e-P": (None, None), "e-Q": ("extractor", None), "e-S": ("extractor", "e-P")},
        [("e-P", "inheritance_violation", "producer")])
    assert run(file_q + [P_claim_unstamped, by["e-S"]], "unstamped-h", seed3) == (
        {"e-P": (None, None), "e-Q": ("extractor", None)},
        [("e-P", "inheritance_violation", "producer"), ("e-S", "inheritance_violation", "producer")])
