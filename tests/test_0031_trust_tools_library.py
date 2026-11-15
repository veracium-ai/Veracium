"""specs/0031 §4f (amendment `0031/trust-tools-direct`, v23 + v23.1): the LIBRARY half of the trust tools.

What the four verbs do when a tool calls them: the agent call path recorded (INV-TT4, INV-TT5), the §3b scope gate
under a principal (INV-TT16 at the library, INV-TT18), the principal-facing redaction receipt (INV-TT19), and the
call-path export era (INV-TT23, v23.1). The tool surfaces (MCP, both adapters) are tested in their own file; every
check here names the mutant it kills, and each mutating case runs on its own fresh store (§6's oracle discipline).
"""
import hashlib
import json
from datetime import datetime, timezone

import pytest

from veracium import EvidenceContext, Memory, MemoryConfig
from veracium import portability
from veracium.schema import (ConfirmationCallPath as C, Edge, EvidenceAuthor, Provenance)
from veracium.scope import Identity
from veracium.trust_tools import NOT_FOUND_DETAIL, TrustRefused

U = "u"
A = Identity(None, "src-a")          # a principal in team-a
B = Identity(None, "src-b")          # a principal in team-b
LONER = Identity(None, "src-z")      # a principal in no group at all
LEGACY_PROV_KEYS = {"author_of_evidence", "evidence_ref", "observed_at", "disclosure", "confidence",
                    "derived_from", "source_id", "origin"}


class _Stub:
    def __call__(self, prompt, *, role="compile", **kw):
        if role == "distill":
            return json.dumps({"triples": [{"subject": "user", "relation": "located_at", "object": "Berlin",
                                            "volatility": "durable"}],
                               "episode": "The user said Berlin.", "instructions": []})
        return "summary"


def _mem(tmp_path, *, scoped=True, cross_visible=False):
    tmp_path.mkdir(parents=True, exist_ok=True)
    groups = {"team-a": [A], "team-b": [B]} if scoped else None
    kw = dict(db_path=str(tmp_path / "v.db"), require_source_id=False, wiki_recompile_after_writes=0)
    if groups is not None:
        kw.update(scope_groups=groups, cross_scope_visible=cross_visible)
    return Memory(llm=_Stub(), config=MemoryConfig(**kw))


def _edge(m, eid, obj, source_id=None, user=U):
    e = Edge(id=eid, user_id=user, subject="user", relation="likes", object=obj,
             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"ev-{eid}",
                                   source_id=source_id))
    m.store.add_edge(e)
    return e


def _digest(m) -> str:
    """Every row of every table: a refusal 'writes nothing' iff this is unchanged."""
    return hashlib.sha256("\n".join(m.store._conn.iterdump()).encode()).hexdigest()


def _episode(m, prefix):
    return next(e for e in m.store.episodes(U) if e.provenance.evidence_ref.startswith(prefix))


def _prov_json(record) -> dict:
    return json.loads(record.model_dump_json())["provenance"]


# ------------------------------------------------------------------ INV-TT4 / INV-TT5: the call path and the source
@pytest.mark.parametrize("path", [C.MCP_DIRECT, C.ADAPTER_DIRECT])
def test_confirm_records_the_agent_path_in_the_row_and_the_quoting_episode(tmp_path, path):
    """INV-TT4. Mutants: the library default left in place (the row reads host_api); the episode left unlabelled."""
    m = _mem(tmp_path, scoped=False)
    e = _edge(m, "e-1", "tea")
    m.confirm(U, e.id, call_path=path, source_id="src-a")
    assert m.store.confirmations_for(U, e.id)[0].call_path is path
    p = _prov_json(_episode(m, "confirm:"))
    assert p.get("call_path") == path.value and p.get("source_id") == "src-a", p


@pytest.mark.parametrize("verb", ["correct", "dispute"])
@pytest.mark.parametrize("source", [None, "src-a"])
def test_correct_and_dispute_audit_episodes_carry_the_path_and_source_in_provenance_never_the_summary(
        tmp_path, verb, source):
    """INV-TT5, at the default source and set. Mutants: a marker omitted; a marker written into `summary`."""
    m = _mem(tmp_path, scoped=False)
    e = _edge(m, "e-1", "tea")
    if verb == "correct":
        m.correct(U, e.id, "coffee", call_path=C.MCP_DIRECT, source_id=source)
    else:
        m.dispute(U, e.id, reason="no", call_path=C.MCP_DIRECT, source_id=source)
    ep = _episode(m, f"{verb}:")
    p = _prov_json(ep)
    assert p.get("call_path") == "mcp_direct" and p.get("source_id") == source, p
    assert "mcp_direct" not in ep.summary and (source is None or source not in ep.summary)
    if verb == "correct":
        new = next(x for x in m.store.edges(U) if x.object == "coffee")
        assert new.provenance.source_id == source and new.provenance.call_path is None


@pytest.mark.parametrize("call_path", [None, C.HOST_API])
@pytest.mark.parametrize("verb", ["correct", "dispute", "confirm"])
def test_a_host_api_write_keeps_todays_provenance_bytes(tmp_path, verb, call_path):
    """INV-TT5 / INV-TT23's byte half: with every new keyword absent (and with host_api passed explicitly) the audit
    episode's provenance is exactly the eight pre-feature keys, `source_id` serialized as null, no `call_path` key.
    Mutants: `host_api` written explicitly; an omitted key written as null."""
    m = _mem(tmp_path, scoped=False)
    e = _edge(m, "e-1", "tea")
    kw = {} if call_path is None else {"call_path": call_path}
    {"correct": lambda: m.correct(U, e.id, "coffee", **kw), "dispute": lambda: m.dispute(U, e.id, **kw),
     "confirm": lambda: m.confirm(U, e.id, **kw)}[verb]()
    p = _prov_json(_episode(m, f"{verb}:"))
    assert set(p) == LEGACY_PROV_KEYS and p["source_id"] is None and "call_path" not in p


def test_a_bound_source_changes_the_confirmation_request_identity_and_absence_keeps_todays(tmp_path):
    """The binding's source is a caller input, so it enters confirm's request digest; absent, the digest is today's
    (a host retry under a held correlation id must keep replaying)."""
    import hashlib as _h
    from veracium.schema import CONFIRMATION_RULE_VERSION
    m = _mem(tmp_path, scoped=False)
    e = _edge(m, "e-1", "tea")
    m.confirm(U, e.id, correlation_id="c-1", date="2026-11-01")
    today = _h.sha256("\x1f".join([U, e.id, "host_api", "user", CONFIRMATION_RULE_VERSION,
                                   "2026-11-01"]).encode()).hexdigest()
    assert m.store.confirmations_for(U, e.id)[0].request_digest == today
    assert m.confirm(U, e.id, correlation_id="c-1", date="2026-11-01")["replayed"] is True


# ------------------------------------------------------------------ §3b: configuration refusals (gate 5)
def test_a_principal_with_no_scope_policy_is_scope_unconfigured_and_writes_nothing(tmp_path):
    m = _mem(tmp_path, scoped=False)
    e = _edge(m, "e-1", "tea")
    before = _digest(m)
    with pytest.raises(TrustRefused) as ei:
        m.dispute(U, e.id, principal=A, source_id="src-a")
    assert ei.value.reason == "scope_unconfigured" and _digest(m) == before


def test_a_principal_with_no_source_is_ungroupable_and_writes_nothing(tmp_path):
    m = _mem(tmp_path)
    e = _edge(m, "e-1", "tea", source_id="src-a")
    before = _digest(m)
    with pytest.raises(TrustRefused) as ei:
        m.dispute(U, e.id, principal=Identity("org-x", None), source_id="src-a")
    assert ei.value.reason == "principal_ungroupable" and _digest(m) == before


# ------------------------------------------------------------------ INV-TT18: the binding's source (gate 6)
@pytest.mark.parametrize("principal, source, outcome", [
    (A, "src-a", "accepted"),                  # team-a's own source classes OWN
    (A, "src-b", "source_out_of_scope"),       # another group's source: CROSS_HIDDEN
    (A, "src-unknown", "source_out_of_scope"),  # an ungrouped source that is not the principal's own
    (A, None, "source_unbound"),               # no source would be SHARED: refused first
    (LONER, "src-z", "accepted"),              # a principal in no group: its own source classes OWN
    (LONER, "src-a", "source_out_of_scope"),
    (LONER, "src-b", "source_out_of_scope"),
])
@pytest.mark.parametrize("verb", ["correct", "dispute", "confirm"])
def test_the_binding_source_must_itself_be_own_to_the_principal(tmp_path, principal, source, outcome, verb):
    """INV-TT18's binding-source cases, as dev executed them in v0.13.1. Mutant: the source check removed (a source-
    less or divergent binding would quote a private record into the pool or another group's scope)."""
    m = _mem(tmp_path)
    e = _edge(m, "e-1", "tea", source_id=principal.source_id)     # the principal's own record
    before = _digest(m)
    call = {"correct": lambda: m.correct(U, e.id, "coffee", principal=principal, source_id=source),
            "dispute": lambda: m.dispute(U, e.id, principal=principal, source_id=source),
            "confirm": lambda: m.confirm(U, e.id, principal=principal, source_id=source)}[verb]
    if outcome == "accepted":
        call()
        assert _prov_json(_episode(m, f"{verb}:"))["source_id"] == source
    else:
        with pytest.raises(TrustRefused) as ei:
            call()
        assert ei.value.reason == outcome and _digest(m) == before


@pytest.mark.parametrize("verb", ["correct", "dispute", "confirm"])
def test_an_act_on_a_private_record_is_quoted_to_no_wider_scope(tmp_path, verb):
    """INV-TT18's leak case (TT-R1-01): after A acts on its private OWN record, an unrelated principal B and a
    principal in no group recall no quotation of it. Mutants: the episode's source dropped; the replacement edge's
    source dropped (each would land in the user-wide pool, visible to both)."""
    m = _mem(tmp_path)
    e = _edge(m, "e-1", "Zanzibar-secret", source_id="src-a")
    {"correct": lambda: m.correct(U, e.id, "Zanzibar-moved", principal=A, source_id="src-a"),
     "dispute": lambda: m.dispute(U, e.id, principal=A, source_id="src-a"),
     "confirm": lambda: m.confirm(U, e.id, principal=A, source_id="src-a")}[verb]()
    for other in (B, LONER):
        r = m.recall(U, "Zanzibar", principal=other)
        text = r.context + " ".join(x.summary for x in r.episodes) + " ".join(x.object for x in r.edges)
        assert "Zanzibar" not in text, (verb, other)
    mine = m.recall(U, "Zanzibar", principal=A)
    assert "Zanzibar" in mine.context + " ".join(x.summary for x in mine.episodes)


# ------------------------------------------------------------------ INV-TT16 at the library: the target (gate 7)
def _classed(tmp_path, cross_visible):
    m = _mem(tmp_path, cross_visible=cross_visible)
    recs = {"own": _edge(m, "e-own", "tea", source_id="src-a"),
            "shared": _edge(m, "e-shared", "milk"),                       # no source: the user-wide pool
            "other_group": _edge(m, "e-b", "juice", source_id="src-b"),
            "other_user": _edge(m, "e-x", "soda", source_id="src-a", user="someone-else")}
    return m, recs


@pytest.mark.parametrize("verb", ["correct", "dispute", "confirm", "redact"])
@pytest.mark.parametrize("cross_visible", [False, True])
def test_the_decision_table_under_a_principal(tmp_path, verb, cross_visible):
    """§3b's frozen table: OWN acted on; SHARED and CROSS_VISIBLE refused `out_of_scope`; CROSS_HIDDEN, another
    user's id and an unknown id refused `not_found_in_scope` with ONE response; every refusal writes nothing.
    Mutants: SHARED admitted; CROSS_VISIBLE admitted; a distinct response for an unknown id."""
    def call(m, eid):
        return {"correct": lambda: m.correct(U, eid, "coffee", principal=A, source_id="src-a"),
                "dispute": lambda: m.dispute(U, eid, principal=A, source_id="src-a"),
                "confirm": lambda: m.confirm(U, eid, principal=A, source_id="src-a"),
                "redact": lambda: m.redact(U, edge_id=eid, reason="subject_request", principal=A)}[verb]()
    expected = {"shared": "out_of_scope",
                "other_group": "out_of_scope" if cross_visible else "not_found_in_scope",
                "other_user": "not_found_in_scope", "unknown": "not_found_in_scope"}
    responses = {}
    for case, reason in expected.items():
        m, recs = _classed(tmp_path / case, cross_visible)
        eid = "e-nope" if case == "unknown" else recs[case].id
        before = _digest(m)
        with pytest.raises(TrustRefused) as ei:
            call(m, eid)
        assert ei.value.reason == reason and _digest(m) == before, case
        responses[case] = (ei.value.reason, ei.value.detail, str(ei.value))
        m.close()
    hidden = [responses[c] for c, r in expected.items() if r == "not_found_in_scope"]
    assert len(set(hidden)) == 1 and hidden[0][1] == NOT_FOUND_DETAIL
    m, recs = _classed(tmp_path / "own", cross_visible)
    call(m, recs["own"].id)                                   # OWN: acted on


def test_with_no_principal_no_scope_code_runs(tmp_path, monkeypatch):
    """0020 V1: with `principal=None` the gate never builds a view. Mutant: scope code run under principal=None."""
    m = _mem(tmp_path)
    e = _edge(m, "e-1", "tea", source_id="src-b")
    from veracium import scope_read
    built, refused = [], None
    real = scope_read.view_for
    monkeypatch.setattr(scope_read, "view_for", lambda *a, **k: built.append(a) or real(*a, **k))
    try:
        m.dispute(U, e.id, source_id="src-a", call_path=C.ADAPTER_DIRECT)
    except Exception as exc:                      # scope code run under principal=None: the defect, asserted below
        refused = f"{type(exc).__name__}: {exc}"
    assert built == [] and refused is None, (built, refused)


# ------------------------------------------------------------------ INV-TT19: the principal-facing receipt
SIX = {"redacted_kind", "target_id", "reason", "marker_version", "repeated", "recorded_at"}


def test_the_principal_receipt_is_six_fields_the_scope_label_and_the_filtered_list(tmp_path):
    """Mutants: the raw host receipt returned; `fields_cleared` kept; a hidden entry kept."""
    m = _mem(tmp_path)
    e = _edge(m, "e-1", "tea", source_id="src-a")
    # a derived record the principal cannot see: a CROSS_HIDDEN episode sharing the target's evidence_ref
    from veracium.schema import Episode
    m.store.add_episode(Episode(id="ep-hidden", user_id=U, date="2026-11-01", summary="tea, said elsewhere",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                      evidence_ref="ev-e-1", source_id="src-b")))
    m.store.add_episode(Episode(id="ep-mine", user_id=U, date="2026-11-01", summary="tea, said here",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                      evidence_ref="ev-e-1", source_id="src-a")))
    r = m.redact(U, edge_id=e.id, reason="subject_request", principal=A)
    assert isinstance(r, dict), type(r).__name__            # the projection, never the host receipt
    assert set(r) == SIX | {"surviving_derived", "scope"} and r["scope"] == "this principal's view"
    assert [(d["id"], d["class"]) for d in r["surviving_derived"]] == [("ep-mine", "OWN")]
    again = m.redact(U, edge_id=e.id, reason="subject_request", principal=A)
    assert again["repeated"] is True and set(again) == set(r)
    host = m.redact(U, edge_id=e.id, reason="subject_request")
    assert {d["id"] for d in host.surviving_derived} == {"ep-hidden", "ep-mine"}   # whole on the host path


def test_a_repeat_under_a_principal_passes_a_fresh_gate_an_unresolved_survivor_is_refused(tmp_path):
    """Round 2's witness `redaction_repeat` (TT-R2-01), on the real verb: a normal same-source ABSORPTION survivor is OWN
    before its redaction and UNRESOLVED after it, because the redaction clears the ledger evidence its OWN rested on.
    The first redaction under the principal succeeds; a repeat under the same principal runs the gate FRESH and is
    refused, writing nothing; the host path's repeat still returns today's receipt (`repeated=True`). Mutant: a
    repeat of an already-redacted target skipping the gate (a receipt replay)."""
    from veracium import graph
    from veracium.schema import Edge as _E
    m = _mem(tmp_path)
    t = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)

    def edge(eid, obj):
        return _E(id=eid, user_id=U, subject="user", relation="has_pet", object=obj, valid_from=t,
                  provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, source_id="src-a",
                                        evidence_ref=f"ev-{eid}", observed_at=t))
    m.store.add_edge(edge("e-short", "Miso"))
    graph.apply_supersession(m.store, edge("e-full", "cat Miso"), m.config.relations)
    assert m._find_edge(U, "e-short").invalidation_reason == "absorbed_duplicate"
    first = m.redact(U, edge_id="e-full", reason="subject_request", principal=A)
    assert first["repeated"] is False and first["target_id"] == "e-full"
    before = _digest(m)
    with pytest.raises(TrustRefused):
        m.redact(U, edge_id="e-full", reason="subject_request", principal=A)
    assert _digest(m) == before
    assert m.redact(U, edge_id="e-full", reason="subject_request").repeated is True    # the host path, unchanged


def test_two_stores_differing_only_in_hidden_records_give_identical_principal_receipts(tmp_path):
    """INV-TT19's comparison: the same visible target, different hidden related records; after normalizing
    generated times, the two principal results are identical. Mutant: a hidden count or "hidden exists" flag."""
    from veracium.schema import Episode
    out = []
    for i, hidden in enumerate((False, True)):
        m = _mem(tmp_path / str(i))
        e = _edge(m, "e-1", "tea", source_id="src-a")
        if hidden:
            m.store.add_episode(Episode(id="ep-hidden", user_id=U, date="2026-11-01", summary="tea elsewhere",
                                        provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                              evidence_ref="ev-e-1", source_id="src-b")))
        r = m.redact(U, edge_id=e.id, reason="subject_request", principal=A)
        assert isinstance(r, dict), type(r).__name__
        out.append({**r, "recorded_at": "<t>"})
    assert out[0] == out[1]


# ------------------------------------------------------------------ INV-TT23 (v23.1): the call-path export era
def _export(m, path):
    m.export_memory(U, path)
    lines = path.read_text().splitlines()
    return json.loads(lines[0])["version"], lines


def test_an_export_carrying_an_agent_path_is_15_and_one_without_keeps_its_era_and_bytes(tmp_path):
    """Mutant: the era predicate reading edges only (the episode case would export 14)."""
    plain, agent = _mem(tmp_path / "p", scoped=False), _mem(tmp_path / "a", scoped=False)
    for m in (plain, agent):
        _edge(m, "e-1", "tea")
    plain.dispute(U, "e-1")
    agent.dispute(U, "e-1", call_path=C.MCP_DIRECT)
    vp, lp = _export(plain, tmp_path / "p.jsonl")
    va, la = _export(agent, tmp_path / "a.jsonl")
    assert va == 15 and vp < 15
    # the plain export is the pre-v23.1 form: no line carries the key
    assert not any('"call_path"' in ln for ln in lp)


def test_a_confirmation_line_with_an_agent_path_stamps_15(tmp_path):
    m = _mem(tmp_path, scoped=False)
    _edge(m, "e-1", "tea")
    m.confirm(U, "e-1", call_path=C.ADAPTER_DIRECT)
    v, _ = _export(m, tmp_path / "x.jsonl")
    assert v == 15


def test_the_call_path_survives_export_import_and_a_redaction_of_the_audit_episode(tmp_path):
    """Mutants: `call_path` dropped by the import; `call_path` cleared by redaction."""
    m = _mem(tmp_path / "src", scoped=False)
    _edge(m, "e-1", "tea")
    m.dispute(U, "e-1", call_path=C.MCP_DIRECT)
    ep = _episode(m, "dispute:")
    m.redact(U, episode_id=ep.id, reason="subject_request")
    assert _episode(m, "dispute:").provenance.call_path is C.MCP_DIRECT
    p = tmp_path / "x.jsonl"
    m.export_memory(U, p)
    dst = _mem(tmp_path / "dst", scoped=False)
    refused = None
    try:
        dst.import_memory(p, restore=True)
    except ValueError as exc:                     # an export that does not declare its era is refused: the defect
        refused = str(exc)[:200]
    assert refused is None, refused
    assert _episode(dst, "dispute:").provenance.call_path is C.MCP_DIRECT


def test_an_older_reader_refuses_a_15_file(tmp_path, monkeypatch):
    """The era refusal driven by a reader whose head is 14 (V-OLD-READER-REFUSES)."""
    m = _mem(tmp_path / "src", scoped=False)
    _edge(m, "e-1", "tea")
    m.dispute(U, "e-1", call_path=C.MCP_DIRECT)
    p = tmp_path / "x.jsonl"
    m.export_memory(U, p)
    monkeypatch.setattr(portability, "FORMAT_VERSION", 14)
    dst = _mem(tmp_path / "dst", scoped=False)
    with pytest.raises(ValueError, match="newer than this Veracium understands"):
        dst.import_memory(p, restore=True)


@pytest.mark.parametrize("plant", ["episode_call_path", "confirmation_adapter_direct"])
def test_a_file_declaring_14_that_carries_an_agent_path_is_refused_whole(tmp_path, plant):
    """Mutant: a planted `call_path` stripped instead of refused (it would read as a host act)."""
    m = _mem(tmp_path / "src", scoped=False)
    _edge(m, "e-1", "tea")
    m.confirm(U, "e-1")                          # a host_api confirmation line: a 14 file
    m.dispute(U, "e-1")
    p = tmp_path / "x.jsonl"
    m.export_memory(U, p)
    lines = [json.loads(x) for x in p.read_text().splitlines()]
    assert lines[0]["version"] == 14
    for rec in lines[1:]:
        if plant == "episode_call_path" and rec.get("record") == "episode" and \
                rec["provenance"]["evidence_ref"].startswith("dispute:"):
            rec["provenance"]["call_path"] = "mcp_direct"
        if plant == "confirmation_adapter_direct" and rec.get("record") == "confirmation":
            rec["call_path"] = "adapter_direct"
    p.write_text("".join(json.dumps(x) + "\n" for x in lines))
    dst = _mem(tmp_path / "dst", scoped=False)
    before = _digest(dst)
    with pytest.raises(ValueError, match="agent call path"):
        dst.import_memory(p, restore=True)
    assert _digest(dst) == before
