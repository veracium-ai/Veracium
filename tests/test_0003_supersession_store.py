"""specs/0003 — the store layer: `apply_supersession_plan` (§4f) and the v3→v4 schema.

These pin the primitive's invariants directly (I5, I9) — the CAS linearization, the
durable idempotency receipt, the complete `expected_state`, the content-free refusal
inventory, and all-or-nothing failure — plus the additive v3→v4 migration and its
wiki-cache drop. The write-guard (§4a) and read layer (§4c-ii/§4e) that USE this primitive
are exercised in their own test files (Slices B and C).
"""
import sqlite3

import pytest

from veracium.authority import RULE_VERSION, effective, scope_fingerprint
from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance, SourceType,
                             SupersessionPlan, SupersessionRefusalDraft)
from veracium.store.base import PLAN_STALE, SupersessionIntegrityError
from veracium.store.migration import migrate_store
from veracium.store.schema_version import SCHEMA_V3, SCHEMA_VERSION
from veracium.store.sqlite import SqliteStore

U = "u1"


def _edge(eid, author, obj, disc=Disclosure.MENTIONABLE, df=None, rel="works_as",
          needs_confirmation=False):
    return Edge(id=eid, user_id=U, subject="user", relation=rel, object=obj,
                needs_confirmation=needs_confirmation,
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=author, evidence_ref="ev",
                                      disclosure=disc, derived_from=df))


def _fp(store, subject="user", relation="works_as"):
    return scope_fingerprint(store.edges(U, subject=subject, relation=relation,
                                         active_only=True, include_quarantined=True))


def _refusal_plan(store, prior, incoming, op="op-1"):
    return SupersessionPlan(
        incoming_edge=incoming, insert_incoming=True, operation_id=op,
        expected_state=_fp(store),
        refusals=[SupersessionRefusalDraft(
            prior_edge_id=prior.id, incoming_edge_id=incoming.id, relation="works_as",
            prior_effective=effective(prior.provenance.author_of_evidence, None),
            incoming_effective=effective(incoming.provenance.author_of_evidence, None))])


# --- I5: a refusal is recorded, content-free -----------------------------------

def test_a_refused_supersession_is_counted_and_logged(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p1", EvidenceAuthor.USER, "CFO at Acme")
    s.add_edge(prior)
    inc = _edge("i1", EvidenceAuthor.THIRD_PARTY, "unemployed", Disclosure.QUARANTINED)
    res = s.apply_supersession_plan(_refusal_plan(s, prior, inc))
    assert res.refused == 1 and res.inserted_incoming
    assert s.supersessions_refused(U) == 1                     # the durable counter
    (r,) = s.refusals(U)
    assert r.prior_edge_id == "p1" and r.incoming_edge_id == "i1"
    assert r.prior_effective == 3 and r.incoming_effective == 0
    assert r.rule_version == RULE_VERSION
    # content-free: only opaque ids, relation, authority levels — never memory content
    dumped = r.model_dump_json()
    assert "CFO" not in dumped and "unemployed" not in dumped and "Acme" not in dumped


def test_refused_supersession_keeps_both_edges_active(tmp_path):  # I3 at the store layer
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p1", EvidenceAuthor.USER, "CFO at Acme")
    s.add_edge(prior)
    inc = _edge("i1", EvidenceAuthor.THIRD_PARTY, "unemployed", Disclosure.QUARANTINED)
    s.apply_supersession_plan(_refusal_plan(s, prior, inc))
    assert {e.id for e in s.edges(U, active_only=True)} == {"p1", "i1"}


def test_forget_user_erases_the_refusal_inventory_and_receipts(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p1", EvidenceAuthor.USER, "CFO at Acme")
    s.add_edge(prior)
    s.apply_supersession_plan(_refusal_plan(
        s, prior, _edge("i1", EvidenceAuthor.THIRD_PARTY, "x", Disclosure.QUARANTINED)))
    assert s.supersessions_refused(U) == 1
    s.forget_user(U)
    assert s.supersessions_refused(U) == 0
    with sqlite3.connect(str(tmp_path / "s.db")) as c:
        assert c.execute("SELECT COUNT(*) FROM supersession_operations "
                         "WHERE user_id=?", (U,)).fetchone()[0] == 0


# --- I9: CAS linearization, durable receipt, complete expected_state ------------

def test_concurrent_equal_authority_plans_do_not_branch(tmp_path):
    """Two concurrent equal-authority updates read the same pre-state and both plan
    "retire the prior, insert mine". The first commits; the second, carrying the now-stale
    `expected_state`, gets PlanStale — so a functional relation never branches into two
    current values (round-8 blocker 3)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    p = _edge("p", EvidenceAuthor.USER, "CFO")
    s.add_edge(p)
    fp = _fp(s)
    a = _edge("a", EvidenceAuthor.USER, "CEO")
    b = _edge("b", EvidenceAuthor.USER, "CTO")
    plan_a = SupersessionPlan(incoming_edge=a, insert_incoming=True, operation_id="A",
                              expected_state=fp,
                              prior_invalidations=[("p", a.valid_from, "superseded")])
    plan_b = SupersessionPlan(incoming_edge=b, insert_incoming=True, operation_id="B",
                              expected_state=fp,
                              prior_invalidations=[("p", b.valid_from, "superseded")])
    assert not isinstance(s.apply_supersession_plan(plan_a), type(PLAN_STALE))
    assert s.apply_supersession_plan(plan_b) is PLAN_STALE     # stale — no branch
    active = {e.object for e in s.edges(U, active_only=True)}
    assert active == {"CEO"}                                   # exactly one current value


def test_expected_state_catches_an_in_place_field_edit(tmp_path):
    """A same-id row whose value/author/derived_from changed between the plan's read and
    commit must yield PlanStale — the coarse active-set alone would miss it (round-9 C)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    s.add_edge(_edge("p", EvidenceAuthor.USER, "CFO"))
    fp = _fp(s)
    # an in-place edit of the SAME id (same active-set, different value)
    s.add_edge(_edge("p", EvidenceAuthor.USER, "CFO at Acme"))
    plan = SupersessionPlan(incoming_edge=_edge("i", EvidenceAuthor.USER, "CEO"),
                            insert_incoming=True, operation_id="op", expected_state=fp,
                            prior_invalidations=[("p", _edge("i", EvidenceAuthor.USER, "CEO").valid_from, "superseded")])
    assert s.apply_supersession_plan(plan) is PLAN_STALE


def test_reinforcement_plan_inserts_no_duplicate(tmp_path):
    """A reinforcement plan is `insert_incoming=False`: it refreshes the existing prior
    and inserts NOTHING, so re-stating a fact does not duplicate it (§4f)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p", EvidenceAuthor.USER, "CFO")
    s.add_edge(prior)
    refreshed = prior.model_copy(deep=True)
    refreshed.provenance.confidence = 0.99
    plan = SupersessionPlan(incoming_edge=_edge("i", EvidenceAuthor.USER, "CFO"),
                            insert_incoming=False, operation_id="op",
                            expected_state=_fp(s), prior_upserts=[refreshed])
    res = s.apply_supersession_plan(plan)
    assert not res.inserted_incoming
    ids = {e.id for e in s.edges(U, active_only=True)}
    assert ids == {"p"}                                        # no "i" inserted


def test_a_lost_reinforcement_response_replays_via_the_durable_receipt(tmp_path):
    """A reinforcement commits with no incoming edge and no refusal row — so the receipt
    is the ONLY durable evidence it happened. After a 'lost response' the same operation
    replays as a no-op rather than double-refreshing (round-9 blocker 3)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p", EvidenceAuthor.USER, "CFO")
    s.add_edge(prior)
    refreshed = prior.model_copy(deep=True)
    refreshed.provenance.confidence = 0.99
    plan = SupersessionPlan(incoming_edge=_edge("i", EvidenceAuthor.USER, "CFO"),
                            insert_incoming=False, operation_id="op-reinforce",
                            expected_state=_fp(s), prior_upserts=[refreshed])
    first = s.apply_supersession_plan(plan)
    assert not first.replayed
    v1 = s.store_version(U)
    second = s.apply_supersession_plan(plan)                   # the lost-response replay
    assert second.replayed
    assert s.store_version(U) == v1                            # replay is a true no-op


def test_receipt_check_precedes_cas_so_a_committed_op_replays_not_planstale(tmp_path):
    """After an op commits, its OWN `expected_state` is now stale. Re-driving the SAME
    operation_id must REPLAY (receipt check first), not trip PlanStale (round-9 blocker 3)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p", EvidenceAuthor.USER, "CFO")
    s.add_edge(prior)
    inc = _edge("i", EvidenceAuthor.THIRD_PARTY, "unemployed", Disclosure.QUARANTINED)
    plan = _refusal_plan(s, prior, inc, op="op-x")
    assert s.apply_supersession_plan(plan).refused == 1        # commits; scope now changed
    assert scope_fingerprint(s.edges(U, subject="user", relation="works_as",
                                     active_only=True)) != plan.expected_state
    replay = s.apply_supersession_plan(plan)                   # same op, now-stale state
    assert replay.replayed                                     # receipt wins over CAS
    assert s.supersessions_refused(U) == 1                     # not doubled


def test_reused_operation_id_with_different_content_is_an_integrity_error(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p", EvidenceAuthor.USER, "CFO")
    s.add_edge(prior)
    s.apply_supersession_plan(_refusal_plan(
        s, prior, _edge("i1", EvidenceAuthor.THIRD_PARTY, "x", Disclosure.QUARANTINED), op="dup"))
    other = SupersessionPlan(incoming_edge=_edge("i2", EvidenceAuthor.USER, "CEO"),
                             insert_incoming=True, operation_id="dup", expected_state=_fp(s))
    with pytest.raises(SupersessionIntegrityError):
        s.apply_supersession_plan(other)


def test_a_failed_plan_leaves_no_partial_state(tmp_path):
    """A plan that fails mid-apply (a refusal bound to a non-existent prior) rolls the
    WHOLE plan back: no incoming edge, no receipt, no partial rows (§4f failure rule)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    s.add_edge(_edge("p", EvidenceAuthor.USER, "CFO"))
    inc = _edge("i", EvidenceAuthor.THIRD_PARTY, "x", Disclosure.QUARANTINED)
    bad = SupersessionPlan(
        incoming_edge=inc, insert_incoming=True, operation_id="op", expected_state=_fp(s),
        refusals=[SupersessionRefusalDraft(prior_edge_id="does-not-exist",
                  incoming_edge_id="i", relation="works_as",
                  prior_effective=3, incoming_effective=0)])
    with pytest.raises(ValueError):
        s.apply_supersession_plan(bad)
    assert {e.id for e in s.edges(U, active_only=False)} == {"p"}   # incoming NOT persisted
    assert s.supersessions_refused(U) == 0
    with sqlite3.connect(str(tmp_path / "s.db")) as c:
        assert c.execute("SELECT COUNT(*) FROM supersession_operations").fetchone()[0] == 0


def test_a_refusal_cannot_be_forged_against_another_users_edge(tmp_path):
    """The store BINDS each refusal to an existing edge of THIS user (round-6 corr C)."""
    s = SqliteStore(str(tmp_path / "s.db"))
    other = Edge(id="other", user_id="u2", subject="user", relation="works_as", object="x",
                 provenance=Provenance(source_type=SourceType.STATED,
                                       author_of_evidence=EvidenceAuthor.USER, evidence_ref="e"))
    s.add_edge(other)
    inc = _edge("i", EvidenceAuthor.THIRD_PARTY, "x", Disclosure.QUARANTINED)
    forged = SupersessionPlan(
        incoming_edge=inc, insert_incoming=True, operation_id="op", expected_state=_fp(s),
        refusals=[SupersessionRefusalDraft(prior_edge_id="other", incoming_edge_id="i",
                  relation="works_as", prior_effective=3, incoming_effective=0)])
    with pytest.raises(ValueError):
        s.apply_supersession_plan(forged)


def test_forming_and_resolving_a_contention_both_drop_the_wiki(tmp_path):
    """§4c-ii (round-10 B1): the wiki drop is symmetric. Forming a refusal contention
    drops it; a later permitted supersession that retires a refusal member (resolution)
    drops it again — so a stale wiki never survives either transition."""
    s = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("p", EvidenceAuthor.USER, "CFO")
    s.add_edge(prior)
    inc = _edge("i", EvidenceAuthor.THIRD_PARTY, "unemployed", Disclosure.QUARANTINED)
    s.apply_supersession_plan(_refusal_plan(s, prior, inc, op="form"))    # FORM
    s.set_wiki(U, "recompiled after formation", s.store_version(U))
    assert s.get_wiki(U) is not None
    # a permitted USER supersession retires the prior (a refusal member) → RESOLUTION
    new = _edge("n", EvidenceAuthor.USER, "CEO")
    resolve = SupersessionPlan(incoming_edge=new, insert_incoming=True, operation_id="resolve",
                               expected_state=_fp(s),
                               prior_invalidations=[("p", new.valid_from, "superseded")])
    assert not isinstance(s.apply_supersession_plan(resolve), type(PLAN_STALE))
    assert s.get_wiki(U) is None                                          # resolution dropped it


# --- the v3→v4 migration -------------------------------------------------------

def _build_v3(path):
    c = sqlite3.connect(path)
    for o in SCHEMA_V3:
        c.execute(o.ddl)
    c.execute("PRAGMA user_version = 3")
    c.commit()
    c.close()


def test_v3_to_v4_migration_adds_both_tables_and_is_additive(tmp_path):
    p = str(tmp_path / "v3.db")
    _build_v3(p)
    # seed a wiki row compiled under pre-0003 semantics — the migration must drop it
    with sqlite3.connect(p) as c:
        c.execute("INSERT INTO wiki(user_id,text,store_version) VALUES('u','stale',1)")
        c.commit()
    assert str(migrate_store(p)) == "migrated"
    with sqlite3.connect(p) as c:
        # head-relative since the 0006 v4→v5 bump: migrate_store now brings v3 all the
        # way to head; the 0003 tables still land as part of that path (this test's point).
        assert c.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "supersession_refusals" in tables and "supersession_operations" in tables
        # the pre-0003 wiki cache was invalidated (§7a)
        assert c.execute("SELECT COUNT(*) FROM wiki").fetchone()[0] == 0
    SqliteStore(p)                                             # opens cleanly at head
    assert str(migrate_store(p)) == "current"                 # idempotent


def test_an_old_build_opening_a_v4_store_refuses_rather_than_losing_the_inventory(tmp_path):
    """0007: an older build (head < 4) opening a v4 store REFUSES ('newer') rather than
    silently dropping the refusal inventory it cannot represent (§7a)."""
    import veracium.store.schema_version as sv
    p = str(tmp_path / "v4.db")
    SqliteStore(p)                                             # a real v4 store
    from veracium.store.schema_version import StoreVersionError
    orig = sv.SCHEMA_VERSION
    try:
        sv.SCHEMA_VERSION = 3                                  # simulate an older build
        with pytest.raises(StoreVersionError):
            SqliteStore(p)
    finally:
        sv.SCHEMA_VERSION = orig
