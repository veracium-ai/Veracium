"""specs/0014 Slice B — the contribution ledger: A1/A5/A7/A8/A9/A10 and the
set-equality trio, at both consumption sites.

Absorption: driven through the REAL public path (`apply_supersession` over a
subsuming restatement — the T1 branch). Consolidation: driven through the real
0010 primitives to the OUTPUTS_DURABLE cutover. Injections mutate plans the way
the reviewer would (omit / duplicate / add a draft) and assert the WHOLE op
aborts with no partial state (A7).
"""
import json
from datetime import datetime, timedelta, timezone

import pytest

from veracium.contribution import (canonical_payload, consolidation_op_key,
                                   evidence_ref_digest, validate_payload)
from veracium.graph import apply_supersession
from veracium.schema import (DEFAULT_RELATIONS, ConsolidationState, ContributionDraft, Disclosure, Edge, EvidenceAuthor, Episode, Provenance)
from veracium.source_identity import resolve_origin, source_identity_digest
from veracium.store.sqlite import SqliteStore, SupersessionIntegrityError

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _edge(uid, obj, *, conf=0.9, observed=NOW, source_id=None, ref="ev-1",
          eid=None):
    return Edge(
        id=eid or f"e-{obj.replace(' ', '-')}", user_id=uid, subject="user",
        relation="pet", object=obj, valid_from=observed,
        provenance=Provenance(
            author_of_evidence=EvidenceAuthor.USER,
            evidence_ref=ref, observed_at=observed, confidence=conf,
            source_id=source_id))


def _store(tmp_path):
    return SqliteStore(str(tmp_path / "s.db"))


def _absorb(store, uid="u1", *, source_id="src-A", conf=0.8):
    """Persist a prior, then a MORE specific restatement that absorbs it."""
    prior = _edge(uid, "Miso", conf=conf, observed=NOW - timedelta(days=3),
                  source_id=source_id, eid=f"e-prior-{uid}")
    apply_supersession(store, prior, DEFAULT_RELATIONS)
    winner = _edge(uid, "cat Miso", conf=0.9, observed=NOW,
                   eid=f"e-winner-{uid}")
    apply_supersession(store, winner, DEFAULT_RELATIONS)
    return prior, winner


# -- A1 / A5 / the absorption payload ---------------------------------------

def test_absorption_writes_one_ledger_row_per_absorbed_prior(tmp_path):
    store = _store(tmp_path)
    prior, winner = _absorb(store)
    recs = store.contributions("u1", "edge", winner.id)
    assert len(recs) == 1
    r = recs[0]
    assert r.site == "absorption" and r.survivor_id == winner.id
    assert r.op_key is None                       # absorption rides 0003's receipt
    assert set(r.payload) == {"base", "contributor"}
    assert r.payload["contributor"]["confidence"] == 0.8


def test_absorption_records_the_contributor_even_when_no_value_moves(tmp_path):
    """A1, the named test: an older/weaker absorbed prior moves no max() yet is
    recorded — its base+contributor payload SHOWING the no-op transfer."""
    store = _store(tmp_path)
    prior, winner = _absorb(store, conf=0.5)      # weaker AND older: nothing moves
    recs = store.contributions("u1", "edge", winner.id)
    assert len(recs) == 1
    p = recs[0].payload
    assert p["contributor"]["confidence"] == 0.5 < p["base"]["confidence"]
    assert p["contributor"]["observed_at"] < p["base"]["observed_at"]


def test_the_base_side_is_the_pre_inheritance_snapshot(tmp_path):
    """R3-1: `base` carries the incoming's ORIGINAL values — after inheritance
    the survivor's stored valid_from is the PRIOR's (min), but the recorded base
    keeps the incoming's own later date."""
    store = _store(tmp_path)
    prior, winner = _absorb(store)
    r = store.contributions("u1", "edge", winner.id)[0]
    from veracium.contribution import json_datetime
    assert r.payload["base"]["valid_from"] == json_datetime(NOW)       # original
    stored = [e for e in store.edges("u1", active_only=True)
              if e.id == winner.id][0]
    assert stored.valid_from == NOW - timedelta(days=3)                # inherited


def test_contribution_records_are_content_free(tmp_path):
    """A5: no object/note/summary anywhere in a ledger row; identity is digests."""
    store = _store(tmp_path)
    _, winner = _absorb(store)
    r = store.contributions("u1", "edge", winner.id)[0]
    flat = json.dumps(r.payload) + (r.identity_digest or "") + (r.evidence_ref_digest or "")
    assert "Miso" not in flat
    for side in r.payload.values():
        for v in side.values():
            assert isinstance(v, (str, int, float, bool))


def test_identity_digest_null_iff_source_id_absent(tmp_path):
    """0006 rule 8 / I13 carried into the ledger (F1)."""
    store = _store(tmp_path)
    _, w1 = _absorb(store, source_id="src-A")
    assert store.contributions("u1", "edge", w1.id)[0].identity_digest is not None
    _, w2 = _absorb(store, uid="u2", source_id=None)
    assert store.contributions("u2", "edge", w2.id)[0].identity_digest is None


# -- A7: atomicity + the set-equality trio ----------------------------------

def _plan_for_absorption(store, uid="u1"):
    """Build the real absorption plan, returned unapplied, for injection."""
    from veracium.graph import _build_supersession_plan
    prior = _edge(uid, "Miso", conf=0.8, observed=NOW - timedelta(days=3),
                  source_id="src-A", eid="e-prior")
    apply_supersession(store, prior, DEFAULT_RELATIONS)
    winner = _edge(uid, "cat Miso", conf=0.9, observed=NOW,
                   eid=f"e-winner-{uid}")
    import uuid
    plan, _ = _build_supersession_plan(store, winner, DEFAULT_RELATIONS,
                                    f"op-{uuid.uuid4().hex[:8]}")
    assert plan.contribution_drafts, "fixture must reach the absorption branch"
    return plan


def _assert_aborted(store, plan, uid="u1"):
    with pytest.raises((SupersessionIntegrityError, ValueError)):
        store.apply_supersession_plan(plan)
    # no partial state: no winner edge, no ledger rows for it
    assert not [e for e in store.edges(uid, active_only=True)
                if e.id == plan.incoming_edge.id]
    assert store.contributions(uid, "edge", plan.incoming_edge.id) == []


def test_an_omitted_absorption_draft_aborts(tmp_path):
    store = _store(tmp_path)
    plan = _plan_for_absorption(store)
    plan.contribution_drafts.pop()
    _assert_aborted(store, plan)


def test_a_duplicated_absorption_draft_aborts(tmp_path):
    store = _store(tmp_path)
    plan = _plan_for_absorption(store)
    plan.contribution_drafts.append(plan.contribution_drafts[0])
    _assert_aborted(store, plan)


def test_an_extra_absorption_draft_aborts(tmp_path):
    store = _store(tmp_path)
    plan = _plan_for_absorption(store)
    plan.contribution_drafts.append(ContributionDraft(
        site="absorption", survivor_type="edge",
        survivor_id=plan.incoming_edge.id,
        contributor_type="edge", contributor_id="e-not-invalidated"))
    _assert_aborted(store, plan)


def test_a_cross_tenant_draft_aborts(tmp_path):
    store = _store(tmp_path)
    other = _edge("u2", "Rex", eid="e-foreign-u2")
    apply_supersession(store, other, DEFAULT_RELATIONS)
    plan = _plan_for_absorption(store)
    plan.contribution_drafts[0] = ContributionDraft(
        site="absorption", survivor_type="edge",
        survivor_id=plan.incoming_edge.id,
        contributor_type="edge", contributor_id="e-foreign-u2")
    # the invalidation list must "match" for set equality, so forge that too —
    # the tenant check must still catch it
    plan.prior_invalidations = [("e-foreign-u2", NOW, "absorbed_duplicate")]
    _assert_aborted(store, plan)


def test_a_rolled_back_maintenance_op_writes_no_ledger_row(tmp_path):
    """A7: inject a failure AFTER the ledger write but before commit — the row
    must roll back with the op (rows atomic with the maintenance transaction)."""
    store = _store(tmp_path)
    plan = _plan_for_absorption(store)
    original = store._upsert_edge_row
    calls = {"n": 0}

    def exploding(e):
        calls["n"] += 1
        if e.id == plan.incoming_edge.id:
            raise RuntimeError("injected failure after the ledger write")
        return original(e)

    store._upsert_edge_row = exploding
    with pytest.raises(RuntimeError):
        store.apply_supersession_plan(plan)
    store._upsert_edge_row = original
    assert store.contributions("u1", "edge", plan.incoming_edge.id) == []


def test_an_empty_payload_aborts_via_validation():
    """{} is an integrity error EVERYWHERE (v8) — at the validation layer both
    site schemas refuse emptiness and None-encoding."""
    with pytest.raises(ValueError):
        validate_payload("absorption", {})
    with pytest.raises(ValueError):
        validate_payload("absorption", {"base": {}, "contributor": {}})
    with pytest.raises(ValueError):
        validate_payload("consolidation", {"input": {}, "output_index": 0})
    with pytest.raises(ValueError):
        validate_payload("consolidation", {})
    with pytest.raises(ValueError):                    # None never encoded
        validate_payload("absorption", {
            "base": {"observed_at": "t", "confidence": 1.0, "valid_from": "t",
                     "disclosure": "mentionable", "derived_from": None},
            "contributor": {"observed_at": "t", "confidence": 1.0,
                            "valid_from": "t", "disclosure": "mentionable"}})
    with pytest.raises(ValueError):                    # closed: unknown key
        validate_payload("absorption", {
            "base": {"observed_at": "t", "confidence": 1.0, "valid_from": "t",
                     "disclosure": "mentionable", "object": "cat Miso"},
            "contributor": {"observed_at": "t", "confidence": 1.0,
                            "valid_from": "t", "disclosure": "mentionable"}})
    with pytest.raises(ValueError):                    # closed site set
        validate_payload("severed", {"base": {}, "contributor": {}})


# -- consolidation: N×M at the cutover + A8 op_key ---------------------------

def _run_consolidation(store, uid="u1", n_inputs=3):
    for i in range(n_inputs):
        store.add_episode(Episode(
            id=f"ep-{i}", user_id=uid, date=f"2026-07-0{i+1}",
            summary=f"day {i}", provenance=Provenance(
                author_of_evidence=EvidenceAuthor.USER,
                evidence_ref=f"ev-{i}", observed_at=NOW,
                confidence=0.9, source_id=f"src-{i}")))
    op = store.create_or_takeover_consolidation(
        uid, [f"ep-{i}" for i in range(n_inputs)], "w1", 60)
    assert store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w1", ConsolidationState.GENERATING)
    from veracium.schema import ConsolidationOutputDraft
    assert store.write_consolidation_output_if_current(
        op.operation_id, op.fence, "w1",
        ConsolidationOutputDraft(summary="the week", date_start="2026-07-01",
                                 date_end="2026-07-03"))
    assert store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w1", ConsolidationState.OUTPUTS_DURABLE)
    outs = [ep for _, ep in store._episodes_for_operation(uid, op.operation_id)
            if ep.lineage]
    return op, outs


def test_consolidation_writes_n_by_m_rows_at_the_cutover(tmp_path):
    """A2/A7: every claimed input × every written output, exact by construction."""
    store = _store(tmp_path)
    op, outs = _run_consolidation(store, n_inputs=3)
    assert len(outs) == 1
    recs = store.contributions("u1", "episode", outs[0].id)
    assert len(recs) == 3
    assert {r.op_key for r in recs} == {
        consolidation_op_key(op.operation_id, r.payload["output_index"],
                             "episode", f"ep-{i}")
        for i, r in enumerate(sorted(recs, key=lambda x: x.op_key))}
    for r in recs:
        assert r.site == "consolidation"
        assert set(r.payload) == {"input", "output_index"}
        assert set(r.payload["input"]) >= {"observed_at", "confidence",
                                           "disclosure", "author_of_evidence",
                                           "date"}


def test_a_mis_keyed_op_key_conflict_aborts_never_ignores(tmp_path):
    """A8/R3-3: a pre-existing row under the same op_key with DIFFERENT
    deterministic fields aborts the cutover — a silent DO NOTHING would lose an
    attribution invisibly."""
    store = _store(tmp_path)
    for i in range(2):
        store.add_episode(Episode(
            id=f"ep-{i}", user_id="u1", date=f"2026-07-0{i+1}",
            summary=f"day {i}", provenance=Provenance(
                author_of_evidence=EvidenceAuthor.USER,
                evidence_ref=f"ev-{i}", observed_at=NOW, confidence=0.9)))
    op = store.create_or_takeover_consolidation("u1", ["ep-0", "ep-1"], "w1", 60)
    assert store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w1", ConsolidationState.GENERATING)
    from veracium.schema import ConsolidationOutputDraft
    assert store.write_consolidation_output_if_current(
        op.operation_id, op.fence, "w1",
        ConsolidationOutputDraft(summary="the week", date_start="2026-07-01",
                                 date_end="2026-07-03"))
    # forge a conflicting row under the key the cutover will derive
    key = consolidation_op_key(op.operation_id, 0, "episode", "ep-0")
    store._conn.execute(
        "INSERT INTO contribution_ledger(id,user_id,survivor_type,survivor_id,"
        "site,identity_digest,evidence_ref_digest,payload,op_key,created_at) "
        "VALUES('contrib-forged','u1','episode','WRONG-SURVIVOR','consolidation',"
        "NULL,NULL,'{\"forged\":true}',?,?)", (key, NOW.isoformat()))
    store._conn.commit()
    with pytest.raises(SupersessionIntegrityError):
        store.transition_consolidation_if_current(
            op.operation_id, op.fence, "w1",
            ConsolidationState.OUTPUTS_DURABLE)


# -- A9: the revocation join --------------------------------------------------

def test_contributors_of_source_joins_a_revocation_pair(tmp_path):
    """A9: write via a site, then look up by the SAME digest primitive a
    revocation would derive — the row is found; unknown-source rows never join."""
    store = _store(tmp_path)
    _, winner = _absorb(store, source_id="src-A")
    local = store.local_origin()
    d = source_identity_digest(resolve_origin(None, local), "src-A")
    hits = store.contributors_of_source("u1", d)
    assert [h.survivor_id for h in hits] == [winner.id]
    assert store.contributors_of_source("u1", None) == []


# -- A10: retention -----------------------------------------------------------

def test_ledger_row_is_dropped_with_its_survivor(tmp_path):
    """A10, incl. the same-raw-id Edge+Episode pair: deleting one leaves the
    other's rows (type-keyed, R1-5)."""
    store = _store(tmp_path)
    op, outs = _run_consolidation(store, n_inputs=2)
    survivor = outs[0].id
    assert store.contributions("u1", "episode", survivor)
    # a same-raw-id EDGE row in the ledger must survive the EPISODE deletion
    store._conn.execute(
        "INSERT INTO contribution_ledger(id,user_id,survivor_type,survivor_id,"
        "site,identity_digest,evidence_ref_digest,payload,op_key,created_at) "
        "VALUES('contrib-edge-twin','u1','edge',?, 'absorption',NULL,NULL,"
        "'{\"base\":{},\"contributor\":{}}',NULL,?)", (survivor, NOW.isoformat()))
    store._conn.commit()
    store.delete_episode(survivor)
    assert store.contributions("u1", "episode", survivor) == []
    assert store.contributions("u1", "edge", survivor)         # the twin lives


def test_forget_user_erases_the_ledger(tmp_path):
    store = _store(tmp_path)
    _, winner = _absorb(store)
    assert store.contributions("u1", "edge", winner.id)
    store.forget_user("u1")
    assert store.contributions("u1", "edge", winner.id) == []


# -- the evidence-ref digest construction ------------------------------------

def test_evidence_ref_digest_is_domain_separated_and_null_on_empty():
    assert evidence_ref_digest("o", "") is None                # "" DEFINED absent
    a = evidence_ref_digest("o", "ref")
    b = source_identity_digest("o", "ref")
    assert a and b and a != b                                  # its own domain
    with pytest.raises(ValueError):
        evidence_ref_digest(None, "ref")                       # resolve first
