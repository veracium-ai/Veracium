"""specs/0055: credential-shaped text is never stored — the build's integration invariants (I1, I2, I4-I8, I10-I20).

The recogniser's own invariants (I1-I3 and I8 on the table, I9's timing) are tests/test_0055_recogniser.py. This file
drives the PRODUCT: every free-text field of §4b's entry points, the identifier refusals, the model-output and derived
writes, the store guard, the read backstop, import, the finder and its remedy, the outward-error boundaries, the
digests over caller input and the `record_procedure` twin. Each test states the RED it holds (the spec's "RED against"
column) in its docstring.

No structural test token appears literally: vectors.py assembles them at run time.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

from veracium import EvidenceAuthor, EvidenceContext, Memory, MemoryConfig
from veracium import credentials as C
from veracium.audit import AuditLog

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


V = _load("_0055_vectors_inv", ROOT / "specs" / "evidence" / "0055" / "vectors.py")
POSITIVE = [(rid, t) for rid, g, t, e in V.ROWS if e and g != "limit"]
NEAR_MISS = [(rid, t) for rid, g, t, e in V.ROWS if g == "near-miss"]
# the secret values each positive row carries (substring, after removing the zero-width space): the property is that
# none survives, not merely that a class was reported
ZW = "​"


def _secrets_in(text: str, *, short: bool = True) -> list:
    """The table's secret values present in `text`. A value under seven characters (the PINs, "4821") occurs by chance
    inside ids and hex digests, so `short=False` leaves those out; `_stored_text` checks them where text is stored."""
    flat = text.replace(ZW, "")
    return [sv for sv in V.SECRET_VALUES if (short or len(sv) >= 7) and sv in flat]


def _stored_text(db: str) -> str:
    """The stored TEXT fields only (edge subject/object/note, episode summary, journal states' same fields, reply
    text, the wiki): where a short secret could be stored, without the ids and digests it collides with by chance."""
    con = sqlite3.connect(db)
    out = []
    try:
        for (js,) in con.execute("SELECT json FROM edges UNION ALL SELECT state FROM edge_event"):
            try:
                d = json.loads(js)
            except (TypeError, ValueError):
                continue
            out += [str(d.get(k) or "") for k in ("subject", "object", "note")] if isinstance(d, dict) else []
        for (js,) in con.execute("SELECT json FROM episodes UNION ALL SELECT state FROM episode_event"):
            try:
                d = json.loads(js)
            except (TypeError, ValueError):
                continue
            out.append(str(d.get("summary") or "") if isinstance(d, dict) else "")
        out += [t or "" for (t,) in con.execute("SELECT text FROM replies")]
        out += [t or "" for (t,) in con.execute("SELECT text FROM wiki")]
    finally:
        con.close()
    return "\n".join(out)


def _leaks(db: str) -> list:
    return _secrets_in(_dump(db), short=False) + _secrets_in(_stored_text(db))


class Stub:
    """A recording provider: the extractor answers one ordinary triple and ECHOES the whole prompt into its episode
    summary (the most exposing answer a model can give), the retry and the gate answer plainly; every prompt is
    recorded for the egress checks."""

    def __init__(self, *, extra_triple=None, raise_on=None):
        self.prompts: list = []
        self.extra = extra_triple
        self.raise_on = raise_on

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        self.prompts.append((role, prompt))
        if self.raise_on == role:
            raise RuntimeError("provider failed while handling: " + prompt)      # an error that echoes the prompt
        if role == "distill":
            triples = [{"subject": "user", "relation": "located_at", "object": "Denver", "volatility": "durable"}]
            if self.extra is not None:
                triples.append(self.extra)
            return json.dumps({"episode": "noted: " + prompt[-600:], "triples": triples})
        if role == "compile":
            return json.dumps({"records": []}) if "consolidat" in (system or "").lower() else "wiki body"
        return "I don't know"


def _needs_mcp():
    """The served-surface tests need the MCP SDK (the `mcp` extra); the floor lane installs none."""
    pytest.importorskip("mcp")


def _mem(tmp_path, name="m", **kw):
    llm = kw.pop("llm", None) or Stub()
    return Memory(llm=llm, config=MemoryConfig(db_path=str(tmp_path / f"{name}.db"), wiki_recompile_after_writes=0),
                  **kw)


def _dump(db: str) -> str:
    """Every text cell of every table (the research probe's scan), as one string."""
    con = sqlite3.connect(db)
    try:
        return "\n".join(con.iterdump())
    finally:
        con.close()


def _dump_digest(db: str) -> str:
    return hashlib.sha256(_dump(db).encode()).hexdigest()


_SEEDED = [0]


def _seed_edge(mem, uid="u", text="I live in Denver"):
    """One ordinary, assertable user edge whose object is `text`, written through the store (the stub extractor
    answers the same triple for every event, so `remember` would merge seeds), with a source id as `remember` gives."""
    from veracium.schema import Edge, Provenance
    _SEEDED[0] += 1
    e = Edge(id=f"e-seed{_SEEDED[0]:06d}", user_id=uid, subject="user", relation="located_at", object=text,
             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"ev-seed{_SEEDED[0]}",
                                   source_id="chat"))
    mem.store.add_edge(e)
    return e


def _plant(db: str, edge_id: str, **fields):
    """A LEGACY value: written straight into the row (and its journal snapshot), as a pre-0055 store holds it."""
    con = sqlite3.connect(db)
    try:
        js = json.loads(con.execute("SELECT json FROM edges WHERE id=?", (edge_id,)).fetchone()[0])
        for k, v in fields.items():
            if k in ("source_id", "evidence_ref"):
                js["provenance"][k] = v
            else:
                js[k] = v
        con.execute("UPDATE edges SET json=?, subject=?, relation=?, object=? WHERE id=?",
                    (json.dumps(js), js["subject"], js["relation"], js["object"], edge_id))
        con.execute("UPDATE edge_event SET state=? WHERE edge_id=? AND seq=(SELECT MAX(seq) FROM edge_event "
                    "WHERE edge_id=?)", (json.dumps(js), edge_id, edge_id))
        con.commit()
    finally:
        con.close()


# ---- I1 / I2: every positive row through every free-text field; every near-miss byte for byte --------------------

def _through(field_name, mem, uid, text):
    if field_name == "remember":
        return mem.remember(uid, text, context=EvidenceContext.direct())
    if field_name == "record_procedure.summary":
        # the summary is capped at 512 characters (0037): a row that does not fit is checked through `note`
        field_name = "record_procedure.summary" if len(text) <= 480 else "record_procedure.note"
    if field_name == "record_procedure.summary":
        return mem.record_procedure_report(uid, "I run the tests first " + text, author=EvidenceAuthor.USER,
                                           context=EvidenceContext.direct(basis="stated"))
    if field_name == "record_procedure.note":
        return mem.record_procedure_report(uid, "I run the tests first", note=text, author=EvidenceAuthor.USER,
                                           context=EvidenceContext.direct(basis="stated"))
    e = _seed_edge(mem, uid)
    if field_name == "dispute.reason":
        return mem.dispute(uid, e.id, reason=text)
    if field_name == "reply.text":
        return mem.reply(uid, e.id, kind="context", text=text)
    if field_name == "record_outcome.corrected_value":
        return mem.record_outcome(uid, e.id, outcome="corrected", actor="user", evidence_ref="run-1",
                                  corrected_value=text)
    raise AssertionError(field_name)


FREE_TEXT_FIELDS = ("remember", "record_procedure.summary", "record_procedure.note", "dispute.reason", "reply.text",
                    "record_outcome.corrected_value")


@pytest.mark.parametrize("field_name", FREE_TEXT_FIELDS)
def test_i1_no_secret_byte_survives_any_free_text_field(tmp_path, field_name):
    """I1: every positive row of the table through the field; afterwards no secret value is in any text cell of any
    table (edge_event.state included), and the result reports the field. RED against: the field left unscreened."""
    mem = _mem(tmp_path)
    for n, (rid, text) in enumerate(POSITIVE):
        r = mem_r = _through(field_name, mem, f"u{n}", text)
        cw = mem_r.get("credentials_withheld") if isinstance(r, dict) else None
        assert cw, f"{rid}: nothing reported for {field_name}"
        assert set(cw) and all(set(v) <= C.CLASSES for v in cw.values()), cw
    mem.close()
    leaked = _leaks(str(tmp_path / "m.db"))
    assert not leaked, [s[:6] for s in leaked]


def test_i2_near_misses_are_stored_byte_for_byte(tmp_path):
    """I2: a near-miss reaches the extractor and the stored episode unchanged, with no report. RED against: a stop
    list removed (K6), a case-insensitive PIN (K35)."""
    stub = Stub()
    mem = _mem(tmp_path, llm=stub)
    for rid, text in NEAR_MISS:
        r = mem.remember("u", text, context=EvidenceContext.direct())
        assert "credentials_withheld" not in r, rid
        assert text in stub.prompts[-1][1], rid
    mem.close()


# ---- I4: identifier fields refuse whole, nothing written ----------------------------------------------------------

def _shaped():
    return V.DBURL


def _identifier_calls():
    s = _shaped()
    yield "remember.source_id", lambda m, e: m.remember("u", "hi", source_id=s, context=EvidenceContext.direct())
    yield "remember.evidence_ref", lambda m, e: m.remember("u", "hi", evidence_ref=s, context=EvidenceContext.direct())
    yield "remember.event_type", lambda m, e: m.remember("u", "hi", event_type=s, context=EvidenceContext.direct())
    yield "record_procedure.source_id", lambda m, e: m.record_procedure(
        "u", "I run tests", author=EvidenceAuthor.USER, context=EvidenceContext.direct(basis="stated"), source_id=s)
    yield "record_procedure.evidence_ref", lambda m, e: m.record_procedure(
        "u", "I run tests", author=EvidenceAuthor.USER, context=EvidenceContext.direct(basis="stated"),
        evidence_ref=s)
    yield "correct.corrected_value", lambda m, e: m.correct("u", e.id, "Boulder " + s)
    yield "correct.actor", lambda m, e: m.correct("u", e.id, "Boulder", actor=s)
    yield "correct.evidence_ref", lambda m, e: m.correct("u", e.id, "Boulder", evidence_ref=s)
    yield "correct.source_id", lambda m, e: m.correct("u", e.id, "Boulder", source_id=s)
    yield "dispute.actor", lambda m, e: m.dispute("u", e.id, actor=s)
    yield "dispute.source_id", lambda m, e: m.dispute("u", e.id, source_id=s)
    yield "confirm.correlation_id", lambda m, e: m.confirm("u", e.id, correlation_id="AK" + "IA" + "IOSFODNN7EXAMPLE")
    yield "confirm.source_id", lambda m, e: m.confirm("u", e.id, source_id=s)
    yield "reply.target", lambda m, e: m.reply("u", e.id, kind="resolve", target=s)
    yield "reply.correlation_id", lambda m, e: m.reply("u", e.id, kind="context", text="x",
                                                        correlation_id="AK" + "IA" + "IOSFODNN7EXAMPLE")
    yield "record_outcome.evidence_ref", lambda m, e: m.record_outcome("u", e.id, outcome="unreviewed", evidence_ref=s)
    yield "record_outcome.context_ref", lambda m, e: m.record_outcome("u", e.id, outcome="unreviewed", evidence_ref="r",
                                                                       context_ref=s)
    yield "undo_restoration.correlation_id", lambda m, e: m.undo_restoration(
        "u", e.id, correlation_id="AK" + "IA" + "IOSFODNN7EXAMPLE")


@pytest.mark.parametrize("name,call", list(_identifier_calls()), ids=[n for n, _ in _identifier_calls()])
def test_i4_an_identifier_with_a_shape_refuses_whole_and_writes_nothing(tmp_path, name, call):
    """I4: `CredentialRefused` naming the field and class; the store's every row is byte-identical before and after.
    RED against: a build that withholds instead of refusing."""
    mem = _mem(tmp_path)
    e = _seed_edge(mem)
    db = str(tmp_path / "m.db")
    before = _dump_digest(db)
    with pytest.raises(C.CredentialRefused) as ei:
        call(mem, e)
    assert ei.value.reason == "credential_refused"
    assert ei.value.field == name.split(".", 1)[1]
    assert V.DBURL not in str(ei.value) and "IOSFODNN7" not in str(ei.value)
    assert _dump_digest(db) == before
    mem.close()


# ---- I5: the model-output screen ----------------------------------------------------------------------------------

def test_i5_a_model_triple_carrying_a_shape_writes_no_edge_and_is_counted(tmp_path):
    """I5: a stub extractor returns a triple carrying S1's shape for an input with none: no edge carries it, the
    result reports it under `extracted_fact`, and the AuditLog counts it as a refusal with source model_output. RED
    against: the screen moved after the write."""
    stub = Stub(extra_triple={"subject": "user", "relation": "located_at",
                              "object": "key " + V.AWS_ID, "volatility": "durable"})
    log = tmp_path / "audit.jsonl"
    mem = _mem(tmp_path, llm=stub, audit=AuditLog(log))
    r = mem.remember("u", "I live in Denver", context=EvidenceContext.direct())
    assert r["credentials_withheld"]["extracted_fact"] == {"aws_access_key_id": 1}
    assert all(V.AWS_ID not in e.object for e in mem.store.edges("u", active_only=False))
    refused = [e for e in AuditLog(log).entries(op="credential_refused")]
    assert refused and refused[0]["source"] == "model_output" and refused[0]["field"] == "extracted_fact"
    mem.close()
    assert V.AWS_ID not in _dump(str(tmp_path / "m.db"))


# ---- I6: import ---------------------------------------------------------------------------------------------------

def _export_with(tmp_path, *, note=None, source_id=None):
    mem = _mem(tmp_path, "src")
    mem.remember("u", "I live in Denver", context=EvidenceContext.direct(), source_id="chat")
    e = sorted(mem.store.edges("u"), key=lambda x: x.id)[0]
    fields = {}
    if note is not None:
        fields["note"] = note
    if source_id is not None:
        fields["source_id"] = source_id
    _plant(str(tmp_path / "src.db"), e.id, **fields)
    out = tmp_path / f"export-{len(fields)}-{bool(source_id)}.jsonl"
    mem.export_memory("u", str(out))
    mem.close()
    return out, e.id


def test_i6_plain_import_withholds_and_restore_refuses_unless_flagged(tmp_path):
    """I6: a plain import withholds per field; a restore with any shape refuses whole naming the records; with
    `withhold_credentials=True` it restores, withholds the free text and lists exactly the affected record; every
    unlisted record is byte-identical to the backup; an identifier with a shape still refuses under the flag. RED
    against: a restore that masks without the flag; a receipt that omits an affected id."""
    from veracium.portability import CredentialImportRefused
    path, eid = _export_with(tmp_path, note="wifi password: hunter2")
    m1 = _mem(tmp_path, "plain")
    r = m1.import_memory(str(path), user_id="v")
    assert r["credentials_withheld"] == {"edge.note": {"labelled_password": 1}}
    m1.close()
    assert "hunter2" not in _dump(str(tmp_path / "plain.db"))
    m2 = _mem(tmp_path, "restore")
    with pytest.raises(CredentialImportRefused) as ei:
        m2.import_memory(str(path), restore=True)
    assert ei.value.records == [f"edge {eid}"] and "hunter2" not in str(ei.value)
    assert not m2.store.edges("u", active_only=False)                                   # nothing written
    r = m2.import_memory(str(path), restore=True, withhold_credentials=True)
    assert [x["locator"] for x in r["credentials_withheld_records"]] == [f"edge {eid}"]
    m2.close()
    dump = _dump(str(tmp_path / "restore.db"))
    assert "hunter2" not in dump
    # unlisted records byte-identical: the episode the source holds is restored as written
    src_eps = [l for l in path.read_text().splitlines() if '"record": "episode"' in l or '"kind": "episode"' in l]
    m3 = _mem(tmp_path, "restore")
    for line in src_eps:
        rec = json.loads(line)
        got = [e for e in m3.store.episodes("u", include_retired=True) if e.id == rec["id"]]
        assert got and got[0].summary == rec["summary"]
    m3.close()
    ipath, _ = _export_with(tmp_path, source_id=V.DBURL)
    m4 = _mem(tmp_path, "ident")
    with pytest.raises(CredentialImportRefused) as ei:
        m4.import_memory(str(ipath), restore=True, withhold_credentials=True)
    assert ei.value.identifiers
    r = m4.import_memory(str(ipath), user_id="w")              # the route: a plain import refuses that record
    assert r["credential_refused"] >= 1 and r["credential_refused_records"][0]["class"] == "url_userinfo_password"
    m4.close()
    assert V.DBURL not in _dump(str(tmp_path / "ident.db"))


# ---- I7: the read backstop ----------------------------------------------------------------------------------------

def test_i7_no_legacy_credential_reaches_a_model_or_a_tool_result(tmp_path):
    """I7: a store seeded with legacy credentials (written past every screen); recall, find_facts, why, answer,
    compile, consolidation and the embedder each run; every captured provider payload and every tool result is free
    of them. RED against: one read path left unmasked."""
    from veracium import why as _why
    from veracium.mcp_server import find_facts_impl, describe_procedures_impl
    stub = Stub()
    embedded: list = []

    class Emb:
        def id(self):
            return "stub-embed-1"

        def dim(self):
            return 4

        def __call__(self, texts):
            embedded.extend(texts)
            return [[1.0, 0.5, 0.25, 0.125] for _ in texts]
    mem = Memory(llm=stub, embed=Emb(), config=MemoryConfig(db_path=str(tmp_path / "m.db"),
                                                             wiki_recompile_after_writes=0))
    e = _seed_edge(mem)
    _plant(str(tmp_path / "m.db"), e.id, object="Denver; db password: hunter2 and " + V.GH,
           note="token " + V.STRIPE)
    # the no-query briefing (proactive) renders a TRANSIENT fact in CURRENT CONTEXT and leaves a durable one out, so
    # the read path it masks is driven by a transient legacy record (2026-11-23: with only the durable seed the
    # briefing read "(nothing needs attention)", and a mutant removing proactive's read mask survived this test)
    from veracium.schema import Edge, Provenance, Volatility
    t = Edge(id="e-i7-transient", user_id="u", subject="user", relation="feeling", object="tired",
             volatility=Volatility.TRANSIENT,
             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-i7", source_id="chat"))
    mem.store.add_edge(t)
    _plant(str(tmp_path / "m.db"), t.id, object="tired; my password: hunter2 and " + V.GH)
    briefing = mem.recall("u").context
    assert "## CURRENT CONTEXT" in briefing and "[credential withheld" in briefing, briefing
    results = [mem.recall("u", "where does the user live").context, briefing,
               json.dumps(find_facts_impl(mem, "u", "where", capability="direct"), default=str),
               json.dumps(describe_procedures_impl(mem, "u"), default=str),
               _why.render(_why.gather(mem.store, "u", e.id)),
               json.dumps(_why.find(mem.store, "u", "Denver"), default=str),
               str(mem.answer("u", "where does the user live"))]
    mem.embed_backfill("u")
    from veracium import compile as _compile
    _compile.compile_wiki(mem.store, stub, "u", mem.config.relations)
    payloads = [p for _role, p in stub.prompts] + embedded + results
    for p in payloads:
        assert not _secrets_in(p) and V.STRIPE not in p, p[:200]
    mem.close()


# ---- I8: no report sink carries the value, and the counts are exact -----------------------------------------------

def _canaries(value: str) -> list:
    return [value, value[:4], value[-4:], hashlib.sha256(value.encode()).hexdigest(),
            hashlib.sha256(value.encode()).hexdigest()[:16]]


#: the report vocabulary: a sink's string that is one of these names a field, a class or an audit key, never a value
#: (the `github_pat_` / `github_token` collision control: a value's first four characters may spell a class name)
VOCAB = (set(C.CLASSES) | {"event_text", "summary", "note", "reason", "text", "corrected_value", "extracted_fact",
                           "episode", "ts", "op", "user_id", "surface", "operation", "field", "source",
                           "shapes_version", "classes", "class", "credential_withheld", "credential_refused",
                           "caller", "library", "remember", "u", "model_output", "derived", "source_id"})


def _outside_vocab(sink: str) -> str:
    """The strings of a sink outside the vocabulary, joined: canary checks run over these only (I8)."""
    try:
        doc = json.loads(sink)
    except ValueError:
        doc = None
    if doc is None:
        words = sink.replace(":", " ").split()
        return " ".join(w for w in words if w not in VOCAB)
    out = []

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(k)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str) and x not in VOCAB:
            out.append(x)
    walk(doc)
    return " ".join(out)


def test_i8_every_sink_holds_only_field_names_class_names_and_exact_counts(tmp_path):
    """I8: the result's report, the AuditLog lines and the refusal text are held to their schemas (field names,
    class names, positive counts, the closed audit keys); no canary of the value (the value, its first and last four,
    its sha256 and sha16) appears in any of them; every count is the row's exact expected report. RED against: a
    report carrying a length, an offset, a prefix or a digest; a cumulative count."""
    log = tmp_path / "audit.jsonl"
    mem = _mem(tmp_path, audit=AuditLog(log))
    sinks = []
    for rid, g, text, expect in V.ROWS:
        if not expect or g == "limit":
            continue
        r = mem.remember("u", text, context=EvidenceContext.direct())
        assert r["credentials_withheld"]["event_text"] == V.expected_report(rid, expect), rid
        sinks.append(json.dumps(r["credentials_withheld"]))
    try:
        mem.remember("u", "hi", source_id=V.DBURL, context=EvidenceContext.direct())
    except C.CredentialRefused as exc:
        sinks.append(str(exc))
    audit_lines = log.read_text().splitlines()
    for ln in audit_lines:
        rec = json.loads(ln)
        if rec["op"] in ("credential_withheld", "credential_refused"):
            assert set(rec) <= {"ts", "op", "user_id", "surface", "operation", "field", "source", "shapes_version",
                                "classes", "class"}, rec
            for c, n in (rec.get("classes") or {}).items():
                assert c in C.CLASSES and isinstance(n, int) and n > 0
        sinks.append(ln)
    mem.close()
    long_secrets = [sv for sv in V.SECRET_VALUES if len(sv) >= 37]
    for sink in sinks:
        rest = _outside_vocab(sink)
        for sv in long_secrets:
            for canary in _canaries(sv):
                assert canary not in rest, (canary[:6], rest[:120])


# ---- I10: every surface --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("capability", [None, "direct"])
def test_i10_the_rule_holds_through_mcp_and_the_adapter_binding(tmp_path, capability):
    """I10: the table's positive rows through the served `remember` (MCP's tool function) and through a 0053
    adapter's Binding, under `none` and `direct`: no secret at rest, the report in the served result. RED against: a
    surface that bypasses the library entry point."""
    _needs_mcp()
    from veracium.adapters._surface import Binding
    from veracium.mcp_server import build_server
    mem = _mem(tmp_path)
    server = build_server(mem, capability=capability, source_id="chat")
    binding = Binding(mem, capability=capability, source_id="chat")
    for n, (rid, text) in enumerate(POSITIVE[:30]):
        out = asyncio.run(server.call_tool("remember", {"text": text}))
        body = json.loads(out[0].text) if isinstance(out, list) else out
        assert "credentials_withheld" in json.dumps(body), rid
        r = binding.call("remember", {"text": text})
        assert r.get("credentials_withheld"), rid
    mem.close()
    assert not _leaks(str(tmp_path / "m.db"))


# ---- I12: the screen runs before the distill call, the degrade hash and any digest -------------------------------

def test_i12_neither_the_provider_nor_the_degrade_callback_sees_a_value_or_its_sha16(tmp_path):
    """I12: a recording provider and a recording `on_degrade` (via the diagnostics hook): no prompt carries a positive
    row's value, and no degrade payload carries its sha16 — including the provider-exception site, driven by a
    provider whose exception message echoes the whole prompt. RED against: the screen moved after `distill`."""
    seen: list = []

    class Rec:
        def record_degrade(self, where, kind, fields):
            seen.append(json.dumps(fields))

        def record_error(self, where, exc, ctx):
            seen.append(str(exc))
    stub = Stub(raise_on="distill-retry")
    mem = Memory(llm=stub, config=MemoryConfig(db_path=str(tmp_path / "m.db"), wiki_recompile_after_writes=0),
                 diagnostics=Rec())
    for rid, text in POSITIVE:
        mem.remember("u", text, context=EvidenceContext.direct())
    for _role, p in stub.prompts:
        assert not _secrets_in(p), p[:120]
    sha16s = {hashlib.sha256(sv.encode()).hexdigest()[:16] for sv in V.SECRET_VALUES}
    for payload in seen:
        assert not any(h in payload for h in sha16s)
    mem.close()


# ---- I13: the store guard -----------------------------------------------------------------------------------------

def test_i13_the_guard_refuses_an_introduced_shape_and_passes_transitions_over_a_legacy_row(tmp_path):
    """I13: a legacy edge carrying S1's shape (guard off: planted), then invalidate, expire-shaped writes, confirm,
    dispute and 0041 redaction of it with the guard on: all succeed; an `add_edge` carrying a shape:
    `CredentialRefused`. RED against: a guard on PRESENT rather than INTRODUCED (dispute of the legacy row fails)."""
    mem = _mem(tmp_path)
    e = _seed_edge(mem)
    _plant(str(tmp_path / "m.db"), e.id, object="key " + V.AWS_ID)
    mem.confirm("u", e.id)
    mem.record_outcome("u", e.id, outcome="unreviewed", evidence_ref="run-1")
    mem.dispute("u", e.id, reason="wrong")
    e2 = _seed_edge(mem, text="I work at Acme")
    _plant(str(tmp_path / "m.db"), e2.id, object="key " + V.AWS_ID)
    mem.redact("u", edge_id=e2.id, reason="operator_policy")
    fresh = mem.store.edges("u")[0] if mem.store.edges("u") else None
    from veracium.schema import Edge, Provenance
    bad = Edge(id="e-guardprobe1", user_id="u", subject="user", relation="located_at", object="token " + V.GH,
               provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-x"))
    with pytest.raises(C.CredentialRefused):
        mem.store.add_edge(bad)
    assert fresh is None or V.GH not in _dump(str(tmp_path / "m.db"))
    mem.close()


# ---- I14: the two-step erase survives every screen ----------------------------------------------------------------

def test_i14_preview_then_confirm_completes_and_a_pasted_token_is_withheld(tmp_path):
    """I14: `forget_everything_preview` then `forget_everything_confirm` with the returned token, through the library,
    MCP's implementation and an adapter Binding: the erase completes. A `tt1` token pasted into `remember` is caller
    text and is withheld. RED against: §4e applied to the preview result; `preview_token` screened at ingress."""
    from veracium.trust_tools import PreviewTokenIssuer
    mem = _mem(tmp_path)
    _seed_edge(mem)
    issuer = PreviewTokenIssuer(mem.store.local_origin(), "u")
    p = mem.forget_everything_preview("u", issuer=issuer)
    r = mem.forget_everything_confirm("u", p["preview_token"], issuer=issuer)
    assert not mem.store.edges("u", active_only=False), r
    _seed_edge(mem, "v")
    tok = PreviewTokenIssuer(mem.store.local_origin(), "v")
    p = mem.forget_everything_preview("v", issuer=tok)
    w = mem.remember("w", "confirm with " + p["preview_token"], context=EvidenceContext.direct())
    assert w["credentials_withheld"]["event_text"] == {"veracium_preview_token": 1}
    _needs_mcp()
    from veracium.adapters._surface import Binding
    b = Binding(mem, user_id="v", capability="direct")
    pv = b.call("forget_everything_preview", {})
    assert pv["ok"], pv
    cf = b.call("forget_everything_confirm", {"preview_token": pv["preview_token"]})
    assert cf["ok"], cf
    mem.close()


# ---- I15: provenance_raises_discarded reaches the AuditLog and never a tool result --------------------------------

def test_i15_the_discarded_raise_count_reaches_the_audit_log(tmp_path, monkeypatch):
    """I15: under `none` with an elevation claim, through the stock server's AuditLog (VERACIUM_AUDIT_LOG, read by
    `build_memory`) and an adapter's `audit_log`: the log holds the count per tool; the tool result lacks the key.
    RED against: `_record` after the strip; the strip removed."""
    _needs_mcp()
    from veracium import mcp_server
    from veracium.adapters._surface import Binding
    log = tmp_path / "stock.jsonl"
    monkeypatch.setenv("VERACIUM_AUDIT_LOG", str(log))
    monkeypatch.setenv("VERACIUM_DB_PATH", str(tmp_path / "stock.db"))
    import veracium.llm.anthropic as _anth
    monkeypatch.setattr(_anth, "AnthropicComplete", lambda *a, **k: Stub())
    monkeypatch.setattr("veracium.telemetry.prompt_consent", lambda *a, **k: None)
    monkeypatch.setattr("veracium.diagnostics.prompt_consent", lambda *a, **k: None)
    monkeypatch.setattr("veracium.diagnostics.load_reporter", lambda *a, **k: None)
    monkeypatch.setattr("veracium.telemetry.load_collector_if_enabled", lambda *a, **k: None)
    mem = mcp_server.build_memory()
    assert mem.audit is not None
    r = mcp_server.remember_impl(mem, "u", "hi", author="user", capability=None, source_id="chat")
    assert "provenance_raises_discarded" not in r
    r = mcp_server.correct_fact_impl(mem, "u", "e-none", "x", capability=None)
    assert "provenance_raises_discarded" not in r
    lines = AuditLog(log).entries(op="provenance_raises_discarded")
    assert {(x["tool"], x["count"]) for x in lines} == {("remember", 1), ("correct_fact", 1)}
    mem.close()
    alog = tmp_path / "adapter.jsonl"
    m2 = _mem(tmp_path, "adapter")
    b = Binding(m2, capability=None, source_id="chat", audit_log=str(alog))
    b.call("remember", {"text": "hi", "author": "user"})
    got = AuditLog(alog).entries(op="provenance_raises_discarded")
    assert got and got[0]["surface"] == "adapter" and got[0]["count"] == 1
    m2.close()


# ---- I16: derived writes --------------------------------------------------------------------------------------------

def test_i16_composed_text_is_withheld_and_transitions_over_legacy_records_succeed(tmp_path):
    """I16: a legacy value in the fields census A's rows copy; dispute, confirm, record_outcome, correct and an
    absorbing `remember` with safe new arguments: every state change succeeds and no NEW row (outside the journal's
    declared snapshots) carries the value; `correct` is refused when the prior's subject carries one. RED against: the
    derived-write screen omitted (the copy reappears in the new summary)."""
    mem = _mem(tmp_path)
    secret = "key " + V.AWS_ID
    ids = []
    for t in ("I live in Denver", "I work at Acme", "I like tea", "I drive a Volvo"):
        e = _seed_edge(mem, text=t)
        ids.append(e.id)
    db = str(tmp_path / "m.db")
    for eid in ids:
        _plant(db, eid, object="value " + secret, note="note " + secret)
    mem.dispute("u", ids[0], reason="wrong")
    mem.confirm("u", ids[1])
    mem.record_outcome("u", ids[2], outcome="corrected", actor="user", evidence_ref="r1", corrected_value="tea")
    r = mem.correct("u", ids[3], "Saab")
    assert r["credentials_withheld"]["note"] == {"aws_access_key_id": 1}
    con = sqlite3.connect(db)
    try:
        eps = [row[0] for row in con.execute("SELECT json FROM episodes")]
        new_edges = [row[0] for row in con.execute("SELECT json FROM edges WHERE id=?", (r["replacement"],))]
    finally:
        con.close()
    assert not any(V.AWS_ID in x for x in eps + new_edges)
    e5 = _seed_edge(mem, text="I live in Paris")
    _plant(db, e5.id, subject="org:" + V.AWS_ID)
    with pytest.raises(C.CredentialRefused) as ei:
        mem.correct("u", e5.id, "Lyon")
    assert ei.value.field == "subject"
    mem.close()


# ---- I17: outward paths never echo caller input; reports name a shaped id by ordinal -----------------------------

CANARY = "ZZCANARY-7731"


def test_i17_served_and_cli_errors_never_echo_the_argument(tmp_path, capsys):
    """I17: the canary in each argument of the served tools (MCP's tool boundary and the SDK's own validation, an
    adapter Binding) and of the CLI: no canary in any error text, `detail`, tool error or CLI stream. RED against: the
    formatter bypassed at one boundary; `hide_input_in_errors` unset."""
    _needs_mcp()
    from veracium.adapters._surface import Binding
    from veracium.cli import main
    from veracium.mcp_server import build_server
    mem = _mem(tmp_path)
    server = build_server(mem, capability="direct", source_id="chat")
    calls = [("remember", {"text": "hi", "author": CANARY}), ("remember", {"text": "hi", "derived_from": CANARY}),
             ("remember", {"text": "hi", "date": CANARY}), ("remember", {"text": 7731, "author": "user"}),
             ("recall", {"token_budget": CANARY}), ("record_procedure", {"summary": "x", "basis": CANARY}),
             ("record_procedure", {"summary": "x", "basis": "stated", "relation": CANARY}),
             ("record_procedure", {"summary": "x", "basis": "stated", "date": CANARY}),
             ("forget_fact", {"edge_id": 7731}), ("correct_fact", {"edge_id": CANARY, "corrected_value": "x"}),
             ("dispute_fact", {"edge_id": CANARY, "reason": "x"})]
    b = Binding(mem, capability="direct", source_id="chat")
    for name, args in calls:
        try:
            out = asyncio.run(server.call_tool(name, args))
            text = json.dumps(out, default=str)
        except Exception as exc:                                     # noqa: BLE001 - the error text is the subject
            text = str(exc)
        assert CANARY not in text and "7731" not in text, (name, text[:200])
        try:
            text = json.dumps(b.call(name, args), default=str)
        except Exception as exc:                                     # noqa: BLE001
            text = str(exc)
        assert CANARY not in text, (name, text[:200])
    mem.close()
    for argv in (["export", "--db", str(tmp_path / "c.db"), "--user", "u", str(tmp_path / CANARY / "x.jsonl")],
                 ["import", "--db", str(tmp_path / "c.db"), str(tmp_path / f"{CANARY}.jsonl")]):
        rc = main(argv)
        out = capsys.readouterr()
        assert rc != 0 and CANARY not in out.out + out.err, (argv[0], out.err[-200:])


def test_i17_a_cli_defect_raises_as_itself_with_its_message_withheld(monkeypatch, capsys):
    """E1 at the CLI, split by kind: a refusal is one line and exit 1 (the test above); any other exception inside a
    verb is a DEFECT, re-raised as itself (its type, its attributes, its traceback) with its message withheld and the
    chain it was raised during suppressed, because either may quote the input. It is never turned into a clean exit.
    RED against: the first build's catch-all, which printed every exception as one line and returned 1, so an unrelated
    crash read as a clean refusal (and the 0018 record's `CTRL-unrelated-TypeError` control read KILLED); and against a
    re-raise that keeps the message or the chain."""
    import traceback

    from veracium import cli

    class _Defect(TypeError):
        pass

    def broken_verb(args, d):
        try:
            raise KeyError(CANARY)
        except KeyError:
            err = _Defect(f"unsupported operand {CANARY}")
            err.marker = "kept"
            raise err

    monkeypatch.setitem(cli._VERBS, "selfcheck", broken_verb)
    with pytest.raises(_Defect) as ei:
        cli.main(["selfcheck"])
    exc = ei.value
    shown = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    out = capsys.readouterr()
    assert exc.marker == "kept" and exc.__suppress_context__ and exc.__cause__ is None
    assert "broken_verb" in shown                       # the traceback is the defect's own
    assert CANARY not in str(exc) and CANARY not in shown, shown[-300:]
    assert CANARY not in out.out + out.err


def test_i17_the_diagnostics_log_is_masked(tmp_path):
    """I17 / E3: an exception carrying a credential-shaped argument is logged with its traceback, masked; the send
    path masks too. RED against: the log written from `str(exc)` unmasked."""
    from veracium.diagnostics import DiagnosticsConfig, Reporter
    cfg = DiagnosticsConfig(log_path=str(tmp_path / "v.log"), log_enabled=True)
    rep = Reporter(cfg)
    rep.record_error("remember", ValueError(f"bad date {V.GH!r}"), {"user_hash": "x"})
    text = (tmp_path / "v.log").read_text()
    assert V.GH not in text and "credential withheld" in text
    assert V.GH not in rep.log_tail()


def test_i17_a_shaped_record_id_is_reported_by_ordinal_and_still_acted_on(tmp_path):
    """§4g's locator rule: the finder names a record whose id carries a shape by a per-report ordinal, never the id,
    and the remedy still redacts it by its raw id. RED against: a report printing the raw id."""
    from veracium import credential_finder as cf
    mem = _mem(tmp_path)
    e = _seed_edge(mem)
    db = str(tmp_path / "m.db")
    shaped_id = "e-" + V.GH
    con = sqlite3.connect(db)
    js = json.loads(con.execute("SELECT json FROM edges WHERE id=?", (e.id,)).fetchone()[0])
    js["id"] = shaped_id
    js["note"] = "password: hunter2"
    con.execute("UPDATE edges SET id=?, json=? WHERE id=?", (shaped_id, json.dumps(js), e.id))
    con.execute("UPDATE edge_event SET edge_id=? WHERE edge_id=?", (shaped_id, e.id))
    con.commit()
    con.close()
    hits = cf.scan(mem.store, "u")
    rep = json.dumps(cf.report(hits))
    assert V.GH not in rep and "record 1 of this report" in rep
    lines = cf.act(mem, hits)
    assert any(x["outcome"] == "redacted" for x in lines) and V.GH not in json.dumps(lines)
    mem.close()


# ---- I18: the remedy reports its residual honestly ----------------------------------------------------------------

def test_i18_redact_removes_what_0041_can_and_reports_the_residual(tmp_path, capsys):
    """I18: matches in a text field, a provenance identifier, a reply's text only and a journal event only; `veracium
    credentials redact --yes`: the removable carriers re-scan clean, the identifier is reported as residual and the CLI
    exits nonzero; then `forget_user` removes the residual. RED against: a remedy that trusts the 0041 receipt
    without the second scan; a reply match not mapped to its parent."""
    from veracium import credential_finder as cf
    from veracium.cli import main
    mem = _mem(tmp_path)
    a = _seed_edge(mem, text="I live in Denver")
    b = _seed_edge(mem, text="I work at Acme")
    c = _seed_edge(mem, text="I like tea")
    db = str(tmp_path / "m.db")
    _plant(db, a.id, note="password: hunter2")
    _plant(db, b.id, source_id=V.DBURL)
    con = sqlite3.connect(db)
    con.execute("UPDATE edge_event SET state=REPLACE(state, 'tea', 'tea; token: Ab3dEf9hJk2L') WHERE edge_id=?",
                (c.id,))
    con.commit()
    con.close()
    rr = mem.reply("u", c.id, kind="context", text="fine")
    con = sqlite3.connect(db)
    con.execute("UPDATE replies SET text=? WHERE id=?", ("my password is swordfish", rr["reply_id"]))
    con.commit()
    con.close()
    mem.close()
    rc = main(["credentials", "redact", "--db", db, "--yes"])
    out = capsys.readouterr().out
    assert rc == 1 and "residual" in out.lower()
    from veracium.store.sqlite import SqliteStore
    st = SqliteStore(db)
    after = cf.scan(st, "u")
    assert {h.carrier for h in after} <= set(cf.RESIDUAL), [h.carrier for h in after]
    st.forget_user("u")
    assert cf.scan(st, "u") == []
    st.close()


# ---- I19: digests over caller input ---------------------------------------------------------------------------------

def test_i19_revoke_source_refuses_an_unknown_shape_before_any_digest(tmp_path):
    """I19 / D3: `revoke_source` with an unknown credential-shaped source refuses before any digest (no revocation
    row, no audit line naming a digest, preview and commit alike, log attached and absent); with a legacy one of the
    same user it revokes and lifts, persisting only D3's digest. An invalid reason is refused before the digest. RED
    against: the digest before the screen; the reason check after it; `dry_run` returning a digest for an unknown
    shape."""
    for with_log in (False, True):
        log = tmp_path / f"a{with_log}.jsonl"
        mem = _mem(tmp_path, f"r{with_log}", **({"audit": AuditLog(log)} if with_log else {}))
        for dry in (True, False):
            with pytest.raises(C.CredentialRefused):
                mem.revoke_source("u", None, V.DBURL, "policy", dry_run=dry)
        assert mem.source_revocations("u")["history"] == []
        if with_log:
            assert not any("identity_digest" in ln for ln in log.read_text().splitlines())
        e = _seed_edge(mem)
        _plant(str(tmp_path / f"r{with_log}.db"), e.id, source_id=V.DBURL)
        with pytest.raises(ValueError) as ei:
            mem.revoke_source("u", None, V.DBURL, "not-a-reason")
        assert "not-a-reason" not in str(ei.value)
        assert mem.source_revocations("u")["history"] == []
        mem.revoke_source("u", None, V.DBURL, "policy")
        mem.unrevoke_source("u", None, V.DBURL, "revoked_in_error")
        assert len(mem.source_revocations("u")["history"]) == 2
        with pytest.raises(C.CredentialRefused):                  # another user's legacy record proves nothing
            mem.revoke_source("other", None, V.DBURL, "policy")
        mem.close()


def test_i19_correct_hashes_the_masked_note_and_the_reply_digest_is_over_masked_text(tmp_path):
    """I19 (census F rows: correct's projection, the reply request digest): the supersession plan and its raw request
    see the masked copied note; the reply request digest equals the digest of the withheld text. RED against:
    `correct` hashing the raw copied note."""
    from veracium.schema import reply_request_digest
    mem = _mem(tmp_path)
    e = _seed_edge(mem)
    _plant(str(tmp_path / "m.db"), e.id, note="password: hunter2")
    r = mem.correct("u", e.id, "Boulder")
    con = sqlite3.connect(str(tmp_path / "m.db"))
    try:
        blobs = [str(v) for t in ("supersession_operations", "contribution_ledger")
                 for row in con.execute(f"SELECT * FROM {t}") for v in row]
    finally:
        con.close()
    assert not any("hunter2" in b for b in blobs) and r["replacement"]
    e2 = _seed_edge(mem, text="I like tea")
    rr = mem.reply("u", e2.id, kind="context", text="my password is swordfish")
    con = sqlite3.connect(str(tmp_path / "m.db"))
    stored = con.execute("SELECT text, request_digest FROM replies WHERE id=?", (rr["reply_id"],)).fetchone()
    con.close()
    assert "swordfish" not in stored[0]
    assert stored[1] == reply_request_digest("u", e2.id, "context", None, stored[0])
    mem.close()


def test_i19_the_diagnostics_digest_is_over_masked_provider_text():
    """I19 / 0039 amendment `0055/0039-masked-diagnostic-digests`: `answer_len` and `answer_sha16` are over the masked
    provider text, and byte-identical to before on text with no shape. RED against: the digest over raw text."""
    from veracium.ingest import _answer_fields
    plain = "no json here, just prose"
    assert _answer_fields(plain) == {"answer_len": len(plain.encode()),
                                     "answer_sha16": hashlib.sha256(plain.encode()).hexdigest()[:16]}
    shaped = "the token is " + V.GH
    masked = C.mask(shaped)[0]
    assert _answer_fields(shaped)["answer_sha16"] == hashlib.sha256(masked.encode()).hexdigest()[:16]
    assert _answer_fields(shaped)["answer_sha16"] != hashlib.sha256(shaped.encode()).hexdigest()[:16]


def test_i19_the_embedding_digest_and_input_are_masked():
    """I19 / census F row 13: `content_digest` and `embedded_text` are over the masked text; unchanged on text with no
    shape. RED against: the raw digest on backfill (census F's W4)."""
    from veracium import semantic
    from veracium.schema import Edge, Provenance
    def mk(obj):
        return Edge(id="e-x", user_id="u", subject="user", relation="located_at", object=obj,
                    provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev"))
    plain = mk("Denver")
    assert semantic.content_digest(plain) == hashlib.sha256(json.dumps(
        {"note": "", "object": "Denver", "relation": "located_at", "subject": "user"}, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    shaped = mk("token " + V.GH)
    assert V.GH not in semantic.embedded_text(shaped)
    assert semantic.content_digest(shaped) == semantic.content_digest(mk(C.mask("token " + V.GH)[0]))


# ---- I20: record_procedure keeps its str; the twin reports ----------------------------------------------------------

def test_i20_record_procedure_keeps_its_str_and_the_twin_reports(tmp_path):
    """I20: `record_procedure` returns the id; `record_procedure_report` returns the id and the report; MCP's
    implementation and an adapter return the dict with the key; a refusal raises `CredentialRefused` with
    `.reason == "credential_refused"` and maps to the refusal dict on the served surfaces. RED against: the str API
    changed; the twin omitted on a served surface."""
    from veracium.mcp_server import record_procedure_impl
    mem = _mem(tmp_path)
    kw = dict(author=EvidenceAuthor.USER, context=EvidenceContext.direct(basis="stated"))
    eid = mem.record_procedure("u", "I run tests before pushing", **kw)
    assert isinstance(eid, str) and eid.startswith("e-")
    r = mem.record_procedure_report("u", "I run tests; password: hunter2", **kw)
    assert set(r) == {"edge_id", "credentials_withheld"} and r["credentials_withheld"] == {
        "summary": {"labelled_password": 1}}
    assert set(mem.record_procedure_report("u", "I stretch every morning", **kw)) == {"edge_id"}
    s = record_procedure_impl(mem, "u", "I run tests; password: hunter2", "stated", capability="direct")
    assert s["ok"] and s.get("credentials_withheld") == {"summary": {"labelled_password": 1}}, s
    refused = record_procedure_impl(mem, "u", "I run tests", "stated", capability="direct", source_id=V.DBURL)
    assert refused == {"ok": False, "refusal": "credential_refused", "field": "source_id",
                       "class": "url_userinfo_password"}
    with pytest.raises(C.CredentialRefused) as ei:
        mem.record_procedure("u", "I run tests", source_id=V.DBURL, **kw)
    assert ei.value.reason == "credential_refused"
    mem.close()
