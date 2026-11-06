"""specs/0042 (accepted v9.2) — the RUNTIME leg over the product's declared sites, per tranche.

The static scan says a binding exists; this executes ONE declining decision at every declared
site and asserts the id's counters MOVED BY EXACTLY ONE — Δconsulted == 1 and Δfired == 1 —
between a before and an after (a LEVEL is the proxy round 4 refused). Every declared id must
have an entry here (completeness), and every entry must name a declared id; the disabled
census (the shipped default) moves nothing.

Tranche 2 (2026-09-19): gate, schema, compile, grounding, authority, asof — 28 sites.
Tranche 3 (2026-09-19): graph, proactive, ingest, procedures, the procedural gate, the registry,
the MCP closed set, the Memory surface, diagnostics, telemetry — 40 more ids.
Tranche 4 (2026-09-19): scope, scope_linkage, scope_read, portability — 33 more ids.
Tranche 5 (2026-09-19): the store — migration, revocation, the sweep's validators, schema
version, sqlite — 46 more ids; 147 in all, every id the semantic review named.
Round 6, pre-seal (2026-09-20): THE PARAMETRISED IDS ARE FROZEN AFTER THE LAST ENTRY BLOCK and asserted
equal to the dicts. The parametrisation had been evaluated above the last three entry blocks, so the
fourteen entries below it (0041 tranches 3–5) had never run under the delta assertion while the
completeness test — which compared dict keys, not the parametrised set — stayed green; building the
per-site decision trace for the implementation-review package found it, and found that one of the
fourteen (`store.redact.target`) bracketed two decision points under one id and consulted twice per
decline — now two ids. A static guard refuses an entry block below the freeze.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

import pathlib
import re

import pytest

import veracium
import veracium.asof.recall  # noqa: F401 — lazily imported by the package; declares two sites
from veracium import authority, census, gate, grounding
from veracium import compile as compile_mod
from veracium.asof import adapter, classify, resolve
from veracium.asof.carrier import Envelope
from veracium.config import MemoryConfig
from veracium import redaction as _redaction
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, Episode, EvidenceAuthor,
                             Provenance, ReplyActor, Volatility)
from veracium.store.base import PLAN_STALE, RawEdgeState, ReplyRefused, RequestRedacted
from veracium.store.sqlite import SqliteStore

U = "u"
NOW = datetime.now(timezone.utc)

# The product's Site objects, captured at THIS module's import: the census tests clear the registry
# for their own fixtures (an autouse `_clear_registry()`), so under a shuffled order the registry
# may be empty by the time these run — the module-level sites keep counting regardless, and
# they are what this leg measures (the registry is the report's carrier, not the counters').
SITES = {sid: census._REGISTRY[sid] for sid in census.registry()}


def _edge(eid="e1", obj="a value", *, disc=Disclosure.MENTIONABLE, author=EvidenceAuthor.USER,
          rel="works_as", valid_from=None, procedural=False):
    t = valid_from or (NOW - timedelta(days=1))
    prov = Provenance(author_of_evidence=author, evidence_ref=f"ev-{eid}", disclosure=disc,
                      observed_at=NOW - timedelta(days=1))
    if procedural:
        prov = prov.model_copy(update={"record_kind": "procedural"})
    return Edge(id=eid, user_id=U, subject="user", relation=rel, object=obj, note="",
                volatility=Volatility.SLOW, valid_from=t, provenance=prov)


def _episode(eid="ep1", *, disc=Disclosure.MENTIONABLE, date=None, retired=None,
             third_party=False):
    prov = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=eid, disclosure=disc,
                      observed_at=NOW, third_party_influenced=third_party)
    return Episode(id=eid, user_id=U, date=(date or NOW.date().isoformat()), summary="s",
                   provenance=prov, retired_reason=retired)


# ---- one declining execution per site: {site_id: callable} ---------------------------------
# Each callable executes the decision ONCE at its site on an input the site declines. Sites whose
# bracket is shared (scoped_assertable's three, _resolve_edge's two) are asserted on their OWN id.

def _grounded_inputs_withholding():
    s = SqliteStore(":memory:")
    s.add_edge(_edge("uo", disc=Disclosure.USE_ONLY, author=EvidenceAuthor.THIRD_PARTY))
    compile_mod._grounded_inputs(s, U, DEFAULT_RELATIONS)
    s.close()


def _resolve_edge_with(monkeypatched, res):
    """Drive `_resolve_edge` with `_classify_live` returning `res` — the decision at the site on a
    controlled classification (the runtime leg executes the site, not the classifier)."""
    monkeypatched.setattr(resolve, "_classify_live", lambda *a, **k: (res, {} if res else None))
    s = SqliteStore(":memory:")
    resolve._resolve_edge(s, U, _edge(), {}, NOW, NOW, None, None, None, True)
    s.close()


DECLINES = {
    "schema.edge.quarantined": lambda mp: _edge(disc=Disclosure.QUARANTINED).quarantined,
    "schema.edge.use-only": lambda mp: _edge(disc=Disclosure.USE_ONLY).use_only,
    "schema.edge.valid-now": lambda mp: _edge(valid_from=NOW + timedelta(days=1)).valid_now,
    "schema.edge.assertable": lambda mp: _edge(disc=Disclosure.QUARANTINED).assertable,
    "schema.episode.quarantined": lambda mp: _episode(disc=Disclosure.QUARANTINED).quarantined,
    "schema.episode.use-only": lambda mp: _episode(disc=Disclosure.USE_ONLY).use_only,
    "schema.episode.active": lambda mp: _episode(retired="superseded").active,
    "schema.episode.assertable": lambda mp: _episode(disc=Disclosure.QUARANTINED).assertable,
    "schema.episode.valid-now": lambda mp: _episode(
        date=(NOW + timedelta(days=2)).date().isoformat()).valid_now,
    "gate.exclude-procedural": lambda mp: gate.exclude_procedural([_edge(procedural=True)]),
    "gate.scoped-assertable.invisible": lambda mp: gate.scoped_assertable(True, (False, "own")),
    "gate.scoped-assertable.third-party-shaped": lambda mp: gate.scoped_assertable(
        True, (True, "third-party-shaped")),
    "gate.scoped-assertable.entitlement": lambda mp: gate.scoped_assertable(
        True, (True, "own"), subject_entitlement=False),
    "gate.partition-parts": lambda mp: gate.partition_parts(
        [_edge(disc=Disclosure.QUARANTINED, author=EvidenceAuthor.THIRD_PARTY)], []),
    "compile.grounded-inputs": lambda mp: _grounded_inputs_withholding(),
    "grounding.ungrounded": lambda mp: grounding.ungrounded("42 units", "we ordered some", "2026-01-01"),
    "authority.permitted": lambda mp: authority.permitted(
        EvidenceAuthor.USER, None, EvidenceAuthor.THIRD_PARTY, None),
    "authority.self-assertion": lambda mp: authority.self_assertion(EvidenceAuthor.USER, None),
    "asof.adapter.derive-quarantined": lambda mp: adapter.derive_quarantined("works_as", "quarantined"),
    "asof.adapter.derive-use-only": lambda mp: adapter.derive_use_only("use_only"),
    "asof.adapter.adapt.refuse": lambda mp: adapter.adapt("not json", expect_id="a", expect_user=U),
    "asof.classify.assertable-as-of": lambda mp: classify.assertable_as_of(
        Envelope(U, "e1"),
        RawEdgeState(edge_id="e2", user_id=U, state={}, txn=0, seq=0, kind="live", recorded_at=""),
        NS(edge_id="e2", user_id=U, scope_cell=None), NOW, NOW),
    "asof.resolve.held-at": lambda mp: resolve.held_at(_edge(valid_from=NOW + timedelta(days=1)), NOW),
    "asof.resolve.future-T": lambda mp: _raises(
        resolve.FutureAsOfRefused, resolve.resolve_as_of, SqliteStore(":memory:"), U,
        NOW + timedelta(days=1)),
    "asof.resolve.edge-unclassified": lambda mp: _resolve_edge_with(mp, None),
    "asof.resolve.edge-hidden-or-invalid": lambda mp: _resolve_edge_with(
        mp, NS(status=resolve.SCOPE_HIDDEN, flags=frozenset())),
}


def _raises(exc, fn, *a, **k):
    with pytest.raises(exc):
        fn(*a, **k)


# the two as-of recall sites are inner functions of `recall_at` and execute once per candidate
# under a recall — driven through the surface, asserted as one decline per candidate
def _asof_recall_one_candidate():
    mem = veracium.Memory(llm=lambda p, **k: "", config=MemoryConfig(db_path=":memory:"))
    mem.store.add_edge(_edge("q", disc=Disclosure.QUARANTINED, author=EvidenceAuthor.THIRD_PARTY))
    mem.recall(U, "a value", as_of=NOW - timedelta(seconds=1))
    mem.close()


SURFACE_DRIVEN = {
    "asof.recall.grounded": _asof_recall_one_candidate,   # one candidate: grounded evaluated FOUR times (EXACT_SURFACE)
    "asof.recall.claim": _asof_recall_one_candidate,      # … and claim once
}


# ---- tranche 3 (2026-09-19): graph, proactive, ingest, procedures, procedural_gate, registry, mcp,
# the package module, diagnostics, telemetry — 40 ids ------------------------------------------
from veracium import graph, procedural_gate, registry as registry_mod, mcp_server, telemetry as T
from veracium import diagnostics as D
import veracium.procedures  # noqa: F401 — lazily imported by the package; declares its site
from veracium.ingest import EvidenceContext, SourceIdRequired, ingest_event
from veracium.proactive import assemble
from veracium.schema import Outcome, RESERVED_RELATIONS, Relation, UNCLASSIFIED_RELATION
from veracium.store.base import ReceiptSchemaBoundaryError, SupersessionIntegrityError
import json as _json


def _store():
    return SqliteStore(":memory:")


def _mem(**cfg):
    return veracium.Memory(llm=lambda p, **k: "", config=MemoryConfig(db_path=":memory:", **cfg))


def _llm_emitting(payload):
    text = _json.dumps(payload)
    return lambda prompt, *, system=None, role="distill", json_schema=None: text


def _receipt_boundary():
    s = _store(); e = _edge("legacy")
    s._conn.execute("INSERT INTO supersession_operations(user_id,operation_id,logical_request_digest,"
                    "status,request_digest,response,outcome_digest_version) VALUES(?,?,?,?,NULL,?,?)",
                    (U, f"sup-{e.id}", "pre-split", "applied", None, 1))
    s._conn.commit()
    with pytest.raises(ReceiptSchemaBoundaryError):
        graph.apply_supersession(s, e, DEFAULT_RELATIONS)
    s.close()


def _replay_mismatch():
    s = _store()
    graph.apply_supersession(s, _edge("same", "Miso"), DEFAULT_RELATIONS)
    with pytest.raises(SupersessionIntegrityError):
        graph.apply_supersession(s, _edge("same", "COMPLETELY different"), DEFAULT_RELATIONS)
    s.close()


def _sourced(eid, obj="v", source="mb-a"):
    e = _edge(eid, obj)
    return e.model_copy(update={"provenance": e.provenance.model_copy(update={"source_id": source})})


def _absorption(mp, case):
    s = _store()
    if case == "unresolved":                          # the incoming's own evidence UNRESOLVED (controlled)
        from veracium import scope_read
        from veracium.scope import UNRESOLVED
        mp.setattr(scope_read.MembershipResolver, "evidence_of_unwritten", lambda self, record: UNRESOLVED)
        gate = graph._absorption_scope_gate(s, _sourced("inc")); prior = _sourced("prior")
        s.add_edge(prior); gate(prior)
    elif case == "cross-scope":                        # two identities: the prior's evidence differs
        prior = _sourced("prior", source="mb-b"); s.add_edge(prior)
        gate = graph._absorption_scope_gate(s, _sourced("inc", source="mb-a")); gate(prior)
    else:                                              # same scope, the prior's closure is None
        from veracium import scope_read
        mp.setattr(scope_read.MembershipResolver, "flattening_plan", lambda self, kind, rid: None)
        prior = _sourced("prior"); s.add_edge(prior)
        gate = graph._absorption_scope_gate(s, _sourced("inc")); gate(prior)
    s.close()


def _src_revoked(mp):
    from veracium import scope_linkage
    mp.setattr(SqliteStore, "standing_revocations", lambda self, uid: {"d"})
    mp.setattr(scope_linkage, "identity_digest_of", lambda *a, **k: "d")
    s = _store(); graph.apply_supersession(s, _sourced("inc"), DEFAULT_RELATIONS); s.close()


def _inactive(e):
    return e.model_copy(update={"invalidated_at": NOW, "invalidation_reason": "superseded"})


def _collapse():
    a = _edge("a", "same value"); b = _edge("b", "same value")
    graph.collapse_for_render([a, b])


def _assemble_with(*edges):
    s = _store()
    for e in edges: s.add_edge(e)
    assemble(s, U, MemoryConfig(db_path=":memory:"), now=NOW); s.close()


def _ingest(**kw):
    s = _store()
    try:
        ingest_event(s, _llm_emitting({"triples": [], "episode": "ep"}), U, event_text="t",
                     author=kw.pop("author", EvidenceAuthor.USER), date="2026-09-19",
                     relations=DEFAULT_RELATIONS, **kw)
    finally:
        s.close()


def _procedure_source_id():
    mem = _mem(require_source_id=True)
    with pytest.raises(SourceIdRequired):
        mem.record_procedure(U, "Rotate service credentials every quarter.", author=EvidenceAuthor.THIRD_PARTY,
                             context=EvidenceContext.direct(basis="stated"))
    mem.close()


def _memory_raises(exc, fn):
    mem = _mem()
    try:
        with pytest.raises(exc):
            fn(mem)
    finally:
        mem.close()


def _local_origin_missing(mp):
    mp.delattr(SqliteStore, "local_origin")
    from veracium.scope import ScopeError
    with pytest.raises(ScopeError):
        veracium.Memory(llm=lambda p, **k: "", config=MemoryConfig(db_path=":memory:", scope_groups={}))


class TwoPhase:
    """A site whose SETUP would consult the same site (disputing an edge to make it inactive consults
    the dispute site): `setup` runs OUTSIDE the counting window, `run` inside it."""
    def __init__(self, setup, run): self.setup, self.run = setup, run


def _with_inactive_edge():
    mem = _mem(); e = _edge("d1"); mem.store.add_edge(e); mem.dispute(U, e.id); return (mem, e.id)


def _with_redacted_edge():
    mem = _mem(); e = _edge("fr1"); mem.store.add_edge(e); mem.redact(U, edge_id=e.id, reason="subject_request")
    return (mem, e.id)


def _inactive_edge_in(mem):
    e = _edge("d1"); mem.store.add_edge(e); mem.dispute(U, e.id); return e.id


def _procedural_edge_in(mem):
    return mem.record_procedure(U, "Rotate service credentials every quarter.", author=EvidenceAuthor.USER,
                                context=EvidenceContext.direct(basis="stated"))


def _other_subject_prior_in(mem):
    e = _edge("p9", "nurse").model_copy(update={"subject": "user's sister", "provenance": _edge("p9").provenance.model_copy(
        update={"author_of_evidence": EvidenceAuthor.SYSTEM, "derived_from": EvidenceAuthor.THIRD_PARTY})})
    mem.store.add_edge(e); return e.id


def _reporter_not_consented():
    r = D.Reporter(); r.config.endpoint = "https://example.invalid/collect"
    assert r.send(interactive=False) is False


def _telemetry(mp, fn, enabled=None):
    mp.setenv("XDG_CONFIG_HOME", str(__import__("tempfile").mkdtemp()))
    if enabled is not None:
        T.set_enabled(enabled)
    cfg = T.TelemetryConfig.load(); c = T.Collector(); c.record("recall", {"subgraph_edges": 1})
    return fn(cfg, c)


DECLINES.update({
    "graph.supersession.receipt-boundary": lambda mp: _receipt_boundary(),
    "graph.supersession.replay-mismatch": lambda mp: _replay_mismatch(),
    "graph.absorption.scope-unresolved": lambda mp: _absorption(mp, "unresolved"),
    "graph.absorption.cross-scope": lambda mp: _absorption(mp, "cross-scope"),
    "graph.absorption.no-flattening-plan": lambda mp: _absorption(mp, "no-plan"),
    "graph.correction.identity-mismatch": lambda mp: _raises(
        ValueError, graph.plan_correction, _store(), _edge("p"), _edge("r").model_copy(update={"subject": "other"}), op_id="op-x"),
    "graph.correction.prior-not-active": lambda mp: _raises(ValueError, graph.plan_correction, _store(), _edge("p"), _edge("r"), op_id="op-x"),
    "graph.src-revoked": lambda mp: _src_revoked(mp),
    "graph.semantic-duplicate.keep": lambda mp: graph.semantic_duplicate_of(_inactive(_edge("m")), _edge("s")),
    "graph.strictly-redundant": lambda mp: graph._strictly_redundant(
        _edge("m").model_copy(update={"note": "extra"}), _edge("s")),
    "graph.collapse-for-render": lambda mp: _collapse(),
    "ingest.source-id-required": lambda mp: _raises(SourceIdRequired, _ingest_third_party_unsourced),
    "ingest.basis-via-remember": lambda mp: _raises(ValueError, lambda: _ingest(context=EvidenceContext.direct(basis="stated"))),
    "ingest.instructions-not-a-list": lambda mp: _ingest_instructions_not_a_list(),
    "procedures.source-id-required": lambda mp: _procedure_source_id(),
    "procedural-gate.positive-form": lambda mp: procedural_gate.positive_form(""),
    "procedural-gate.actor-present": lambda mp: procedural_gate.actor_present(""),
    "registry.empty-refused": lambda mp: _raises(registry_mod.RegistryError, registry_mod.effective_registry, {}),
    "registry.reserved-shadowed": lambda mp: _raises(
        registry_mod.RegistryError, registry_mod.effective_registry,
        {UNCLASSIFIED_RELATION: Relation(name=UNCLASSIFIED_RELATION, functional=True, desc="shadowed")}),
    "registry.arity-refused": lambda mp: _raises(
        registry_mod.RegistryError, registry_mod.effective_registry, {"weighs": Relation(name="weighs", arity="keyed")}),
    "mcp.closed-set.author": lambda mp: _raises(ValueError, mcp_server._closed_set, "author", "system"),
    "mcp.closed-set.trust-field": lambda mp: _raises(ValueError, mcp_server._closed_set, "derived_from", "bogus"),
    "memory.scope.local-origin-missing": lambda mp: _local_origin_missing(mp),
    "memory.recall.as-of-on-proactive": lambda mp: _memory_raises(ValueError, lambda m: m.recall(U, None, as_of=NOW)),
    "memory.recall.policy-with-as-of": lambda mp: _memory_raises(ValueError, lambda m: m.recall(
        U, "q", policy=veracium.PolicyLane(policy_id="p", policy_version="1", tags_matched=("t",), ranks={}), as_of=NOW)),
    "memory.edge.unknown-target": lambda mp: _memory_raises(ValueError, lambda m: m.dispute(U, "nope")),
    "memory.confirm.unknown-target": lambda mp: _memory_raises(ValueError, lambda m: m.confirm(U, "nope")),
    "memory.dispute.inactive-edge": TwoPhase(lambda mp: _with_inactive_edge(), lambda st: _raises(ValueError, st[0].dispute, U, st[1])),
    # 0041 round 10: dispute/record_outcome/correct refuse an attested target (the setup redacts outside the window)
    "memory.feedback.attested-target": TwoPhase(lambda mp: _with_redacted_edge(), lambda st: _raises(ValueError, st[0].dispute, U, st[1])),
    "memory.record-outcome.actor-vocabulary": lambda mp: _memory_raises(ValueError, lambda m: m.record_outcome(
        U, "x", outcome=Outcome.CONFIRMED, evidence_ref="r", actor="bogus")),
    "memory.record-outcome.human-judgment": lambda mp: _memory_raises(ValueError, lambda m: m.record_outcome(
        U, "x", outcome=Outcome.CONFIRMED, evidence_ref="r", actor="system")),
    "memory.record-outcome.system-judgment": lambda mp: _memory_raises(ValueError, lambda m: m.record_outcome(
        U, "x", outcome=Outcome.CHALLENGED, evidence_ref="r", actor="user")),
    "memory.correct.inactive-edge": lambda mp: _memory_raises(ValueError, lambda m: m.correct(U, _inactive_edge_in(m), "new")),
    "memory.correct.procedural": lambda mp: _memory_raises(
        __import__("veracium.procedures", fromlist=["ProcedureValueError"]).ProcedureValueError,
        lambda m: m.correct(U, _procedural_edge_in(m), "new")),
    "memory.correct.refused": lambda mp: _memory_raises(graph.CorrectionRefused, lambda m: m.correct(U, _other_subject_prior_in(m), "surgeon")),
    "diagnostics.send.not-consented": lambda mp: _reporter_not_consented(),
    "telemetry.preview.invalid-consent": lambda mp: _telemetry(mp, T.preview),
    "telemetry.preview.not-enabled": lambda mp: _telemetry(mp, T.preview, enabled=False),
    "telemetry.flush.invalid-consent": lambda mp: _telemetry(mp, lambda cfg, c: T.flush_if_due(cfg, c, poster=lambda u, p: None)),
    "telemetry.flush.not-enabled": lambda mp: _telemetry(mp, lambda cfg, c: T.flush_if_due(cfg, c, poster=lambda u, p: None), enabled=False),
    "telemetry.collector.not-enabled": lambda mp: _telemetry(mp, lambda cfg, c: T.load_collector_if_enabled()),
})


def _ingest_third_party_unsourced():
    _ingest(author=EvidenceAuthor.THIRD_PARTY, require_source_id=True)


def _ingest_instructions_not_a_list():
    s = _store()
    ingest_event(s, _llm_emitting({"triples": [], "episode": "ep", "instructions": "x"}), U, event_text="t",
                 author=EvidenceAuthor.USER, date="2026-09-19", relations=DEFAULT_RELATIONS)
    s.close()


SURFACE_DRIVEN.update({
    # a variant needs an ELIGIBLE group (a survivor is chosen among class rank < 9): transient
    # members, one value, two distinct notes (neither strictly redundant) → one survivor, one variant
    "proactive.variant": lambda: _assemble_with(
        _edge("a", "same value").model_copy(update={"note": "one note", "volatility": Volatility.TRANSIENT}),
        _edge("b", "same value").model_copy(update={"note": "another note", "volatility": Volatility.TRANSIENT})),
    "proactive.eligible": lambda: _assemble_with(_edge("durable", "a plain durable fact")),
})


# the lazily imported modules declared their sites only now: refresh the snapshot the leg measures
SITES.update({sid: census._REGISTRY[sid] for sid in census.registry()})


# ---- tranche 4 (2026-09-19): scope, scope_linkage, scope_read, portability — 33 ids ----------------
from veracium import portability, scope, scope_linkage, scope_read
from veracium.scope import Identity, ScopeError, validate_policy
import veracium.portability  # noqa: F401 — lazily imported by the package; declares its sites

_LOCAL = "org-local-1234"
_A1 = Identity("org-a", "agent-1")
_B1 = Identity("org-b", "agent-9")


def _pol(local=_LOCAL):
    return validate_policy({"team-a": [Identity("org-a", "agent-1"), Identity("org-a", "agent-2")],
                            "team-b": [Identity("org-b", "agent-9")]}, False, local_origin=local)


def _ungroupable():
    return Identity("org-a", None)


def _row(ref, **payload):
    return {"site": "absorption", "identity_digest": "d", "op_key": None, "evidence_ref_digest": None,
            "contributor_ref": ref, "payload": payload}


def _export_lines(records, version=12, uid=U):
    head = {"kind": "veracium-export", "version": version, "user_id": uid, "exported_at": "2026-01-01T00:00:00+00:00"}
    return [_json.dumps(head)] + [_json.dumps(r) for r in records]


def _edge_rec(eid="e1", origin="org-x", **over):
    rec = _json.loads(_edge(eid).model_dump_json()); rec["provenance"]["origin"] = origin
    rec.update(over); return {"record": "edge", **rec}


def _episode_rec(eid="ep1", origin="org-x", **over):
    rec = _json.loads(_episode(eid).model_dump_json()); rec["provenance"]["origin"] = origin
    rec.pop("consolidation_output_index", None); rec.update(over); return {"record": "episode", **rec}


def _import(lines, **kw):
    import tempfile, os
    d = tempfile.mkdtemp(); p = os.path.join(d, "e.jsonl")
    with open(p, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    s = _store()
    try:
        return portability.import_memory(s, p, **kw)
    finally:
        s.close()


def _import_raises(lines, exc=ValueError, **kw):
    with pytest.raises(exc):
        _import(lines, **kw)


def _export_non_quiescent(mp):
    mp.setattr(SqliteStore, "quiescent_episode_snapshot", lambda self, *a, **k: portability.NON_QUIESCENT)
    s = _store()
    with pytest.raises(ValueError):
        portability.export_memory(s, U, "/dev/null")
    s.close()


def _preflight_conflict():
    s = _store(); s.add_edge(_edge("e1", "stored value"))
    import tempfile, os
    p = os.path.join(tempfile.mkdtemp(), "e.jsonl")
    with open(p, "w") as f:
        f.write("\n".join(_export_lines([_edge_rec("e1", object="a different value")])) + "\n")
    with pytest.raises(ValueError):
        portability.import_memory(s, p, restore=True)
    s.close()


_OUTCOME = {"outcome_uid": "u-1", "plan_id": "pl-1", "edge_id": "e1", "outcome": "restored",
            "pre_invalidated_at": "2025-06-01T00:00:00+00:00", "pre_reason": "superseded",
            "successor_evidence": ["none", []], "stage": "live", "origin": "local", "undone_at": None}


def _arity_candidate_refused():
    """0044 §4l (T11a): an undecided source's candidate into a store with no plan — the staged-union refusal."""
    e = _edge("p1", "weight 78", rel="measures").model_copy(update={
        "invalidated_at": NOW - timedelta(days=2), "invalidation_reason": "superseded"})
    _raises(ValueError, portability._arity_preflight, _store(), "p", U, [], "uninitialized", [e], {},
            restore=False, registry=None, import_op="op-x", inputs_digest="d", notice_targets=set())


def _act_orphan_refused():
    """0008 §6e / 0047 INV-R11 (T11b): an act whose edge is in neither the unit nor the destination — refused whole."""
    act = {"table": "confirmations", "act_uid": ("other", U, "c-1"), "act_seq": 1, "edge_id": "e-nowhere",
           "kind": "confirm", "target_uid": None, "text": None, "actor": "user", "call_path": "host_api",
           "confirmed_at": "2026-10-01T00:00:00+00:00", "written_at": None, "recorded_correlation_id": "k",
           "request_digest": "a" * 64, "origin": "local"}
    _raises(ValueError, portability._act_preflight, _store(), "p", U, [act], [], {}, restore=False, notices=[],
            now=NOW)


def _race_exhausted(mp):
    mp.setattr(portability, "_IMPORT_RETRIES", 0)
    _import_raises(_export_lines([_edge_rec("e1")]))


def _scoped_view_hides():
    s = _store(); pol = _pol(s.local_origin())
    v = scope_read.ScopeView(s, U, _A1, pol)
    e = _edge("x"); e = e.model_copy(update={"provenance": e.provenance.model_copy(update={"source_id": "agent-9", "origin": "org-b"})})
    v.scoped([e])
    s.close()


DECLINES.update({
    "scope.identity.groupable": lambda mp: _ungroupable().groupable,
    "scope.policy.non-groupable-member": lambda mp: _raises(ScopeError, validate_policy, {"g": [_ungroupable()]}, local_origin=_LOCAL),
    "scope.policy.digest-overlap": lambda mp: _raises(
        ScopeError, validate_policy, {"g1": [Identity("org-a", "agent-1")], "g2": [Identity("org-a", "agent-1")]}, local_origin=_LOCAL),
    "scope.revalidate": lambda mp: _raises(ScopeError, scope._revalidate, "not a policy", _LOCAL),
    "scope.closure.walk": lambda mp: scope.close_absorption_rows("S", {"S": [_row(None)]}),
    "scope.prune.cycle": lambda mp: _raises(
        scope.ExportLinkageError, scope.prune_absorbed_record, "B",
        {"B": [_row("C")], "C": [_row("B")]}, prune_op="op-000000000001"),
    "scope.membership.unknown-state": lambda mp: _raises(
        ScopeError, scope.membership, {"author": "user", "origin": "o", "source_id": "s", "evidence_ref": "r", "lineage": False}, [], "bogus", _LOCAL),
    "scope.membership.abandoned": lambda mp: _raises(
        ScopeError, scope.membership, {"author": "user", "origin": "o", "source_id": "s", "evidence_ref": "r", "lineage": False}, [], "abandoned", _LOCAL),
    "scope.classify.no-policy": lambda mp: _raises(ScopeError, scope.classify, scope.digest_of(_A1, _LOCAL), _A1, None, _LOCAL),
    "scope.classify.principal-ungroupable": lambda mp: _raises(ScopeError, scope.classify, scope.digest_of(_A1, _LOCAL), _ungroupable(), _pol(), _LOCAL),
    "scope.classify.evidence-not-digest": lambda mp: _raises(ScopeError, scope.classify, "not-a-digest", _A1, _pol(), _LOCAL),
    "scope.filters.not-mapping": lambda mp: _raises(ScopeError, scope.validate_filters, 5),
    "scope.filters.unknown-field": lambda mp: _raises(ScopeError, scope.validate_filters, {"bogus": "x"}),
    "scope.filters.bad-value": lambda mp: _raises(ScopeError, scope.validate_filters, {"subject": ""}),
    "scope.filters.apply": lambda mp: scope.apply_filters([{"subject": "a"}], {"subject": "b"}),
    "scope-linkage.import.winner": lambda mp: _raises(
        scope_linkage.ImportLinkageError, scope_linkage._resolve_winner, {"id": "r", "absorbed_by_id": "gone"}, {"r"}),
    "scope-linkage.import.rows": lambda mp: _raises(
        scope_linkage.ImportLinkageError, scope_linkage.reconstruct_absorption_rows,
        [{"id": "r", "invalidation_reason": "superseded", "absorbed_by_id": "w"}, {"id": "w"}], "org-dest-1", import_op="op-feedbeef0042"),
    "scope-linkage.export.ambiguous-absorber": lambda mp: _raises(
        scope.ExportLinkageError, scope.derive_absorbed_by, "A", {"B": [_row("A")], "C": [_row("A")]}),
    "scope-read.view.principal-not-identity": lambda mp: _raises(ScopeError, scope_read.ScopeView, _store(), U, "not-an-identity", _pol()),
    "scope-read.view.no-policy": lambda mp: _raises(ScopeError, scope_read.ScopeView, _store(), U, _A1, None),
    "scope-read.view.principal-ungroupable": lambda mp: _raises(ScopeError, scope_read.ScopeView, _store(), U, _ungroupable(), _pol()),
    "scope-read.scoped": lambda mp: _scoped_view_hides(),
    "scope-read.narrow-edges": lambda mp: scope_read.narrow_edges([_edge("n")], {"subject": "nobody"}),
    "portability.export.non-quiescent": lambda mp: _export_non_quiescent(mp),
    "portability.import.chain": lambda mp: _raises(ValueError, portability._validate_incoming_chain, [], "k", "p"),
    "portability.import.restore-not-bool": lambda mp: _import_raises(_export_lines([]), TypeError, restore="yes"),
    "portability.import.restore-with-user": lambda mp: _import_raises(_export_lines([]), restore=True, user_id="v"),
    "portability.import.file": lambda mp: _import_raises([]),
    "portability.import.agreement-invalid": lambda mp: _import_raises(
        _export_lines([_edge_rec("e1", agreement={"malformed": True})]), restore=True),
    "portability.import.origin-missing": lambda mp: _import_raises(_export_lines([_edge_rec("e1", origin=None)])),
    "portability.import.record": lambda mp: _import_raises(_export_lines([_episode_rec("ep1", claimed_by="op-x")])),
    "portability.import.race-exhausted": lambda mp: _race_exhausted(mp),
    "portability.import.preflight": lambda mp: _preflight_conflict(),
    # 0044 T11a: the arity era's three refusal sites
    "portability.import.arity-records": lambda mp: _raises(ValueError, portability._arity_records, "p", [],
                                                           [{"state": "unknown"}], portability._ARITY_VERSION),
    "portability.import.arity-unit": lambda mp: _raises(ValueError, portability._validate_outcome_unit, "p",
                                                        [dict(_OUTCOME)], []),
    "portability.import.arity-preflight": lambda mp: _arity_candidate_refused(),
    # 0008 §6e–§6f / 0045 §2c (T11b): the act and axis refusal sites
    "portability.import.act-records": lambda mp: _raises(ValueError, portability._act_records, "p",
                                                         [("confirmation", {})], portability._ACT_VERSION),
    "portability.import.act-preflight": lambda mp: _act_orphan_refused(),
    "portability.import.axis": lambda mp: _raises(ValueError, portability._axis_records, "p",
                                                  [{"id": "e1", "att": "proven"}], portability._ACT_VERSION, False),
})

SITES.update({sid: census._REGISTRY[sid] for sid in census.registry()})


# ---- tranche 5 (2026-09-19): the store — migration, revocation, the sweep's validators, schema
# version, sqlite — 46 ids ---------------------------------------------------------------------
import contextlib as _contextlib
import sqlite3 as _sqlite3
import tempfile as _tempfile

from veracium import contribution as _C
from veracium.graph import _build_supersession_plan, apply_supersession, plan_correction
from veracium.schema import (ConfirmationActor, ConfirmationCallPath, ConsolidationOutputDraft,
                             ConsolidationState, ContributionDraft)
from veracium.store import migration as _migration, revocation as _rv, revocation_sweep as _rvs
from veracium.store import schema_version as _sv
from veracium.store.base import (NON_QUIESCENT, CorrectionAuthorisationError, PreEpochQuery,
                                 ReceiptSchemaBoundaryError, SupersessionIntegrityError)
from veracium.store.schema_version import StoreVersionError


def _dbpath():
    return _tempfile.mktemp(suffix=".db")


def _sourced5(eid, obj="v", source="src-A", days=1):
    e = _edge(eid, obj, valid_from=NOW - timedelta(days=days))
    return e.model_copy(update={"provenance": e.provenance.model_copy(update={"source_id": source})})


def _seeded(n=3):
    s = _store()
    for i in range(1, n + 1):
        s.add_episode(_episode(f"e{i}", date=f"2026-01-0{i}"))
    return s


def _claimed(ids=("e1", "e2")):
    s = _seeded(); op = s.create_or_takeover_consolidation(U, list(ids), "w1", 60); assert op is not None
    return s, op


def _v2_conn_with_duplicate_legacy_outcome():
    p = _dbpath(); conn = _sqlite3.connect(p)
    for o in _sv.SCHEMA_V2:
        conn.execute(o.ddl)
    legacy = {"id": "leg-1", "user_id": U, "date": "2026-05-05", "summary": "legacy use", "kind": "outcome",
              "edge_id": "e1", "outcome": "concurred", "provenance": {"author_of_evidence": "system", "evidence_ref": "run-1"}}
    for eid in ("leg-1", "leg-2"):
        conn.execute("INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)", (eid, U, "2026-05-05", _json.dumps(dict(legacy, id=eid))))
    conn.execute("PRAGMA user_version = 2"); conn.commit(); return conn


class _RollbackFails:
    def __init__(self, conn): self._c = conn
    def __getattr__(self, n): return getattr(self._c, n)
    def execute(self, sql, *a):
        if sql == "ROLLBACK":
            raise _sqlite3.OperationalError("disk gone")
        return self._c.execute(sql, *a)


class _CommitFails:
    def __init__(self, conn): self._c = conn
    def __getattr__(self, n): return getattr(self._c, n)
    def commit(self):
        raise _sqlite3.OperationalError("database is locked")


def _stamped_foreign_file():
    p = _dbpath(); c = _sqlite3.connect(p); c.execute("CREATE TABLE not_ours (x)")
    c.execute(f"PRAGMA user_version = {_sv.SCHEMA_VERSION}"); c.commit(); c.close(); return p


def _stamped(version):
    p = _dbpath(); SqliteStore(p).close(); c = _sqlite3.connect(p); c.execute(f"PRAGMA user_version = {version}"); c.commit(); c.close(); return p


def _legacy_v1_file():
    p = _dbpath(); c = _sqlite3.connect(p); c.executescript(";\n".join(o.ddl for o in _sv.SCHEMA_V1) + ";\n"); c.commit(); c.close(); return p


def _open_locked():
    p = _dbpath(); holder = SqliteStore(p)
    try:
        holder._conn.execute("BEGIN IMMEDIATE")
        with pytest.raises(StoreVersionError) as ei:
            SqliteStore(p, busy_timeout_ms=100)
        assert ei.value.reason == "locked"
    finally:
        with _contextlib.suppress(_sqlite3.OperationalError):
            holder._conn.execute("ROLLBACK")
        holder.close()


def _txn_locked():
    p = _dbpath(); holder = SqliteStore(p); writer = SqliteStore(p, busy_timeout_ms=100)
    try:
        holder._conn.execute("BEGIN IMMEDIATE")
        with pytest.raises(_sqlite3.OperationalError, match="could not take the write lock"):
            writer.add_edge(_edge("x"))
    finally:
        with _contextlib.suppress(_sqlite3.OperationalError):
            holder._conn.execute("ROLLBACK")
        holder.close(); writer.close()


def _txn_commit_lost():
    s = _store(); s._conn = _CommitFails(s._conn)
    with pytest.raises(_sqlite3.OperationalError, match="could not COMMIT"):
        s.add_edge(_edge("x"))


def _journal_bad_reason():
    s = _store(); s.add_edge(_edge("j"))
    with pytest.raises(ValueError):
        with s._write_txn():
            s._journal_edge_write(U, "j", '{"changed": 1}', "{}", kind="invalidated", reason="bogus")   # a changed row reaches the reason check
    s.close()


def _upsert_changes_user():
    s = _store(); e = _edge("u1"); s.add_edge(e)
    with pytest.raises(ValueError):
        with s._write_txn():
            s._upsert_edge_row(e.model_copy(update={"user_id": "someone-else"}))
    s.close()


def _flattening_unresolved(mp):
    from veracium import scope_read
    from veracium.scope import UNRESOLVED
    mp.setattr(scope_read.MembershipResolver, "evidence_of_unwritten", lambda self, record: UNRESOLVED)
    s = _store(); inc = _sourced5("inc")
    plan = NS(incoming_edge=inc, contribution_drafts=[ContributionDraft(
        site="absorption", survivor_type="edge", survivor_id=inc.id, contributor_type="edge", contributor_id="prior")])
    with pytest.raises(SupersessionIntegrityError):
        s._write_absorption_flattening(U, plan)
    s.close()


def _consolidation_output_without_index(mp):
    s = _store()
    out = _episode("out1").model_copy(update={"lineage": ["e1"], "consolidation_output_index": None, "operation_id": "op-x"})
    mp.setattr(SqliteStore, "_episodes_for_operation", lambda self, uid, op: [(None, out)])
    with pytest.raises(SupersessionIntegrityError):
        s._write_consolidation_contributions(NS(user_id=U, operation_id="op-x", claimed_ids=["e1"]))
    s.close()


def _receipt_boundary_in_store():
    s = _store(); e = _sourced5("eb")
    plan, _ = _build_supersession_plan(s, e, DEFAULT_RELATIONS, "op-boundary")
    plan.raw_request = _C.raw_request_snapshot(e)
    s._conn.execute("INSERT INTO supersession_operations(user_id,operation_id,logical_request_digest,status,"
                    "request_digest,response,outcome_digest_version) VALUES(?,?,?,?,?,?,?)",
                    (U, "op-boundary", "stored-pre-d2", "applied", None, None, 1))
    s._conn.commit()
    with pytest.raises(ReceiptSchemaBoundaryError):
        s.apply_supersession_plan(plan)
    s.close()


def _correction_without_authorisation():
    s = _store(); prior = _sourced5("p1", "nurse"); s.add_edge(prior)
    plan = plan_correction(s, prior, _sourced5("r1", "surgeon"), op_id="op-c")[0]
    with pytest.raises(CorrectionAuthorisationError):
        s.apply_supersession_plan(plan)
    s.close()


def _absorption_drafts_mismatch():
    s = _store()
    prior = _sourced5("e-prior", "Miso", days=3); apply_supersession(s, prior, DEFAULT_RELATIONS)
    winner = _sourced5("e-winner", "cat Miso", days=0)
    plan, _ = _build_supersession_plan(s, winner, DEFAULT_RELATIONS, "op-abs")
    assert plan.contribution_drafts, "the fixture must absorb (same source, more specific value)"
    plan.contribution_drafts.append(plan.contribution_drafts[0])
    with pytest.raises(SupersessionIntegrityError):
        s.apply_supersession_plan(plan)
    s.close()


def _confirm(s, **over):
    kw = dict(actor=ConfirmationActor.USER, call_path=ConfirmationCallPath.HOST_API,
              correlation_id="k1", request_digest="d1", confirmed_at=NOW)
    kw.update(over); return s.confirm_edge(U, "c1", **kw)


def _confirm_correlation_race():
    """The concurrent-duplicate branch: the UNIQUE(user_id, correlation_id) row appears between the
    replay check and the INSERT, with a DIFFERENT request digest."""
    s = _store(); s.add_edge(_edge("c1")); real = s._conn
    class Racing:
        done = False
        def __getattr__(self, n): return getattr(real, n)
        def execute(self, sql, *a):
            if sql.lstrip().upper().startswith("INSERT INTO CONFIRMATIONS") and not Racing.done:
                Racing.done = True
                params = list(a[0]); params[params.index("d1")] = "OTHER"     # same id, other digest, first
                real.execute(sql, tuple(params))
            return real.execute(sql, *a)
    s._conn = Racing()
    with pytest.raises(ValueError, match="conflict"):
        _confirm(s)
    s.close()


def _outcome_episode_id(mem):
    e = _edge("o1"); mem.store.add_edge(e)
    mem.record_outcome(U, e.id, outcome=Outcome.CONCURRED, evidence_ref="run-1", actor="system")
    return next(ep.id for ep in mem.store.episodes(U) if ep.kind == "outcome")


def _delete_outcome_episode():
    mem = _mem(); eid = _outcome_episode_id(mem)
    with pytest.raises(ValueError):
        mem.store.delete_episode(eid)
    mem.close()


def _delete_reserved_episode():
    s, op = _claimed(("e1",))
    with pytest.raises(ValueError):
        s.delete_episode("e1")
    s.close()


def _pre_epoch(mp):
    mp.setattr(SqliteStore, "epoch_txn", lambda self, uid: 5)
    s = _store()
    with pytest.raises(PreEpochQuery):
        s.edge_state_at(U, "e", 1)
    s.close()


def _non_quiescent_snapshot():
    s, op = _claimed(); assert s.quiescent_episode_snapshot(U) is NON_QUIESCENT; s.close()


def _contended_claim():
    s = _seeded(); a = s.create_or_takeover_consolidation(U, ["e1", "e2"], "w1", 60)
    assert a is not None and s.create_or_takeover_consolidation(U, ["e2", "e3"], "w2", 60) is None; s.close()


def _delete_not_current():
    s, op = _claimed(); assert s.delete_claimed_inputs_if_current(op.operation_id, op.fence) is False; s.close()


def _abandon_live():
    s, op = _claimed(); assert s.abandon_consolidation_if_current(op.operation_id, op.fence) is False; s.close()


def _embedding(edge_exists, digest):
    s = _store()
    if edge_exists:
        s.add_edge(_edge("emb"))
    assert s.upsert_embedding(edge_id="emb", user_id=U, embedder_id="x", content_digest=digest,
                              dim=2, vec=[0.0, 0.0], built_at=NOW) is False
    s.close()


def _stored_episode():
    """0004 v3.5 §2c (i)'s setup: one stored episode, so the measured call is the same-ID write under another owner."""
    s = _store(); s.add_episode(_episode("own")); return s


def _import_of_a_reserved_id(tmp_path_factory=None):
    """0010 X21 at the import (0004 v3.5 §2c (ii)): an archive carrying an id a non-quiescent op reserves after the
    fenced delete of its inputs (R-II round 3)."""
    import tempfile
    from veracium.schema import ConsolidationOutputDraft, ConsolidationState as CS
    with tempfile.TemporaryDirectory() as d:
        src = veracium.Memory(llm=lambda p, **k: "", config=MemoryConfig(db_path=f"{d}/src.db"))
        src.store.add_episode(_episode("res-y")); src.export_memory(U, f"{d}/x.jsonl"); src.close()
        dst = veracium.Memory(llm=lambda p, **k: "", config=MemoryConfig(db_path=f"{d}/dst.db")); s = dst.store
        s.add_episode(_episode("res-y")); s.add_episode(_episode("res-z"))
        op = s.create_or_takeover_consolidation(U, ["res-y", "res-z"], "w1", 60)
        assert s.transition_consolidation_if_current(op.operation_id, op.fence, "w1", CS.GENERATING)
        assert s.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", ConsolidationOutputDraft(
            summary="y and z", date_start=NOW.date().isoformat(), date_end=NOW.date().isoformat()))
        assert s.transition_consolidation_if_current(op.operation_id, op.fence, "w1", CS.OUTPUTS_DURABLE)
        assert s.delete_claimed_inputs_if_current(op.operation_id, op.fence)
        _raises(ValueError, dst.import_memory, f"{d}/x.jsonl", user_id=U); dst.close()


def _import_plan_missing_fields():
    s = _store()
    with pytest.raises(ValueError):
        s.commit_outcome_import_plan(U, {"edges": [], "episodes": [], "contributions": [{"id": "x"}]}, {})
    s.close()


def _visible(**over):
    return _episode("v1").model_copy(update=over)


DECLINES.update({
    "store.migration.version": lambda mp: _raises(StoreVersionError, _migration._apply_forward, _sqlite3.connect(":memory:"), 99),
    "store.migration.postcondition": lambda mp: _raises(                                     # specs/0013 §4f (v33)
        _migration.MigrationPostconditionError, _migration._refuse_unless, _migration._Forward(4, 16), _migration.STEP_IDENTITY,
        ["the probe's failed postcondition"]),
    "store.migration.duplicate-outcome-chain": lambda mp: _raises(
        _migration.DuplicateOutcomeChainError, _migration._migrate_outcome_chains, _v2_conn_with_duplicate_legacy_outcome()),
    "store.revocation.unknown-state": lambda mp: _raises(
        _rv.RevocationUnknownState, _rv._rollback_or_poison, _RollbackFails(_store()._conn), RuntimeError("boom")),
    "store.revocation.ordinal-collision": lambda mp: _ordinal_collision(),
    "store.revocation.integrity": lambda mp: _raises(
        _rv.RevocationIntegrityError, _rv.revocation_operation, _store()._conn, U, "d1", "resurrect", "r",
        "2026-01-01T00:00:00Z", plan=lambda st: [], apply_effect=lambda c, e: None),
    "store.revocation.self-linkage": lambda mp: _raises(
        _rvs.RevocationLinkageError, _rvs.validate_contribution_row,
        {"user_id": U, "survivor_type": "edge", "survivor_id": "a", "site": "absorption", "identity_digest": "0" * 64,
         "evidence_ref_digest": None, "payload": {}, "op_key": None, "contributor_type": "edge", "contributor_ref": "a"}),
    "store.revocation.source-not-revocable": lambda mp: _raises(
        _rvs.RevocationError, _rvs.validate_revocation_row,
        {"user_id": U, "identity_digest": "not-a-digest", "action": "revoke", "at": "2026-01-01T00:00:00Z", "seq": 1, "reason": "r"}),
    "store.open.unaccepted-shape": lambda mp: _raises(StoreVersionError, SqliteStore, _stamped_foreign_file()),
    "store.open.runtime-unsupported": lambda mp: (mp.setattr(_sv, "runtime_status", lambda: _sv.RuntimeStatus(
        "refused", "feature probe preserves_ddl_body is False", None, ())),
                                                  _raises(StoreVersionError, SqliteStore, _dbpath())),
    "store.open.locked": TwoPhase(lambda mp: _lock_holder(), lambda st: _open_while_held(st)),
    "store.open.invalid-version": TwoPhase(lambda mp: _stamped(-1), lambda p: _raises(StoreVersionError, SqliteStore, p)),
    "store.open.newer": TwoPhase(lambda mp: _stamped(_sv.SCHEMA_VERSION + 1), lambda p: _raises(StoreVersionError, SqliteStore, p)),
    "store.open.legacy": lambda mp: _raises(StoreVersionError, SqliteStore, _legacy_v1_file()),
    "store.runtime-refused": lambda mp: _sv.runtime_refused(_sv.RuntimeStatus("refused", "feature probe x is False",
                                                                              None, ())),
    "store.journal.reason-not-dispositioned": lambda mp: _journal_bad_reason(),
    "store.read.output-not-visible": lambda mp: SqliteStore._ordinary_read_visible(
        _visible(lineage=["e1"], operation_id="op"), {"op": ConsolidationState.CLAIMED}),
    "store.read.input-claimed": lambda mp: SqliteStore._ordinary_read_visible(
        _visible(operation_id="op"), {"op": ConsolidationState.OUTPUTS_DURABLE}),
    "store.upsert.immutable": TwoPhase(lambda mp: _stored_edge(), lambda st: _upsert_other_user(*st)),
    "store.flattening": lambda mp: _flattening_unresolved(mp),
    "store.consolidation-contribution": lambda mp: _consolidation_output_without_index(mp),
    "store.contribution": lambda mp: _raises(
        SupersessionIntegrityError, _store()._write_contribution, U,
        ContributionDraft(site="consolidation", survivor_type="edge", survivor_id="a", contributor_type="edge", contributor_id="b"), None),
    "store.txn.locked": lambda mp: _txn_locked(),
    "store.txn.locked-retry": lambda mp: _txn_commit_lost(),
    "store.consolidation.abandon-live-lease": lambda mp: _abandon_live(),
    "store.add-episode": lambda mp: _raises(ValueError, _store().add_episode, _episode("bad").model_copy(update={"consolidation_output_index": 1})),
    "store.outcome.context-ref": TwoPhase(lambda mp: _outcome_chain_state(), lambda st: _raises(ValueError, st[0].store.append_outcome_if_head, *st[1])),
    "store.supersession.integrity": lambda mp: _receipt_boundary_in_store(),
    "store.correction.authorisation": lambda mp: _correction_without_authorisation(),
    "store.supersession.plan": TwoPhase(lambda mp: _absorption_plan_with_duplicate_draft(), lambda st: _raises(SupersessionIntegrityError, st[0].apply_supersession_plan, st[1])),
    "store.import-plan": lambda mp: _import_plan_missing_fields(),
    "store.add-episode.owner": TwoPhase(lambda mp: _stored_episode(), lambda s: _raises(
        ValueError, s.add_episode, _episode("own").model_copy(update={"user_id": "someone-else"}))),
    "store.import.reserved-id": lambda mp: _import_of_a_reserved_id(),
    "store.confirm.unknown-edge": lambda mp: _raises(KeyError, _confirm, _store()),
    "store.confirm.not-assertable": TwoPhase(lambda mp: _quarantined_store(), lambda s: _raises(ValueError, _confirm, s)),
    "store.confirm.request-digest": TwoPhase(lambda mp: _confirmed_once(), lambda s: _raises(ValueError, _confirm, s, request_digest="DIFFERENT")),
    "store.confirm.correlation": lambda mp: _confirm_correlation_race(),
    # specs/0045 §4d (T9, INV-G10): a not_attested edge whose source episode is redacted
    "store.confirm.source-redacted": TwoPhase(lambda mp: _source_redacted_store(), lambda s: _raises(ValueError, _confirm, s)),
    # specs/0047 (T10a): confirm under an open challenge, and the reply verb's refusals
    "store.confirm.active-challenge": TwoPhase(lambda mp: _challenged(), lambda s: _raises(ValueError, _confirm, s)),
    "store.reply.kind": TwoPhase(lambda mp: _replyable(), lambda s: _raises(ReplyRefused, _reply, s, kind="bogus")),
    "store.reply.actor": TwoPhase(lambda mp: _replyable(), lambda s: _raises(ReplyRefused, _reply, s, actor="assistant")),
    "store.reply.shape": TwoPhase(lambda mp: _replyable(), lambda s: _raises(ReplyRefused, _reply, s, text="")),
    "store.reply.marker": TwoPhase(lambda mp: _replyable(), lambda s: _raises(ReplyRefused, _reply, s,
                                                                               text=_redaction.MARKER)),
    "store.reply.unknown-edge": TwoPhase(lambda mp: _store(), lambda s: _raises(ReplyRefused, _reply, s)),
    "store.reply.redacted-edge": TwoPhase(lambda mp: _replyable(redacted=True), lambda s: _raises(ReplyRefused, _reply, s)),
    "store.reply.procedural-edge": TwoPhase(lambda mp: _replyable(procedural=True),
                                            lambda s: _raises(ReplyRefused, _reply, s)),
    "store.reply.request-digest": TwoPhase(lambda mp: _replied(), lambda s: _raises(ValueError, _reply, s, text="other")),
    "store.reply.result-missing": TwoPhase(lambda mp: _replied(lost=True), lambda s: _raises(ValueError, _reply, s)),
    "store.reply.resolve-target": TwoPhase(lambda mp: _replyable(), lambda s: _raises(
        ReplyRefused, _reply, s, kind="resolve", text=None, target="r-none")),
    "store.reply.resolve-repeat": TwoPhase(lambda mp: _resolved_once(), lambda st: _raises(
        ReplyRefused, _reply, st[0], kind="resolve", text=None, target=st[1], correlation_id="r3")),
    "store.supersession.absorb-acted": TwoPhase(lambda mp: _absorption_plan_over_an_act(),
                                                lambda st: _stale(st[0].apply_supersession_plan(st[1]))),
    # specs/0047 T10b: the read half's four decision points, each declining once
    "read.challenge.withheld": TwoPhase(lambda mp: _challenge_snapshot(), lambda st: st[0].withheld(st[1])),
    "read.challenge.twin": TwoPhase(lambda mp: _twin_of_a_challenge(), lambda st: _challenge_mod._is_twin(st[0], st[1])),
    "compile.fence.disputed": TwoPhase(lambda mp: _compile_challenged_midway(),
                                       lambda st: compile_mod.compile_wiki(st[0], st[1], U, DEFAULT_RELATIONS)),
    "graph.collapse.acted": TwoPhase(lambda mp: _redundant_pair_one_acted(),
                                     lambda st: graph.collapse_for_render(st[0], st[1])),
    # specs/0008 v7 §6c/§6f/§6g (v16): the registry's terminal and verb rules, and the act counter's refusal
    "store.registry.request-redacted": TwoPhase(lambda mp: _confirmed_then_redacted(), lambda s: _raises(RequestRedacted, _confirm, s)),
    "store.registry.verb-held": TwoPhase(lambda mp: _id_held_by_a_reply(), lambda s: _raises(ValueError, _confirm, s)),
    "store.act-counter.allocate": TwoPhase(lambda mp: _counter_row_lost(), lambda s: _raises(RuntimeError, _confirm, s)),
    "store.registry.result-missing": TwoPhase(lambda mp: _registry_result_lost(), lambda s: _raises(ValueError, _confirm, s)),
    "store.consolidation.contended": TwoPhase(lambda mp: _first_claim(), lambda s: s.create_or_takeover_consolidation(U, ["e2", "e3"], "w2", 60)),
    "store.consolidation.delete-not-current": lambda mp: _delete_not_current(),
    "store.delete-episode.outcome": lambda mp: _delete_outcome_episode(),
    "store.delete-episode.reserved": lambda mp: _delete_reserved_episode(),
    "store.journal.pre-epoch": lambda mp: _pre_epoch(mp),
    "store.edges.read-fence": lambda mp: _store().edges(U, include_quarantined=False),
    "store.export.non-quiescent": lambda mp: _non_quiescent_snapshot(),
    "store.consolidation.renew-refused": lambda mp: _store().renew_consolidation_lease("nope", "f", "w"),
    "store.consolidation.transition": lambda mp: _store().transition_consolidation_if_current("nope", "f", "w", "generating"),
    "store.embedding.delayed-writer": lambda mp: _embedding(False, "d"),
    "store.embedding.stale-content": lambda mp: _embedding(True, "not-the-digest"),
    "store.consolidation.write-not-current": lambda mp: _store().write_consolidation_output_if_current(
        "nope", "f", "w", ConsolidationOutputDraft(summary="m", date_start="2026-01-01", date_end="2026-01-02")),
})


def _ordinal_collision():
    s = _store()
    _rv.revocation_operation(s._conn, U, "d1", "revoke", "r", "2026-08-21T00:00:00Z", plan=lambda st: [], apply_effect=lambda c, e: None)
    def plan_preinsert(st):
        s._conn.execute("INSERT INTO source_revocations(user_id, seq, identity_digest, action, at, reason) VALUES(?,?,?,?,?,?)",
                        (U, 1, "other", "revoke", "2026-01-01T00:00:00Z", "r"))
        return []
    with pytest.raises(_rv.OrdinalCollision):
        _rv.revocation_operation(s._conn, U, "d2", "revoke", "r", "2026-08-21T00:00:00Z", plan=plan_preinsert, apply_effect=lambda c, e: None)
    s.close()


def _quarantined_store():
    s = _store(); s.add_edge(_edge("c1", disc=Disclosure.QUARANTINED, author=EvidenceAuthor.THIRD_PARTY)); return s


def _source_redacted_store():
    s = _store()
    s.add_episode(_episode("ep-src"))
    s.add_edge(Edge.model_validate({**_edge("c1").model_dump(), "att": "not_attested", "attv": "ATTEST-3@b1329a81",
                                    "src": "ep-src"}))
    s.redact(U, episode_id="ep-src", reason="subject_request")
    return s


def _reply(s, **over):
    kw = dict(kind="challenge", text="no", target=None, actor=ReplyActor.USER, correlation_id="r1")
    kw.update(over); return s.add_reply(U, "c1", **kw)


def _replyable(*, redacted=False, procedural=False):
    s = _store(); s.add_edge(_edge("c1", procedural=procedural))
    if redacted:
        s.redact(U, edge_id="c1", reason="subject_request")
    return s


def _challenged():
    s = _replyable(); _reply(s); return s


def _replied(*, lost=False):
    s = _replyable(); _reply(s)
    if lost:
        s._conn.execute("DELETE FROM replies"); s._conn.commit()
    return s


def _resolved_once():
    s = _replyable(); c = _reply(s)
    _reply(s, kind="resolve", text=None, target=c.id, correlation_id="r2")
    return (s, c.id)


from veracium import challenge as _challenge_mod


def _challenge_snapshot():
    """0047 §4d: a challenged record and the store's one snapshot; the run asks the snapshot about that record."""
    s = _challenged()
    return (s.challenge_snapshot(U), s.edges(U, active_only=False, include_quarantined=True)[0])


def _twin_of_a_challenge():
    """F7: a same-value restatement of a challenged record, matched against the snapshot's record of it."""
    s = _challenged()
    return (_edge("c2", "a value"), s.challenge_snapshot(U).challenged["c1"])


def _compile_challenged_midway():
    """INV-R18's fence: the compiler's call writes a challenge on a fact the compile drew on, so the publish fails and
    the fence withholds the body (it recompiles once; the second publish succeeds, so the fence is consulted once)."""
    s = _store(); s.add_edge(_edge("w1", "green tea", rel="likes"))
    calls = []

    def llm(prompt, system=None, role=None):
        calls.append(prompt)
        if len(calls) == 1:
            s.add_reply(U, "w1", kind="challenge", text="no", target=None, actor=ReplyActor.USER, correlation_id="f1")
        return "WIKI"
    return (s, llm)


def _redundant_pair_one_acted():
    """§4e (the narrower reading): two strictly-redundant restatements; the non-survivor carries an act, so collapse
    keeps it."""
    a, b = _edge("c-a", "chef"), _edge("c-b", "chef")
    return ([a, b], _challenge_mod.ChallengeSnapshot(acted=frozenset({"c-b"})))


def _absorption_plan_over_an_act():
    """A plan that absorbs a prior, built BEFORE the prior took an act (a confirmation): the store's verifier finds the
    act in the plan's own transaction and answers PlanStale (0047 §4e, research's T10a Q13)."""
    s = _store()
    prior = _sourced5("e-prior", "Miso", days=3); apply_supersession(s, prior, DEFAULT_RELATIONS)
    winner = _sourced5("e-winner", "cat Miso", days=0)
    plan, _ = _build_supersession_plan(s, winner, DEFAULT_RELATIONS, "op-abs-act")
    assert plan.contribution_drafts, "the fixture must absorb (same source, more specific value)"
    s.confirm_edge(U, "e-prior", actor=ConfirmationActor.USER, call_path=ConfirmationCallPath.HOST_API,
                   correlation_id="k-abs", request_digest="d-abs", confirmed_at=NOW)
    return (s, plan)


def _stale(result):
    assert result is PLAN_STALE, result


def _confirmed_once():
    s = _store(); s.add_edge(_edge("c1")); _confirm(s); return s


def _confirmed_then_redacted():
    s = _confirmed_once(); s.redact(U, edge_id="c1", reason="subject_request"); return s


def _id_held_by_a_reply():
    s = _store(); s.add_edge(_edge("c1"))
    s._conn.execute("INSERT INTO request_registry VALUES (?,?,?,?,?,?,?)", (U, "k1", "reply", "c1", "d1", "r-1", "x"))
    s._conn.commit(); return s


def _registry_result_lost():
    s = _confirmed_once(); s._conn.execute("DELETE FROM confirmations"); s._conn.commit(); return s


def _counter_row_lost():
    s = _store(); s.add_edge(_edge("c1")); s._conn.execute("DELETE FROM act_counter"); s._conn.commit(); return s


def _outcome_chain_state():
    """A head whose context_ref is X; the run then appends a draft with context_ref Y."""
    from veracium.schema import OutcomeJudgmentDraft
    mem = _mem(); e = _edge("o2"); mem.store.add_edge(e)
    ts = "2026-01-01T00:00:00+00:00"
    first = OutcomeJudgmentDraft(outcome=Outcome.CONCURRED, author=EvidenceAuthor.SYSTEM, context_ref="ctx-a",
                                 summary="s", event_timestamp=ts)
    mem.store.append_outcome_if_head(U, e.id, "run-1", None, first)
    head = mem.store._chain_head(U, e.id, "run-1")
    second = OutcomeJudgmentDraft(outcome=Outcome.CONCURRED, author=EvidenceAuthor.SYSTEM, context_ref="ctx-b",
                                  summary="s", event_timestamp=ts)
    return (mem, (U, e.id, "run-1", head.id, second))


SITES.update({sid: census._REGISTRY[sid] for sid in census.registry()})


def _first_claim():
    s = _seeded(); assert s.create_or_takeover_consolidation(U, ["e1", "e2"], "w1", 60) is not None; return s


def _lock_holder():
    p = _dbpath(); holder = SqliteStore(p); holder._conn.execute("BEGIN IMMEDIATE"); return (p, holder)


def _open_while_held(st):
    p, holder = st
    try:
        with pytest.raises(StoreVersionError) as ei:
            SqliteStore(p, busy_timeout_ms=100)
        assert ei.value.reason == "locked"
    finally:
        with _contextlib.suppress(_sqlite3.OperationalError):
            holder._conn.execute("ROLLBACK")
        holder.close()


def _absorption_plan_with_duplicate_draft():
    s = _store()
    prior = _sourced5("e-prior", "Miso", days=3); apply_supersession(s, prior, DEFAULT_RELATIONS)
    winner = _sourced5("e-winner", "cat Miso", days=0)
    plan, _ = _build_supersession_plan(s, winner, DEFAULT_RELATIONS, "op-abs")
    assert plan.contribution_drafts, "the fixture must absorb (same source, more specific value)"
    plan.contribution_drafts.append(plan.contribution_drafts[0])
    return (s, plan)


def _stored_edge():
    s = _store(); e = _edge("u1"); s.add_edge(e); return (s, e)


def _upsert_other_user(s, e):
    with pytest.raises(ValueError):
        with s._write_txn():
            s._upsert_edge_row(e.model_copy(update={"user_id": "someone-else"}))
    s.close()


SITES.update({sid: census._REGISTRY[sid] for sid in census.registry()})


@pytest.fixture
def enabled():
    census.enable(True)
    try:
        yield
    finally:
        census.enable(False)


def _delta(site_id, run):
    before = SITES[site_id].counters()
    run()
    after = SITES[site_id].counters()
    return (after["consulted"] - before["consulted"], after["fired"] - before["fired"],
            after["errors"] - before["errors"])


def test_the_disabled_census_moves_nothing(monkeypatch):
    assert not census.enabled()
    for site_id, entry in DECLINES.items():
        with monkeypatch.context() as mp:          # one entry's patches never reach the next
            if isinstance(entry, TwoPhase):
                state = entry.setup(mp); run = lambda st=state, e=entry: e.run(st)
            else:
                run = lambda e=entry, m=mp: e(m)
            assert _delta(site_id, run) == (0, 0, 0), site_id


def test_the_trace_names_the_branch_not_the_content(enabled, monkeypatch):
    census.trace(True)
    try:
        census.trace_reset()
        DECLINES["asof.adapter.adapt.refuse"](monkeypatch)
        DECLINES["gate.scoped-assertable.entitlement"](monkeypatch)
        rows = census.trace_snapshot()
    finally:
        census.trace(False)
    labels = {(r[1], r[2]) for r in rows}
    assert ("asof.adapter.adapt.refuse", "unparseable") in labels
    assert ("gate.scoped-assertable.entitlement", "entitlement") in labels
    assert all(len(r) == 3 for r in rows)


# ---- the bypass at the four hot Edge predicates (the owner, 2026-09-19): both paths, and the raise --
# The decision is computed ONCE (`q = <expr>`) and the census machinery runs only when enabled, so
# §4A-2's "consulted before the decision branches" is honoured in purpose (counted at the site) and
# not in letter: a predicate that RAISES is invisible to the census at these four sites. Research's
# sharpest case for the fourth arm: the bypassed path and the enabled path must raise the SAME
# exception, and `Site.__exit__` must never swallow it.

def test_a_raising_predicate_raises_identically_on_both_paths_and_is_consulted_before_it_is_evaluated(monkeypatch):
    """Round 6, R6-2b: the four hot predicates evaluated their value BEFORE consulting, so a predicate that
    raised left consulted at zero with the census on — 'never reached' for a site that was reached. Now the
    consult happens first (through the value helper called from both branches); the raise is identical on the
    bypassed and the enabled path and is not a measurement failure: (1, 0, 0)."""
    from veracium import schema as schema_mod

    def boom(_dt):
        raise RuntimeError("the predicate itself raised")
    monkeypatch.setattr(schema_mod, "as_utc", boom)
    e = _edge()
    census.enable(False)
    with pytest.raises(RuntimeError, match="the predicate itself raised"):
        e.valid_now                                             # the bypassed (shipped) path
    census.enable(True)
    try:
        dc, df, de = _delta("schema.edge.valid-now", lambda: pytest.raises(RuntimeError, e.__class__.valid_now.fget, e))
    finally:
        census.enable(False)
    assert (dc, df, de) == (1, 0, 0), "reached, not fired, not a measurement failure"


def test_the_enabled_and_bypassed_paths_agree_on_every_verdict(monkeypatch):
    """The fourth arm in miniature: for each of the four hot predicates, the value the property
    returns is identical with the census off and on, on a declining and a passing edge."""
    cases = [(_edge(disc=Disclosure.QUARANTINED), _edge()), (_edge(disc=Disclosure.USE_ONLY), _edge()),
             (_edge(valid_from=NOW + timedelta(days=1)), _edge()), (_edge(disc=Disclosure.QUARANTINED), _edge())]
    props = ["quarantined", "use_only", "valid_now", "assertable"]
    for prop, (declining, passing) in zip(props, cases):
        for e in (declining, passing):
            census.enable(False); off = getattr(e, prop)
            census.enable(True)
            try:
                on = getattr(e, prop)
            finally:
                census.enable(False)
            assert off == on, (prop, e.id, off, on)


# ---- specs/0041 tranche 1 (2026-09-19): INV-11's mirror, the relation-only quarantine, the kind closure — 5 ids
from veracium.redaction import MARKER as _MARKER
from veracium.schema import QUARANTINE_RELATION as _QR


def _import_prose_kind(mp):
    """A plan whose episode carries a prose kind reaches the import commit's own refusal."""
    from veracium.portability import export_memory, import_memory
    import tempfile, pathlib, json
    src = _mem(); ep = _episode("ek-src").model_copy(update={"kind": "interaction"}); src.store.add_episode(ep)
    d = pathlib.Path(tempfile.mkdtemp()); out = d / "x.jsonl"; export_memory(src.store, U, out)
    lines = out.read_text().splitlines()
    rewritten = []
    for ln in lines:
        rec = json.loads(ln)
        if rec.get("record") == "episode":          # format v2: the per-line marker is "record"; `kind` is the episode's own
            rec["kind"] = "told me in confidence"
        rewritten.append(json.dumps(rec))
    out.write_text("\n".join(rewritten) + "\n")
    return _raises(ValueError, import_memory, _mem().store, out)


DECLINES.update({
    "store.upsert.marker-introduced": lambda mp: _raises(ValueError, _mem().store.add_edge, _edge("m1", obj=_MARKER)),
    "store.upsert.relation-only-quarantine": lambda mp: _raises(ValueError, _mem().store.add_edge, _edge("q1", rel=_QR)),
    "store.episode.marker-introduced": lambda mp: _raises(ValueError, _mem().store.add_episode, _episode("em1").model_copy(update={"summary": _MARKER})),
    "store.episode.kind-not-recognised": lambda mp: _raises(ValueError, _mem().store.add_episode, _episode("ek1").model_copy(update={"kind": "told me in confidence"})),
    "store.import.episode-kind-not-recognised": _import_prose_kind,
})


# specs/0041 tranche 3 (2026-09-19): the operation's refusals and INV-11 keyed on the attestation record. The two
# attested-redaction sites are TwoPhase: their SETUP is a redaction, which consults the redact sites outside the window.
def _redacted_edge():
    s = _store(); s.add_edge(_edge("ra1", obj="a secret")); s.redact(U, edge_id="ra1", reason="subject_request"); return (s,)


def _upsert_attested(s):
    with pytest.raises(ValueError):
        s.add_edge(_edge("ra1", obj="repopulated"))
    s.close()


def _redacted_episode():
    s = _store(); s.add_episode(_episode("rae1")); s.redact(U, episode_id="rae1", reason="subject_request"); return (s,)


def _add_attested_episode(s):
    with pytest.raises(ValueError):
        s.add_episode(_episode("rae1"))
    s.close()


def _redacted_cold_input():
    s = _store(); s.add_episode(_episode("cir1")); s.add_episode(_episode("cir2"))
    s.redact(U, episode_id="cir2", reason="subject_request"); return (s,)


def _claim_redacted_input(s):
    with pytest.raises(ValueError):
        s.create_or_takeover_consolidation(U, ["cir1", "cir2"], "w", 60)
    s.close()


def _redact_bad_reason():
    s = _store(); s.add_edge(_edge("rr1"))
    with pytest.raises(ValueError):
        s.redact(U, edge_id="rr1", reason="the user's HIV status")
    s.close()


def _redact_claimed(mp):
    s = _store(); s.add_episode(_episode("rc1"))
    mp.setattr(type(s), "_reserved_ids", lambda self, user_id: {"rc1"})
    with pytest.raises(ValueError):
        s.redact(U, episode_id="rc1", reason="subject_request")
    s.close()


def _redact_disposition(mp):
    from veracium import redaction as _rd
    s = _store(); s.add_edge(_edge("rd1"))
    real = _rd.treat_edge
    def flipping(dump, **kw):
        d, treated = real(dump, **kw); d["invalidated_at"] = "2026-09-19T00:00:00+00:00"; return d, treated + ["invalidated_at"]
    mp.setattr(_rd, "treat_edge", flipping)
    with pytest.raises(ValueError):
        s.redact(U, edge_id="rd1", reason="subject_request")
    s.close()


def _redact_nothing(mp):
    """0041 round 11 (the owner's ruling): a record with no content and no marker has nothing to redact — refused."""
    s = _store(); s.add_episode(Episode(id="rn", user_id=U, date="2026-10-01", summary="", provenance=_edge("x").provenance))
    with pytest.raises(ValueError, match="nothing to redact"):
        s.redact(U, episode_id="rn", reason="subject_request")
    s.close()


def _journal_bad_redaction_reason():
    s = _store(); s.add_edge(_edge("jr"))
    with pytest.raises(ValueError):
        with s._write_txn():
            s._journal_edge_write(U, "jr", '{"changed": 1}', "{}", kind="redacted", reason="prose")
    s.close()


def _journal_bad_reinstatement_reason():
    """specs/0029 v12 §4b-i: a `reinstated` write whose reason is outside REINSTATEMENT_REASONS (NULL included)."""
    s = _store(); s.add_edge(_edge("jn"))
    with pytest.raises(ValueError):
        with s._write_txn():
            s._journal_edge_write(U, "jn", '{"changed": 1}', "{}", kind="reinstated", reason=None)
    s.close()


DECLINES.update({
    "store.journal.reinstatement-reason": lambda mp: _journal_bad_reinstatement_reason(),            # specs/0029 v12
    "store.redact.target": lambda mp: _raises(ValueError, _store().redact, U, edge_id="no-such-edge", reason="subject_request"),
    "store.redact.both-or-neither": lambda mp: _raises(ValueError, _store().redact, U, edge_id="e", episode_id="ep", reason="subject_request"),
    "store.redact.reason-not-registered": lambda mp: _redact_bad_reason(),
    "store.redact.input-claimed": _redact_claimed,
    "store.redact.disposition-changed": _redact_disposition,
    "store.redact.nothing-to-redact": _redact_nothing,
    "store.upsert.attested-redaction": TwoPhase(lambda mp: _redacted_edge(), lambda st: _upsert_attested(*st)),
    "store.episode.attested-redaction": TwoPhase(lambda mp: _redacted_episode(), lambda st: _add_attested_episode(*st)),
    "store.consolidation.input-redacted": TwoPhase(lambda mp: _redacted_cold_input(), lambda st: _claim_redacted_input(*st)),
    "store.journal.redaction-reason": lambda mp: _journal_bad_redaction_reason(),
})


# specs/0041 §4g (tranche 4b): INV-11 at the IMPORT boundary — a record this store redacted arrives in a plan with
# no notice covering it. TwoPhase: the setup redacts (consulting the redact sites outside the window).
def _redacted_then_plan():
    s = _store(); e = _edge("ri1", obj="a secret"); s.add_edge(e); s.redact(U, edge_id="ri1", reason="subject_request")
    return (s, e)


def _import_plan_repopulates(s, e):
    with pytest.raises(ValueError):
        s.commit_outcome_import_plan(U, {"edges": [e], "episodes": [], "contributions": [], "redactions": []},
                                     {"edge_ids": {e.id: True}, "episode_records": {}, "chain_heads": {}, "contribution_state": {}})
    s.close()


_NOTICE = {"origin": "o", "source_user": U, "source_event_ref": "u:1", "target_kind": "edge", "target_id": "absent",
           "fields": ["object"], "marker_version": 1, "reason": "subject_request"}
_EMPTY_EXPECT = {"edge_ids": {}, "episode_records": {}, "chain_heads": {}, "contribution_state": {}}


def _standing_notice_held():
    # 0041 round 10 (R9-04): a notice committed once (its target absent here, so it stands) under one source identity
    s = _store()
    # a STANDING notice is a trusted-restore state since the 2026-10-13 notice-binding hotfix: the default scope binds
    # a notice only to a record the commit inserts, so the fixture names the restore scope
    s.commit_outcome_import_plan(U, {"edges": [], "episodes": [], "contributions": [], "redactions": [dict(_NOTICE)],
                                     "notice_scope": "any"}, dict(_EMPTY_EXPECT))
    return (s,)


def _contradictory_notice(s):
    with pytest.raises(ValueError):
        s.commit_outcome_import_plan(U, {"edges": [], "episodes": [], "contributions": [],
                                         "redactions": [dict(_NOTICE, fields=["object", "subject"])]}, dict(_EMPTY_EXPECT))
    s.close()


def _notice_row(state, reason=None, target="absent"):
    """0041 §11.6.6 (T4): a notice row in the given state, written raw (the setup of a probe, outside its window)."""
    s = _store()
    if target != "absent":
        s.add_edge(_edge(target))
    s._conn.execute("INSERT INTO redactions(id, user_id, target_kind, target_id, fields, marker_version, reason, "
                    "store_version_before, store_version_after, event_ref, recorded_at, source_body, source_origin, "
                    "source_user, source_event_ref, state, pending_reason) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("n-1", U, "edge", target, '["object"]', 1, "imported_notice", 1, 1, None,
                     "2026-10-14T00:00:00+00:00", "{}", "o", U, "u:1", state, reason))
    s._conn.commit()
    return s


def _unredacted_arrival_on_restore_scope(s):
    # the 2026-10-13 hotfix: the standing notice's record ARRIVES (restore scope, so no origin check) carrying its
    # content — a record that does not show the redaction under a notice for it refuses the import whole
    e = _edge("absent")
    with pytest.raises(ValueError, match="arrives UNREDACTED under a standing redaction notice"):
        s.commit_outcome_import_plan(U, {"edges": [e], "episodes": [], "contributions": [], "redactions": [],
                                         "notice_scope": "any"}, dict(_EMPTY_EXPECT, edge_ids={"absent": False}))
    s.close()


DECLINES.update({
    "store.import.attested-redaction": TwoPhase(lambda mp: _redacted_then_plan(), lambda st: _import_plan_repopulates(*st)),
    "store.import.notice-body-conflict": TwoPhase(lambda mp: _standing_notice_held(), lambda st: _contradictory_notice(*st)),
    # 0041 §11.6.6 (T4): the notice state's one writer, and confirm_notice's three refusals
    "store.notice.state-domain": TwoPhase(lambda mp: _store(), lambda s: _raises(
        ValueError, s._set_notice_state, U, {"_rid": "n-x"}, "half", None, prior=None, now="2026-10-14T00:00:00+00:00")),
    "store.confirm-notice.unknown": TwoPhase(lambda mp: _store(), lambda s: _raises(ValueError, s.confirm_notice, U, "n-none")),
    "store.confirm-notice.standing": TwoPhase(lambda mp: _notice_row("standing"),
                                              lambda s: _raises(ValueError, s.confirm_notice, U, "n-1")),
    "store.confirm-notice.target-absent": TwoPhase(lambda mp: _notice_row("pending", "held-target"),
                                                   lambda s: _raises(ValueError, s.confirm_notice, U, "n-1")),
    "store.import.notice-record-unredacted": TwoPhase(lambda mp: _standing_notice_held(),
                                                      lambda st: _unredacted_arrival_on_restore_scope(*st)),
})


# 0041 round 10 (R9-02): the D1 reason closures at the writers and at import
_PROSE_REASON = "she asked me to drop everything"


def _prose_invalidation():
    import datetime as _dt
    e = _edge("pr1").model_copy(update={"invalidated_at": _dt.datetime(2026, 9, 1, tzinfo=_dt.timezone.utc),
                                        "invalidation_reason": _PROSE_REASON})
    s = _store()
    with pytest.raises(ValueError):
        s.add_edge(e)
    s.close()


def _prose_retirement():
    import datetime as _dt
    ep = _episode("pr2").model_copy(update={"retired_at": _dt.datetime(2026, 9, 1, tzinfo=_dt.timezone.utc),
                                            "retired_reason": _PROSE_REASON})
    s = _store()
    with pytest.raises(ValueError):
        s.add_episode(ep)
    s.close()


def _import_prose_reason():
    import datetime as _dt
    e = _edge("pr3").model_copy(update={"invalidated_at": _dt.datetime(2026, 9, 1, tzinfo=_dt.timezone.utc),
                                        "invalidation_reason": _PROSE_REASON})
    s = _store()
    with pytest.raises(ValueError):
        s.commit_outcome_import_plan(U, {"edges": [e], "episodes": [], "contributions": [], "redactions": []},
                                     {"edge_ids": {e.id: False}, "episode_records": {}, "chain_heads": {},
                                      "contribution_state": {}})
    s.close()


def _prose_revoke():
    from veracium.store.revocation import revoke_source as _rs
    s = _store()
    with pytest.raises(ValueError):
        _rs(s, U, "a" * 64, "revoke", _PROSE_REASON, "2026-09-01T00:00:00Z")
    s.close()


DECLINES.update({
    "store.upsert.invalidation-reason-not-registered": lambda mp: _prose_invalidation(),
    "store.episode.retired-reason-not-registered": lambda mp: _prose_retirement(),
    "store.import.reason-not-registered": lambda mp: _import_prose_reason(),
    "store.revocation.revoke-reason-not-registered": lambda mp: _prose_revoke(),
    "store.redacted-reason.not-a-redaction": lambda mp: _redacted_reason_by_an_ordinary_write(),
})


def _redacted_reason_by_an_ordinary_write():
    import datetime as _dt
    e = _edge("rr1").model_copy(update={"invalidated_at": _dt.datetime(2026, 9, 1, tzinfo=_dt.timezone.utc),
                                        "invalidation_reason": "redacted"})
    s = _store()
    with pytest.raises(ValueError):
        s.add_edge(e)
    s.close()


# specs/0041 §4e (tranche 5): the embedding upsert's read-and-publish lock — a second connection holds the write
# lock; the upsert cannot take BEGIN IMMEDIATE within its busy timeout and refuses loudly (0007 §4c form)
def _embedding_lock_refused():
    import sqlite3 as _sq, tempfile as _tf, os as _os
    from veracium.store.sqlite import SqliteStore as _SS
    d = _tf.mkdtemp(); path = _os.path.join(d, "lock.db")
    s = _SS(path); e = _edge("el1"); s.add_edge(e)
    s._conn.execute("PRAGMA busy_timeout=50")
    other = _sq.connect(path); other.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(_sq.OperationalError):
            s.upsert_embedding(edge_id="el1", user_id=U, embedder_id="emb@1", content_digest="d", dim=2, vec=b"\x00\x00",
                               built_at="2026-09-20T00:00:00Z")
    finally:
        other.rollback(); other.close(); s.close()


DECLINES.update({
    "store.embedding.txn-locked": lambda mp: _embedding_lock_refused(),
})
SITES.update({sid: census._REGISTRY[sid] for sid in census.registry()})


# specs/0018 §4i / 0044 §4f (T6-1): run_data_migration's five sites. Each SETUP (a file-backed v16 store, a plan
# written, an inventoried retirement) runs outside the window; each RUN reaches its site's condition exactly once.
def _dm_store(*, revoked=False, marked=False, mismatched=False):
    import tempfile as _tf, os as _os, json as _j
    from veracium.store import data_migration as _DM, revocation as _rv
    from veracium.store.release_migration import MigrationAttestation as _Att
    from veracium.store.revocation_sweep import digest_of as _digest_of
    path = _os.path.join(_tf.mkdtemp(), "dm.db")
    s = SqliteStore(path)
    old = _edge("dm-p", "weight 78", rel="measures").model_copy(update={
        "invalidated_at": NOW - timedelta(days=1), "invalidation_reason": "superseded",
        "provenance": _edge("dm-p").provenance.model_copy(update={"source_id": "feed-1"})})
    s.add_edge(old)                                           # an insert: no lifetime transition
    if marked:
        s._conn.execute("UPDATE edges SET json=? WHERE id='dm-p'",
                        (_j.dumps({**_j.loads(old.model_dump_json()), "object": _MARKER}),))
    d = _j.loads(s._conn.execute("SELECT json FROM edges WHERE id='dm-p'").fetchone()[0])
    # T12 (research's T6 S2 F5): `mismatched` plants the inventory row under ANOTHER user than its edge's
    s._conn.execute("INSERT INTO arity_inventory VALUES('dm-p', ?, ?, 'superseded')",
                    ("dm-other" if mismatched else U, d["invalidated_at"]))
    s._conn.commit()
    if revoked:
        _rv.revoke_source(s, U, _digest_of(None, "feed-1", s.local_origin()), "revoke", "policy", "2026-10-16T00:00:00Z")
    s.close()
    att = _Att(quiesced=True, backup_ref="bk-sites")
    run = lambda **k: _DM.run_data_migration(path, host_attestation=att, **{"registry": dict(DEFAULT_RELATIONS), **k})
    assert run(op_id="dm-plan", plan_only=True).outcome == "planned"
    run.path = path                                           # T7-2's undo sites open the same store
    return run


def _dm_assert(run, outcome, **k):
    r = run(**k)
    assert r.outcome == outcome, (r.outcome, r.diagnostic)


def _dm_registry_changed(run):
    from veracium.schema import Relation as _Rel
    reg = dict(DEFAULT_RELATIONS)
    reg["prefers"] = _Rel(name="prefers", functional=True, desc=reg["prefers"].desc, arity="single")
    _dm_assert(run, "registry-changed", op_id="dm-other", registry=reg)


def _dm_read_refused():
    import tempfile as _tf, os as _os
    from veracium.store import data_migration as _DM
    _raises(ValueError, _DM.data_migration_receipt, _os.path.join(_tf.mkdtemp(), "absent.db"), "plan", U)


DECLINES.update({
    "store.data-migration.op-id-conflict": TwoPhase(lambda mp: _dm_store(),
                                                    lambda run: _dm_assert(run, "op-id-conflict", op_id="dm-plan")),
    "store.data-migration.registry-changed": TwoPhase(lambda mp: _dm_store(), _dm_registry_changed),
    "store.data-migration.withheld-revoked": TwoPhase(lambda mp: _dm_store(revoked=True),
                                                      lambda run: _dm_assert(run, "migrated", op_id="dm-run")),
    "store.data-migration.redacted-not-considered": TwoPhase(lambda mp: _dm_store(marked=True),
                                                             lambda run: _dm_assert(run, "migrated", op_id="dm-run")),
    "store.data-migration.read-refused": lambda mp: _dm_read_refused(),
    # T12 (research's T6 S2 F5): an inventory row naming another user's edge fails that user (0018 §4i D1's carrier)
    "store.data-migration.inventory-integrity": TwoPhase(lambda mp: _dm_store(mismatched=True),
                                                         lambda run: _dm_assert(run, "failed", op_id="dm-run")),
})
SITES.update({sid: census._REGISTRY[sid] for sid in census.registry()})


# specs/0044 §4i (T7-2): undo_restoration's nine sites. SETUP restores `dm-p` through the real operation and plants
# the state each site needs (outside the window); RUN makes the one undo call that reaches the site's condition.
def _undo_store(mp, plant=None, *, revoked=False, patch_free=False):
    from veracium.store.sqlite import SqliteStore as _SS
    run = _dm_store(revoked=revoked)
    _dm_assert(run, "migrated", op_id="dm-run")
    s = _SS(run.path)
    if plant:
        plant(s)
        s._conn.commit()
    if patch_free:                                   # the C8 race: the registry reads FREE although a row is held
        mp.setattr(_SS, "_registry_held", lambda self, *a, **k: None)
    return s


def _undo_refused(s, reason, edge="dm-p", cid="u-1"):
    from veracium.store.base import UndoRefused as _UR
    try:
        with pytest.raises(_UR) as ei:
            s.undo_restoration(U, edge, correlation_id=cid)
        assert ei.value.reason == reason, ei.value.reason
    finally:
        s.close()


def _undo_raises(s, edge="dm-p", cid="u-1"):
    try:
        _raises(ValueError, s.undo_restoration, U, edge, correlation_id=cid)
    finally:
        s.close()


_SECOND_ROW = ("INSERT INTO migration_outcome(plan_id, user_id, edge_id, outcome, pre_invalidated_at, pre_reason, "
               "successor_evidence, applicable, origin, outcome_uid) VALUES('other-plan', ?, 'dm-p', 'restored', "
               "'2026-01-01T00:00:00+00:00', 'superseded', 'none', 1, 'imported', 'uid-other')")
_HELD_UNDO = ("INSERT INTO request_registry(user_id, correlation_id, verb, target_edge_id, request_digest, result_ref, "
              "written_at) VALUES(?, 'u-1', 'undo', 'dm-p', 'd', 'r', '2026-10-16T00:00:00+00:00')")


def _undone_under(cid):
    def plant(s):
        s.undo_restoration(U, "dm-p", correlation_id=cid)
    return plant


DECLINES.update({
    "store.undo.no-outcome": TwoPhase(lambda mp: _undo_store(mp), lambda s: _undo_refused(s, "no-outcome", edge="dm-q")),
    "store.undo.not-restored": TwoPhase(lambda mp: _undo_store(mp, revoked=True),
                                        lambda s: _undo_refused(s, "not-restored")),
    "store.undo.testimony": TwoPhase(lambda mp: _undo_store(mp, lambda s: s._conn.execute(
        "UPDATE migration_outcome SET origin='imported' WHERE edge_id='dm-p'")), lambda s: _undo_refused(s, "testimony")),
    "store.undo.not-applicable": TwoPhase(lambda mp: _undo_store(mp, lambda s: s._conn.execute(
        "UPDATE migration_outcome SET applicable=0 WHERE edge_id='dm-p'")), lambda s: _undo_refused(s, "not-applicable")),
    "store.undo.edge-unavailable": TwoPhase(lambda mp: _undo_store(mp, lambda s: s._conn.execute(
        "DELETE FROM edges WHERE id='dm-p'")), lambda s: _undo_refused(s, "edge-unavailable")),
    "store.undo.ambiguous-outcome": TwoPhase(lambda mp: _undo_store(mp, lambda s: s._conn.execute(_SECOND_ROW, (U,))),
                                             lambda s: _undo_refused(s, "ambiguous-outcome")),
    # a completed undo under u-1, then u-1 again for an edge with no outcome: the digest differs (a different edge)
    "store.undo.request-digest": TwoPhase(lambda mp: _undo_store(mp, _undone_under("u-1")),
                                          lambda s: _undo_raises(s, edge="dm-q")),
    # a completed undo whose outcome_uid no longer matches the registry's result_ref (planted)
    "store.undo.result-missing": TwoPhase(lambda mp: _undo_store(mp, lambda s: (_undone_under("u-1")(s), s._conn.execute(
        "UPDATE migration_outcome SET outcome_uid='moved' WHERE edge_id='dm-p'"))), lambda s: _undo_raises(s)),
    # C8: a held row the (patched) front lookup cannot see, so the INSERT meets the UNIQUE and the fallback, through
    # the same patched lookup, finds nothing either → the correlation conflict
    "store.undo.correlation": TwoPhase(lambda mp: _undo_store(mp, lambda s: s._conn.execute(_HELD_UNDO, (U,)),
                                                              patch_free=True), lambda s: _undo_raises(s)),
})
# specs/0047 INV-R18, R-II round 2's RII-01: bound_wiki's one decision (a body its call's snapshot does not admit is
# withheld), declining once on a cause
DECLINES.update({
    "compile.bind.unbound": TwoPhase(lambda mp: compile_mod._budgets.REDACTED_DURING_COMPILE_NOTICE,
                                     lambda why: compile_mod._bind_withholds(why)),
})
SITES.update({sid: census._REGISTRY[sid] for sid in census.registry()})


# THE PARAMETRISED SET IS FROZEN HERE, AFTER THE LAST ENTRY BLOCK (2026-09-20). A parametrize decorator
# evaluates its list when the function is DEFINED; every entry block must sit above this line, and the
# completeness test below asserts the frozen tuples equal the dicts so a block added beneath refuses loudly.
DECLINE_IDS = tuple(sorted(DECLINES))
SURFACE_IDS = tuple(sorted(SURFACE_DRIVEN))

# EXACT EXPECTED DELTAS (round 6, R6-7): every entry asserts an EXACT (consulted, fired, errors); the default is
# (1, 1, 0) and the exceptions are LITERALS frozen here, each with its derivation from the code path written beside
# it — never a number read back from the run it scores (a doubled increment would double both sides). A site whose
# condition sits inside a loop consults once per evaluation (census.consult's rule).
EXACT_DECLINE = {
    # validate(): the digest check is evaluated per MEMBER; the fixture's group has TWO members and the second
    # overlaps the first → consulted 2, fired 1
    "scope.policy.digest-overlap": (2, 1, 0),
}
EXACT_SURFACE = {
    # recall_at with ONE candidate: grounded(e) is evaluated by claim(e) (1), by `_fit_to_budget`'s assertable
    # filter (1), and by the two stats sums `grounded_items` / `unverified_items` (2) → 4 consults; the edge is
    # quarantined so every evaluation declines (declines=False) → 4 fired
    "asof.recall.grounded": (4, 4, 0),
    # claim(e) is evaluated once, by `_fit_to_budget`'s claims filter → (1, 1, 0)
    "asof.recall.claim": (1, 1, 0),
    # assemble(): the variant verdict is evaluated per MEMBER of the eligible group; two transient members, one
    # survivor → the other is the variant: consulted 2, fired 1
    "proactive.variant": (2, 1, 0),
    # one durable candidate, ineligible → (1, 1, 0)
    "proactive.eligible": (1, 1, 0),
}


def test_the_freeze_follows_every_entry_block():
    """The static half of the guard: no entry block (a `DECLINES = {`/`.update({` or the SURFACE_DRIVEN
    forms) may appear below the freeze line in this file — the class that hid fourteen executions."""
    src = pathlib.Path(__file__).read_text().splitlines()
    freeze = next(i for i, l in enumerate(src) if l.startswith("DECLINE_IDS = tuple(sorted(DECLINES))"))
    below = [i + 1 for i, l in enumerate(src) if i > freeze and re.match(r"^(DECLINES|SURFACE_DRIVEN)(\.update\(| = )", l)]
    assert below == [], f"entry block(s) below the freeze at line {freeze + 1}: {below}"
    # the control: the pattern finds the blocks that ARE above it (a regex that matched nothing would pass vacuously)
    above = [i for i, l in enumerate(src) if i < freeze and re.match(r"^(DECLINES|SURFACE_DRIVEN)(\.update\(| = )", l)]
    assert len(above) >= 2, above


def test_every_declared_site_has_one_declining_execution_here_and_vice_versa():
    declared = set(SITES)
    covered = set(DECLINES) | set(SURFACE_DRIVEN)
    assert declared == covered, (sorted(declared - covered), sorted(covered - declared))
    # and the PARAMETRISED sets are the dicts: an entry added below the freeze is a test that never runs
    assert set(DECLINE_IDS) == set(DECLINES) and set(SURFACE_IDS) == set(SURFACE_DRIVEN), \
        "an entry was added after the parametrised ids were frozen — it would never run; move its block above the freeze"


def test_the_collected_parametrisations_cover_every_declared_id(request):
    """The EXECUTION side (research, 2026-09-20): the two guards above compare artifacts that share a parent —
    the frozen tuple and the dict it was frozen from. This one takes the other side from pytest's own
    collection: the `site_id` of every collected node of the two parametrised tests in this module, which
    is what will actually RUN, and asserts it equals the declared set. A collection that fell short (the
    143-for-157 shape) is visible only from this side. Under a narrowed selection the collection is narrow
    by request, so this SKIPS BY NAME rather than reading a deselection as a defect — and it detects the
    narrowing by its EFFECT (a node of THIS module deselected, recorded by conftest's pytest_deselected
    hook; -k, -m, --deselect, --lf, --sw and any future narrower all reach it) or by a node id / file
    argument (which restricts collection without deselecting). A hand list of flags missed --sw, which
    deselects a random prefix under pytest-randomly, and the guard accused a correct tree (research,
    2026-09-20). A -k that keeps this whole module, or --lf on a cold cache, deselects nothing here and
    the guard ENFORCES. The recorder's PRESENCE is asserted (conftest initialises the attribute in
    pytest_configure): an absent recorder is a named failure, never a silent enforce — the third outcome."""
    cfg = request.config
    assert hasattr(cfg, "veracium_deselected"), \
        "the pytest_deselected recorder (tests/conftest.py) did not run — this guard cannot tell a whole collection from a narrowed one"
    this_module = request.node.nodeid.split("::")[0]
    deselected_here = sorted(n for n in cfg.veracium_deselected if n.split("::")[0] == this_module)
    narrowed = bool(deselected_here) or any("::" in a for a in cfg.args)
    if narrowed:
        pytest.skip(f"selection narrowed (a deselection in this module, or a node id on the command line): "
                    f"the collected-vs-declared comparison needs the whole module; {len(deselected_here)} of its nodes deselected")
    here = pathlib.Path(__file__).resolve()
    collected = {}
    for item in request.session.items:
        if pathlib.Path(str(item.fspath)).resolve() != here or not hasattr(item, "callspec"):
            continue
        collected.setdefault(item.originalname, set()).add(item.callspec.params.get("site_id"))
    ran = collected.get("test_one_declining_decision_moves_the_counters_by_exactly_one", set()) | \
          collected.get("test_the_surface_driven_sites_move_by_exactly_their_derived_counts", set())
    assert ran == set(SITES), (f"collected {len(ran)} parametrisations for {len(SITES)} declared ids: "
                               f"never collected {sorted(set(SITES) - ran)}; collected but undeclared {sorted(ran - set(SITES))}")


@pytest.mark.parametrize("site_id", DECLINE_IDS)
def test_one_declining_decision_moves_the_counters_by_exactly_one(site_id, enabled, monkeypatch):
    entry = DECLINES[site_id]
    if isinstance(entry, TwoPhase):
        state = entry.setup(monkeypatch)
        dc, df, de = _delta(site_id, lambda: entry.run(state))
    else:
        dc, df, de = _delta(site_id, lambda: entry(monkeypatch))
    expected = EXACT_DECLINE.get(site_id, (1, 1, 0))
    assert (dc, df, de) == expected, f"{site_id}: consulted moved {dc}, fired moved {df}, errors {de} (expected {expected})"


@pytest.mark.parametrize("site_id", SURFACE_IDS)
def test_the_surface_driven_sites_move_by_exactly_their_derived_counts(site_id, enabled):
    """Round 6, R6-7: `fired >= 1 and consulted >= fired` accepted a doubled increment ((8,8,0) for a
    (4,4,0) execution). Exact deltas against the frozen literals above."""
    dc, df, de = _delta(site_id, SURFACE_DRIVEN[site_id])
    assert (dc, df, de) == EXACT_SURFACE[site_id], f"{site_id}: consulted {dc}, fired {df}, errors {de} (expected {EXACT_SURFACE[site_id]})"


def test_r6_7_a_doubled_increment_fails_every_exact_delta(enabled, monkeypatch):
    """The control the round-6 reviewer ran: double every increment and require the exact assertions to REFUSE
    for every surface-driven site and for one ordinary entry — the test that could not fail before."""
    orig = census.Site._bump
    def twice(self, field):
        orig(self, field); orig(self, field)
    monkeypatch.setattr(census.Site, "_bump", twice)
    for sid in SURFACE_IDS:
        d = _delta(sid, SURFACE_DRIVEN[sid])
        assert d != EXACT_SURFACE[sid] and d == tuple(2 * x for x in EXACT_SURFACE[sid]), (sid, d)
    d = _delta("gate.partition-parts", lambda: DECLINES["gate.partition-parts"](monkeypatch))
    assert d == (2, 2, 0) != EXACT_DECLINE.get("gate.partition-parts", (1, 1, 0))
    # the SUPERSEDED assertion is the surviving mutant: the round-6 surface-driven check was `fired >= 1 and
    # consulted >= fired`, which every doubled delta above satisfies — that is exactly what the reviewer ran
    # (memory: superseded implementation is the mutant; the old rule kept as the negative control)
    for sid in SURFACE_IDS:
        c, f, e = tuple(2 * x for x in EXACT_SURFACE[sid])
        assert f >= 1 and c >= f and e == 0, (sid, "the old form would have refused this doubled delta — the control is wrong")


def test_r6_2a_a_consult_means_the_sites_own_condition_was_reached(enabled):
    """Cell B: `scoped_assertable(True, (False, "own"))` returns at the invisible check; the two later sites
    are NOT consulted (they were never evaluated). On the entitlement path all three are reached, one fires."""
    from veracium import gate
    ids = ("gate.scoped-assertable.invisible", "gate.scoped-assertable.third-party-shaped", "gate.scoped-assertable.entitlement")
    def deltas(fn):
        before = {i: SITES[i].counters() for i in ids}; fn(); after = {i: SITES[i].counters() for i in ids}
        return {i: tuple(after[i][k] - before[i][k] for k in ("consulted", "fired", "errors")) for i in ids}
    d = deltas(lambda: gate.scoped_assertable(True, (False, "own")))
    assert d == {ids[0]: (1, 1, 0), ids[1]: (0, 0, 0), ids[2]: (0, 0, 0)}, d
    d = deltas(lambda: gate.scoped_assertable(True, (True, "own"), subject_entitlement=False))
    assert d == {ids[0]: (1, 0, 0), ids[1]: (1, 0, 0), ids[2]: (1, 1, 0)}, d
