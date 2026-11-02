"""R-II round 2's RII-R2-01: a cached wiki stays bound to what it may assert across EVERY write, a same-ID replace
included (specs/0047 §4d, INV-R3, INV-R18, the owner's F7 twin rule; specs/0004 W1, W7, W9).

The reviewer's finding was that the wiki's evictions were found by a census of functions already deleting the wiki
row, which cannot show that every NECESSARY eviction exists. This file answers it by behaviour, in four parts:

1. THE VIEW'S PARTITION (`schema.assertion_view`, `schema.ASSERTION_VIEW_KEEPS`): every Edge, Provenance and
   Episode field is mutated alone; a field in the view changes the view, a field in the keeps does not, and the
   mutation table is total over the models' fields (a new field fails here until it is placed and mutated).
2. THE WRITER INVENTORY, by writer × mutation class (research's stage-1 Q-c): every public SqliteStore method is
   classed, a READ or a WRITER naming the cells that run it; each cell performs one mutation class against a cached
   wiki on a real store and asserts EVICT or KEEP — and, independently of that expectation, the GENERIC ORACLE: the
   wiki survives a write iff no pre-existing record's assertion view changed.
3. THE RECALL-LEVEL REGRESSIONS, sequential and interleaved, cached and compiled: the reviewer's two families (the
   twin witness without its row-survives precondition, which the fix makes false by design) and research's stage-1
   families — demotion to quarantined and to use_only, a same-ID content change, the drawn record becoming a twin,
   an episode's demotion. Their KEEP controls: record_outcome counters, decay's confidence, a note, needs_confirmation.
4. D2 (defence in depth): with the write-side eviction disabled, a compiled body that failed its bind is not served
   back from its own cache row on the retry.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import re
import sys
from datetime import datetime, timedelta, timezone

import pytest

from veracium import Memory, MemoryConfig
from veracium.schema import (ASSERTION_VIEW_KEEPS, Disclosure, Edge, Episode, EvidenceAuthor, Outcome, Provenance,
                             Volatility, _ASSERTION_VIEW_READS, assertion_view)
from veracium.store.sqlite import SqliteStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
U = "u-r2-01"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _prov(**kw):
    return Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-r2-01",
                      disclosure=Disclosure.MENTIONABLE, **kw)


def _edge(eid="e-loc", obj="Lisbon", **kw):
    return Edge(id=eid, user_id=U, subject="user", relation="located_at", object=obj, provenance=_prov(),
                valid_from=T0, **kw)


def _ep(eid="p-1", summary="The user moved to Lisbon.", **kw):
    return Episode(id=eid, user_id=U, date="2026-01-02", summary=summary, provenance=_prov(), **kw)


# ---------------------------------------------------------------------------------------------------------------------
# 1. the view's partition
# ---------------------------------------------------------------------------------------------------------------------

_NOW = T0 + timedelta(days=3)
# one changed value per field (model_copy does not validate: the view is a function of the values, not of a write)
EDGE_MUTATIONS = {
    "id": "e-other", "user_id": "v", "subject": "boss", "relation": "works_at", "object": "Porto", "note": "a note",
    "volatility": Volatility.TRANSIENT, "provenance": None, "valid_from": T0 - timedelta(days=9),
    "invalidated_at": None, "invalidation_reason": None, "supersedes": "e-0", "original_relation": "lives_in",
    "needs_confirmation": True, "agreement": "an agreement record", "att": "attested", "src": "s-1",
    "attv": "ATTEST-6", "ungrounded": True, "times_used": 4, "outcome_counts": {"confirmed": 2},
    "last_outcome": Outcome.CONFIRMED, "last_outcome_at": _NOW,
}
PROVENANCE_MUTATIONS = {
    "author_of_evidence": EvidenceAuthor.THIRD_PARTY, "evidence_ref": "ev-2", "observed_at": _NOW,
    "disclosure": Disclosure.QUARANTINED, "confidence": 0.31, "derived_from": EvidenceAuthor.THIRD_PARTY,
    "source_id": "src-9", "origin": "o-9", "record_kind": "procedural", "basis": "stated", "producer": "host",
}
EPISODE_MUTATIONS = {
    "id": "p-other", "user_id": "v", "date": "2026-02-02", "summary": "The user moved to Porto.", "provenance": None,
    "kind": "outcome", "edge_id": "e-loc", "outcome": Outcome.CONFIRMED, "context_ref": "rubric-1",
    "consolidation_output_index": 0, "retired_reason": None, "retired_at": None, "seq": 3,
    "supersedes_episode": "p-0", "judgment_time_known": True, "claimed_by": "op-1", "operation_id": "op-1",
    "lineage": ["p-0"], "date_start": "2026-01-01", "date_end": "2026-01-03",
}
# retirement is the view's liveness component: its fields are keeps alone and move the view through their reason
LIVENESS = {"invalidated_at", "invalidation_reason", "retired_at", "retired_reason"}


@pytest.mark.parametrize("table, model", [(EDGE_MUTATIONS, Edge), (PROVENANCE_MUTATIONS, Provenance),
                                          (EPISODE_MUTATIONS, Episode)], ids=["edge", "provenance", "episode"])
def test_the_mutation_tables_are_total(table, model):
    assert set(table) == set(model.model_fields), sorted(set(table) ^ set(model.model_fields))


def _cases(kind, base, table):
    for f, v in table.items():
        if f == "provenance" or f in LIVENESS:
            continue
        yield pytest.param(kind, base, f, v, f in _ASSERTION_VIEW_READS[kind], id=f"{kind}-{f}")


@pytest.mark.parametrize("kind, base, field, value, in_view",
                         [*_cases("edge", _edge(), EDGE_MUTATIONS), *_cases("episode", _ep(), EPISODE_MUTATIONS)])
def test_a_field_changes_the_view_iff_the_view_reads_it(kind, base, field, value, in_view):
    changed = base.model_copy(update={field: value})
    assert (assertion_view(changed) != assertion_view(base)) is in_view
    assert in_view is (field not in ASSERTION_VIEW_KEEPS[kind])


@pytest.mark.parametrize("base", [_edge(), _ep()], ids=["edge", "episode"])
@pytest.mark.parametrize("field, value", list(PROVENANCE_MUTATIONS.items()))
def test_a_provenance_field_changes_the_view_iff_the_view_reads_it(base, field, value):
    changed = base.model_copy(update={"provenance": base.provenance.model_copy(update={field: value})})
    in_view = field in _ASSERTION_VIEW_READS["provenance"]
    assert (assertion_view(changed) != assertion_view(base)) is in_view
    assert in_view is (field not in ASSERTION_VIEW_KEEPS["provenance"])


@pytest.mark.parametrize("reason, moves", [("disputed", True), ("corrected", True), ("superseded", True),
                                           ("revoked_source", True), ("redacted", True), ("lapsed", False),
                                           ("decayed", False), ("absorbed_duplicate", False)])
def test_an_edge_retirement_moves_the_view_by_wiki_drops_on(reason, moves):
    e = _edge()
    assert (assertion_view(e.model_copy(update={"invalidated_at": _NOW, "invalidation_reason": reason}))
            != assertion_view(e)) is moves


@pytest.mark.parametrize("reason", ["revoked_source", "lapsed", "decayed"])
def test_any_episode_retirement_moves_the_view(reason):
    """Research's E1: every retired episode is out of the compile, whatever the reason (W3/W8 are edge rules)."""
    p = _ep()
    assert assertion_view(p.model_copy(update={"retired_at": _NOW, "retired_reason": reason})) != assertion_view(p)


def test_an_absent_record_has_no_view():
    assert assertion_view(None) is None and assertion_view(_edge()) is not None


# ---------------------------------------------------------------------------------------------------------------------
# 2. the writer inventory: writer × mutation class, with the generic oracle
# ---------------------------------------------------------------------------------------------------------------------

def _views(s):
    rows = [("edge", r[0]) for r in s._conn.execute("SELECT json FROM edges WHERE user_id=?", (U,))]
    rows += [("episode", r[0]) for r in s._conn.execute("SELECT json FROM episodes WHERE user_id=?", (U,))]
    out = {}
    for kind, blob in rows:
        rec = (Edge if kind == "edge" else Episode).model_validate_json(blob)
        out[(kind, rec.id)] = assertion_view(rec)
    return out


@pytest.fixture
def cached(tmp_path):
    """A real store holding one edge and one episode, and a published wiki row over them."""
    s = SqliteStore(str(tmp_path / "w.db"))
    s.add_edge(_edge())
    s.add_episode(_ep())

    def publish():
        assert s.set_wiki(U, "cached body", s.store_version(U)) and s.get_wiki(U) is not None
    publish()
    s.publish = publish
    yield s
    s.close()


def _run(s, mutate, expect, setup=None):
    """One cell: after `setup` (republishing the wiki over it), apply `mutate` to a store with a cached wiki and assert
    `expect` ("EVICT", "KEEP" or an exception class, which must also KEEP) — and the generic oracle, which knows
    nothing of the cell: a write that moves a pre-existing record's view never leaves the wiki (a write may evict
    for a cause of its own, a reply's or an erasure's, without moving a view)."""
    if setup is not None:
        setup(s)
        s.publish()
    before = _views(s)
    if isinstance(expect, type):
        with pytest.raises(expect):
            mutate(s)
        expect = "KEEP"
    else:
        mutate(s)
    after = _views(s)
    moved = sorted(k for k in before if after.get(k) != before[k])
    kept = s.get_wiki(U) is not None
    assert not (moved and kept), f"oracle: views moved {moved}, wiki kept"
    assert kept is (expect == "KEEP"), f"expected {expect}, wiki kept={kept}"


def _same_id_edge(**upd):
    return lambda s: s.add_edge(_edge().model_copy(update=upd))


def _same_id_edge_prov(**upd):
    e = _edge()
    return lambda s: s.add_edge(e.model_copy(update={"provenance": e.provenance.model_copy(update=upd)}))


def _same_id_ep(**upd):
    return lambda s: s.add_episode(_ep().model_copy(update=upd))


def _same_id_ep_prov(**upd):
    p = _ep()
    return lambda s: s.add_episode(p.model_copy(update={"provenance": p.provenance.model_copy(update=upd)}))


def _challenge(s):
    """Setup: a challenged record beside the drawn one (the challenge evicts on its own write; _run republishes)."""
    s.add_edge(_edge("e-challenged", "Toronto"))
    s.add_reply(U, "e-challenged", kind="challenge", text="Please withhold this.", target=None,
                actor="user", correlation_id="c-r2-01")


def _retarget(s):
    """The challenged record's twin key moves under the same ID (the reviewer's first witness)."""
    s.add_edge(_edge("e-challenged", "Lisbon"))


def _consolidate(s, finish):
    op = s.create_or_takeover_consolidation(U, ["p-1"], "w1", 60)
    if finish == "claim":
        return
    from veracium.schema import ConsolidationOutputDraft
    assert s.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "generating")
    assert s.write_consolidation_output_if_current(op.operation_id, op.fence, "w1", ConsolidationOutputDraft(
        summary="The user moved to Lisbon.", date_start="2026-01-02", date_end="2026-01-02"))
    if finish == "abandon":
        assert s.abandon_consolidation_if_current(op.operation_id, op.fence) in (True, False)
        return
    assert s.transition_consolidation_if_current(op.operation_id, op.fence, "w1", "outputs_durable")
    if finish == "cutover":
        return
    assert s.delete_claimed_inputs_if_current(op.operation_id, op.fence)


def _flag(s):
    s.add_edge(_edge().model_copy(update={"needs_confirmation": True}))


def _confirm(s):
    s.confirm_edge(U, "e-loc", actor="user", call_path="host_api", correlation_id="k-r2-01", request_digest="d-1",
                   confirmed_at=_NOW)


CELLS = {
    # add_edge — a fresh id is W3's staleness; a same-ID replace is judged by the view
    "edge-fresh-id": (lambda s: s.add_edge(_edge("e-new", "Porto")), "KEEP"),
    **{f"edge-same-id-{f}": (_same_id_edge(**{f: v}), "EVICT")
       for f, v in (("subject", "boss"), ("relation", "works_at"), ("object", "Porto"),
                    ("valid_from", T0 - timedelta(days=9)))},
    **{f"edge-same-id-{f}": (_same_id_edge_prov(**{f.split("-")[0]: v}), "EVICT")
       for f, v in (("disclosure-quarantined", Disclosure.QUARANTINED), ("disclosure-use_only", Disclosure.USE_ONLY),
                    ("author_of_evidence", EvidenceAuthor.THIRD_PARTY),
                    ("derived_from", EvidenceAuthor.THIRD_PARTY))},
    "edge-same-id-ungrounded": (_same_id_edge(ungrounded=True), ValueError),        # refused both ways (0019 U4)
    "edge-same-id-user_id": (_same_id_edge(user_id="v"), ValueError),               # the owner, 0008 §6d
    **{f"edge-same-id-keep-{f}": (_same_id_edge(**{f: v}), "KEEP")
       for f, v in (("note", "a note"), ("volatility", Volatility.TRANSIENT), ("needs_confirmation", True),
                    ("times_used", 4), ("outcome_counts", {"confirmed": 2}), ("last_outcome", Outcome.CONFIRMED),
                    ("last_outcome_at", _NOW), ("original_relation", "lives_in"))},
    **{f"edge-same-id-keep-{f}": (_same_id_edge_prov(**{f: v}), "KEEP")
       for f, v in (("confidence", 0.31), ("evidence_ref", "ev-2"), ("observed_at", _NOW),
                    ("source_id", "src-9"))},
    **{f"edge-same-id-retire-{r}": (_same_id_edge(invalidated_at=_NOW, invalidation_reason=r),
                                    "EVICT" if r in ("disputed", "corrected", "superseded", "revoked_source")
                                    else "KEEP")
       for r in ("disputed", "corrected", "superseded", "revoked_source", "lapsed", "decayed",
                 "absorbed_duplicate")},
    "edge-challenged-twin-key-change": (_retarget, "EVICT", _challenge),
    # invalidate_edge — through the sole active=0 writer, W1/W3
    **{f"invalidate-{r}": ((lambda r: lambda s: s.invalidate_edge("e-loc", _NOW, r))(r),
                           "EVICT" if r in ("disputed", "corrected") else "KEEP")
       for r in ("disputed", "corrected", "lapsed", "decayed")},
    # confirm_edge — needs_confirmation is outside wiki admission today (research's N1)
    "confirm-edge": (_confirm, "KEEP", _flag),
    # add_episode — the same rule for episodes (research's S2)
    "episode-fresh-id": (lambda s: s.add_episode(_ep("p-new", "The user visited Porto.")), "KEEP"),
    **{f"episode-same-id-{f}": (_same_id_ep(**{f: v}), "EVICT")
       for f, v in (("summary", "The user moved to Porto."), ("date", "2026-02-02"))},
    "episode-same-id-retired": (_same_id_ep(retired_reason="revoked_source", retired_at=_NOW), "EVICT"),
    **{f"episode-same-id-{f}": (_same_id_ep_prov(**{f.split('-')[0]: v}), "EVICT")
       for f, v in (("disclosure-quarantined", Disclosure.QUARANTINED), ("disclosure-use_only", Disclosure.USE_ONLY),
                    ("author_of_evidence", EvidenceAuthor.THIRD_PARTY))},
    **{f"episode-same-id-keep-{f}": (_same_id_ep(**{f: v}), "KEEP")
       for f, v in (("context_ref", "rubric-1"),)},
    "episode-same-id-keep-confidence": (_same_id_ep_prov(confidence=0.31), "KEEP"),
    # the owner (R-II round 3): refused against the PERSISTED row; before, the per-user oracle saw U's episode vanish
    "episode-same-id-user_id": (_same_id_ep(user_id="v"), ValueError),
    "delete-episode": (lambda s: s.delete_episode("p-1"), "EVICT"),
    # the consolidation primitives: a claim keeps (metadata), the inputs' deletion after the cutover evicts
    "consolidation-claim": (lambda s: _consolidate(s, "claim"), "KEEP"),
    "consolidation-abandon": (lambda s: _consolidate(s, "abandon"), "KEEP"),
    "consolidation-complete": (lambda s: _consolidate(s, "complete"), "EVICT"),
    # the cutover writes no episodes row, yet hides the inputs and reveals the outputs (0010 X9): it evicts itself
    # (research's stage-1 addendum (c)), before the inputs' deletion, which recovery may delay
    "consolidation-cutover": (lambda s: _consolidate(s, "cutover"), "EVICT"),
    # the rest of the writers that touch edges or episodes
    "forget-user": (lambda s: s.forget_user(U), "EVICT"),
    "redact-edge": (lambda s: s.redact(U, edge_id="e-loc", reason="subject_request"), "EVICT"),
    "reply-challenge": (lambda s: s.add_reply(U, "e-loc", kind="challenge", text="No.", target=None, actor="user",
                                              correlation_id="c-2"), "EVICT"),
}

@pytest.mark.parametrize("cell", sorted(CELLS))
def test_every_mutation_class_evicts_iff_it_moves_a_view(cached, cell):
    _run(cached, *CELLS[cell])


def test_the_eviction_cells_cover_every_view_field():
    """Each field the view reads has a same-ID EVICT cell for an edge (the view's complement is part 1's keeps)."""
    covered = {k.removeprefix("edge-same-id-").split("-")[0] for k in CELLS if k.startswith("edge-same-id-")
               and CELLS[k][1] in ("EVICT", ValueError) and "-keep-" not in k and "-retire-" not in k}
    view = (_ASSERTION_VIEW_READS["edge"] - {"provenance"}) | _ASSERTION_VIEW_READS["provenance"]
    unreachable = {"record_kind", "basis"}   # the procedural stamp: test below — a same-ID write cannot move it
    assert view - unreachable <= covered, sorted(view - unreachable - covered)


def _premises():
    """The KEEPs whose reason is a write-path PREMISE ("immutable …"), read from the table, never listed by hand."""
    return sorted((kind, f) for kind, reasons in ASSERTION_VIEW_KEEPS.items() for f, r in reasons.items()
                  if r.startswith("immutable"))


def test_every_write_path_premise_names_its_guard_and_has_a_refusal_cell():
    """0004 v3.5 W11: the partition proves a field is placed, not that its reason is true (R-II round 3: `Episode.user_id`
    said immutable and no write made it so). Each premise names its Store protocol obligation and has a same-ID cell
    that must be REFUSED."""
    assert _premises(), "no premise found: the census reads nothing"
    for kind, field in _premises():
        assert "obligation" in ASSERTION_VIEW_KEEPS[kind][field], (kind, field)
        assert CELLS.get(f"{kind}-same-id-{field}", (None, None))[1] is ValueError, (kind, field)


@pytest.mark.parametrize("kind, field", _premises())
def test_a_premise_holds_at_the_store_write(cached, kind, field):
    """The premise's guard at the durable write: the same-ID write that breaks it is refused, the stored row and the
    version are unchanged, and nothing lands under the value it named."""
    table = {"edge": (EDGE_MUTATIONS, _edge, "edges", cached.add_edge),
             "episode": (EPISODE_MUTATIONS, _ep, "episodes", cached.add_episode)}[kind]
    mutations, make, sql_table, write = table
    rec = make()
    row = lambda: cached._conn.execute(f"SELECT user_id, json FROM {sql_table} WHERE id=?", (rec.id,)).fetchone()
    before, version = row(), cached.store_version(U)
    with pytest.raises(ValueError):
        write(rec.model_copy(update={field: mutations[field]}))
    assert row() == before and cached.store_version(U) == version and cached.get_wiki(U) is not None


@pytest.mark.parametrize("upd", [{"record_kind": "procedural", "basis": "stated"}])
def test_the_procedural_stamp_cannot_move_under_a_same_id_write(cached, upd):
    """record_kind and basis are in the view; a same-ID write that sets them on an ordinary record is refused or
    moves the view and evicts — either way never a kept wiki over a moved view (the oracle)."""
    e = _edge()
    before = _views(cached)
    try:
        cached.add_edge(e.model_copy(update={"provenance": e.provenance.model_copy(update=upd)}))
    except ValueError:
        assert _views(cached) == before and cached.get_wiki(U) is not None
        return
    assert cached.get_wiki(U) is None


# every public method of SqliteStore, classed: a READ (it writes no edge or episode row, nor the wiki), or a WRITER
# naming its cells here or the test that pins it. A new public method fails here until it is classed.
READ = "read"
WRITERS = {
    "add_edge": [k for k in CELLS if k.startswith("edge-")],
    # specs/0048 §4D: expiry's per-edge transition writes through _invalidate_edge_row / _upsert_edge_row (each
    # evicting by the view rule) and drops the wiki on a retirement that ends a refusal contention, as invalidate_edge
    "expiry_transition": ["tests/test_0048_decay_bounds.py::test_a_transitions_side_effects_equal_the_shipped_paths",
                          "tests/test_0048_decay_bounds.py::test_decay_keeps_the_shipped_result"],
    "add_episode": [k for k in CELLS if k.startswith("episode-")],
    "invalidate_edge": [k for k in CELLS if k.startswith("invalidate-")],
    "confirm_edge": ["confirm-edge"],
    "delete_episode": ["delete-episode"],
    "create_or_takeover_consolidation": ["consolidation-claim"],
    "transition_consolidation_if_current": ["consolidation-cutover", "consolidation-complete"],
    "write_consolidation_output_if_current": ["consolidation-complete"],
    "delete_claimed_inputs_if_current": ["consolidation-complete"],
    "abandon_consolidation_if_current": ["consolidation-abandon"],
    "forget_user": ["forget-user"],
    "redact": ["redact-edge"],
    "add_reply": ["reply-challenge", "edge-challenged-twin-key-change"],
    "apply_supersession_plan": ["tests/test_0004_wiki_revocation.py::test_third_party_supersession_drops_the_wiki",
                                "tests/test_0004_wiki_revocation.py::test_absorption_does_not_drop_the_wiki",
                                "test_supersession_and_absorption_through_the_plan"],
    "commit_outcome_import_plan": ["tests/test_0047_rii01_wiki_bind.py (every import evicts, RII-01)",
                                   "its edges pass _journal_edge_write"],
    "undo_restoration": ["its edges pass _journal_edge_write (test_every_edges_writer_passes_the_journal)"],
    "append_outcome_if_head": ["test_an_outcome_append_keeps_the_wiki"],
    "set_wiki": ["the wiki's publish (specs/0041 §4e)"],
    "discard_wiki": ["test_d2_a_rejected_compile_is_not_served_back_from_its_own_row",
                     "test_the_discard_never_drops_a_newer_row"],
    "upsert_embedding": ["writes edge_embedding only"],
    "write_policy_receipt": ["writes policy receipts only"],
    "renew_consolidation_lease": ["a lease's expiry only"],
}
READS = {
    "act_rows", "act_state", "acted_edge_ids", "active_challenges", "arity_plan_state", "challenge_snapshot",
    "confirm_notice", "confirmations_for", "contributions", "contributions_naming", "contributors_of_source",
    "current_state", "edge_events", "edge_state_at", "edges", "edges_superseding", "embedding_keys", "episodes",
    "get_wiki", "list_users", "local_origin", "migration_outcomes", "migration_outcomes_by_uid", "notice_body",
    "notice_id", "pending_consolidations", "pending_notices", "policy_receipt", "policy_receipts",
    "quiescent_episode_snapshot", "read_window", "redacted_targets", "redaction_records", "refusal_inventory_ids",
    "refusals", "replies_for", "semantic_candidates", "standing_revocations", "store_version", "supersession_receipt",
    "supersessions_refused", "validate_receipt_state", "close", "atomic", "epoch_txn",
}


def test_every_public_store_method_is_classed():
    public = {n for n, _ in inspect.getmembers(SqliteStore, callable) if not n.startswith("_")}
    assert public == set(WRITERS) | READS, (sorted(public - set(WRITERS) - READS),
                                             sorted((set(WRITERS) | READS) - public))
    assert not set(WRITERS) & READS
    for name, cells in WRITERS.items():
        assert cells, name
        for c in cells:
            assert c in CELLS or not c.startswith(("edge-", "episode-", "invalidate-", "consolidation-")), (name, c)


def test_confirm_notice_is_a_read_in_name_only_or_writes_no_record():
    """confirm_notice is classed READ above for the wiki: it writes 0041 notice state, never an edge, an episode or
    the wiki row (its SQL, read here, names none of the three)."""
    src = inspect.getsource(SqliteStore.confirm_notice)
    for table in ("INTO edges", "UPDATE edges", "INTO episodes", "UPDATE episodes", "FROM wiki", "INTO wiki"):
        assert table not in src, table


def test_supersession_and_absorption_through_the_plan(tmp_path):
    """apply_supersession_plan's two uses of _upsert_edge_row: a supersession evicts (W2), an absorption keeps (W8)
    — both by the same choke-point rule, the generic oracle beside each."""
    from veracium.graph import _build_supersession_plan, apply_supersession
    from veracium.schema import DEFAULT_RELATIONS
    s = SqliteStore(str(tmp_path / "p.db"))
    try:
        apply_supersession(s, _edge("e-a", "Lisbon"), DEFAULT_RELATIONS)
        s.publish = lambda: s.set_wiki(U, "cached", s.store_version(U))
        s.publish()

        def supersede(st):
            plan, _ = _build_supersession_plan(st, _edge("e-b", "Porto"), DEFAULT_RELATIONS, "sup-e-b")
            assert any(r == "superseded" for _, _, r in plan.prior_invalidations)
            st.apply_supersession_plan(plan)
        _run(s, supersede, "EVICT")
    finally:
        s.close()


def test_an_outcome_append_keeps_the_wiki(tmp_path):
    """record_outcome's writes (the counters on the edge, a fresh outcome episode) keep the wiki: W3's staleness
    counter, never an eviction (research's S1 KEEP control)."""
    cfg = MemoryConfig(db_path=str(tmp_path / "o.db"), require_source_id=False, scope_groups={})
    m = Memory(llm=lambda p, **k: "User lives in Lisbon.", config=cfg)
    try:
        m.store.add_edge(_edge())
        m.store.set_wiki(U, "cached", m.store.store_version(U))
        before = _views(m.store)
        m.record_outcome(U, "e-loc", outcome=Outcome.CONFIRMED, evidence_ref="ev-outcome", actor="user")
        after = _views(m.store)
        assert all(after.get(k) == v for k, v in before.items())
        assert m.store.get_wiki(U) is not None
    finally:
        m.close()


def test_every_edges_writer_passes_the_journal():
    """W7 restated (RII-R2-01; research's S4): the wiki's edge eviction sits in _journal_edge_write, so its reach is
    the journal's — every SQL statement in store/sqlite.py that writes `edges` sits in a function that calls
    _journal_edge_write (or IS it). The 0029 choke point and the wiki's eviction are one call."""
    tree = ast.parse((ROOT / "src" / "veracium" / "store" / "sqlite.py").read_text())
    bad = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef):
            continue
        sqls = [c.args[0].value for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and c.func.attr == "execute" and c.args and isinstance(c.args[0], ast.Constant)
                and isinstance(c.args[0].value, str)]
        sqls += ["".join(p.value for p in c.args[0].values if isinstance(p, ast.Constant))
                 for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                 and c.func.attr == "execute" and c.args and isinstance(c.args[0], ast.JoinedStr)]
        writes = [q for q in sqls if _writes_table(q, "edges")]
        calls = {c.func.attr for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
        if writes and "_journal_edge_write" not in calls and fn.name not in EDGES_WRITERS_EXEMPT:
            bad.append((fn.name, writes))
    assert not bad, bad


def test_every_episodes_writer_calls_the_eviction():
    """Research's E4: episodes have no journal, so the helper is called at each site; every function whose SQL
    replaces, updates or deletes an `episodes` row calls _evict_wiki_on_view_change (a plain INSERT of a fresh id
    cannot replace a record, and is W3's staleness)."""
    tree = ast.parse((ROOT / "src" / "veracium" / "store" / "sqlite.py").read_text())
    bad = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef):
            continue
        sqls = [c.args[0].value for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and c.func.attr == "execute" and c.args and isinstance(c.args[0], ast.Constant)
                and isinstance(c.args[0].value, str)]
        replacing = [q for q in sqls if _writes_table(q, "episodes")
                     and not re.match(r"\s*INSERT\s+INTO", q, re.I)]
        calls = {c.func.attr for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
        if replacing and "_evict_wiki_on_view_change" not in calls and fn.name not in EPISODES_WRITERS_EXEMPT:
            bad.append((fn.name, replacing))
    assert not bad, bad


def _writes_table(sql: str, table: str) -> bool:
    """Whether a statement's verb writes `table`: matched at the statement's start, case-insensitively, the SQL text
    itself left untouched."""
    return re.match(rf"\s*(INSERT(\s+OR\s+REPLACE)?\s+INTO|UPDATE|DELETE\s+FROM)\s+{table}\b", sql, re.I) is not None


# the writers the two sweeps above exempt, each with why
EDGES_WRITERS_EXEMPT = {
    "forget_user": "erasure: deletes every row of the user and the wiki with them (an evicting writer)",
}
EPISODES_WRITERS_EXEMPT = {
    "forget_user": "erasure: deletes every row of the user and the wiki with them",
    "_redact_in_txn": "redaction: evicts the wiki unconditionally in its own transaction",
}


@pytest.mark.parametrize("sql, table, writes", [
    ("INSERT OR REPLACE INTO episodes(id) VALUES(?)", "episodes", True),
    ("UPDATE edges SET json=? WHERE id=?", "edges", True), ("DELETE FROM episodes WHERE id=?", "episodes", True),
    ("SELECT json FROM episodes", "episodes", False), ("DELETE FROM wiki WHERE user_id=?", "episodes", False),
    ("INSERT INTO episodes_archive(id) VALUES(?)", "episodes", False), ("  update  EPISODES set json=?", "episodes", True),
])
def test_the_sweeps_table_recogniser(sql, table, writes):
    assert _writes_table(sql, table) is writes


# ---------------------------------------------------------------------------------------------------------------------
# 3. the recall-level regressions: sequential and interleaved, cached and compiled
# ---------------------------------------------------------------------------------------------------------------------

LINE = "User lives in Lisbon."


def _provider(prompt, *, role="compile", **kwargs):
    return LINE if role == "compile" and "Lisbon" in prompt else "No current location."


def _pair(tmp_path):
    cfg = MemoryConfig(db_path=str(tmp_path / "m.db"), require_source_id=False, scope_groups={})
    assert cfg.wiki_recompile_after_writes == 8          # the default threshold, as the reviewer ran it
    return Memory(llm=_provider, config=cfg), Memory(llm=_provider, config=cfg)


def _arm(reader, monkeypatch, timing, write, done):
    """Run `write` before the recall (sequential) or inside bound_wiki just before its snapshot (interleaved), or
    just after it (the coherent-older-snapshot control)."""
    if timing == "before_recall":
        write()
    real = reader.store.challenge_snapshot

    def snapshot(uid):
        bind = sys._getframe(1).f_code.co_name == "bound_wiki"
        if bind and timing == "before_snapshot" and not done:
            write()
        snap = real(uid)
        if bind and timing == "after_snapshot" and not done:
            write()
        return snap
    monkeypatch.setattr(reader.store, "challenge_snapshot", snapshot)


@pytest.mark.parametrize("timing", ["before_recall", "before_snapshot", "after_snapshot"])
@pytest.mark.parametrize("cached_body", [True, False], ids=["cached", "compiled"])
def test_reviewer_twin_a_challenged_record_moving_its_twin_key(tmp_path, monkeypatch, timing, cached_body):
    """0047 INV-R18 (the wiki never serves a fact challenged since its compile): the reviewer's first witness, without
    its row-survives precondition (the fix evicts the row by design)."""
    reader, writer = _pair(tmp_path)
    try:
        reader.store.add_edge(_edge("challenged", "Toronto"))
        reader.store.add_edge(_edge("candidate", "Lisbon"))
        reader.reply(U, "challenged", kind="challenge", text="Please withhold this.")
        if cached_body:
            first = reader.recall(U, "Lisbon", semantic=False)
            assert LINE in first.grounded and first.inspection["candidate"].challenge_clear
        done = []

        def write():
            writer.store.add_edge(_edge("challenged", "Lisbon"))
            done.append(True)
            assert not writer.store.challenge_snapshot(U).inspect(_edge("candidate", "Lisbon")).challenge_clear
        _arm(reader, monkeypatch, timing, write, done)
        r = reader.recall(U, "Lisbon", semantic=False)
        assert done
        ins = r.inspection["candidate"]
        if timing != "after_snapshot":
            assert not ins.challenge_clear
        assert ins.challenge_clear == (LINE in r.grounded), r.grounded
    finally:
        reader.close(); writer.close()


def _replacement(kind):
    e = _edge()
    if kind == "retire":
        return e.model_copy(update={"invalidated_at": datetime.now(timezone.utc), "invalidation_reason": "disputed"})
    if kind in ("quarantine", "use_only"):
        d = Disclosure.QUARANTINED if kind == "quarantine" else Disclosure.USE_ONLY
        return e.model_copy(update={"provenance": e.provenance.model_copy(update={"disclosure": d})})
    if kind == "content":
        return e.model_copy(update={"object": "Porto"})
    raise AssertionError(kind)


@pytest.mark.parametrize("kind", ["retire", "quarantine", "use_only", "content"])
@pytest.mark.parametrize("timing", ["before_recall", "before_snapshot"])
@pytest.mark.parametrize("cached_body", [True, False], ids=["cached", "compiled"])
def test_a_same_id_replacement_of_a_drawn_edge(tmp_path, monkeypatch, timing, cached_body, kind):
    """The reviewer's retirement witness (kind=retire) and research's stage-1 families: a drawn edge demoted to
    quarantined or use_only, or its value replaced, under the same ID — no wiki body asserts the drawn value."""
    reader, writer = _pair(tmp_path)
    try:
        reader.store.add_edge(_edge())
        if cached_body:
            assert LINE in reader.recall(U, "Lisbon", semantic=False).grounded
        done = []

        def write():
            writer.store.add_edge(_replacement(kind))
            done.append(True)
        _arm(reader, monkeypatch, timing, write, done)
        r = reader.recall(U, "Lisbon", semantic=False)
        assert done
        assert LINE not in r.grounded, r.grounded
    finally:
        reader.close(); writer.close()


@pytest.mark.parametrize("cached_body", [True, False], ids=["cached", "compiled"])
def test_the_drawn_edge_becoming_a_twin_of_a_challenged_record(tmp_path, monkeypatch, cached_body):
    """0047 INV-R18, research's S2: the DRAWN record is replaced into a twin of a challenged one between the compile and
    the bind's snapshot; the reviewer's oracle — the candidate's inspection is clear iff the body is served."""
    reader, writer = _pair(tmp_path)
    try:
        reader.store.add_edge(_edge("challenged", "Toronto"))
        reader.store.add_edge(_edge("candidate", "Lisbon"))
        reader.reply(U, "challenged", kind="challenge", text="Please withhold this.")
        if cached_body:
            assert LINE in reader.recall(U, "Lisbon", semantic=False).grounded
        done = []

        def write():
            writer.store.add_edge(_edge("candidate", "Toronto"))
            done.append(True)
        _arm(reader, monkeypatch, "before_snapshot", write, done)
        r = reader.recall(U, "Lisbon", semantic=False)
        assert done
        ins = r.inspection.get("candidate")
        assert ins is not None and not ins.challenge_clear
        assert ins.challenge_clear == (LINE in r.grounded), r.grounded
    finally:
        reader.close(); writer.close()


@pytest.mark.parametrize("timing", ["before_recall", "before_snapshot"])
@pytest.mark.parametrize("cached_body", [True, False], ids=["cached", "compiled"])
def test_an_episode_demoted_under_its_id(tmp_path, monkeypatch, cached_body, timing):
    """Research's S2 for episodes: a same-ID add_episode demoting a drawn episode to QUARANTINED."""
    line = "User moved to Lisbon."
    cfg = MemoryConfig(db_path=str(tmp_path / "m.db"), require_source_id=False, scope_groups={})
    prov = (lambda p, *, role="compile", **k: line if role == "compile" and "Lisbon" in p else "Nothing recorded.")
    reader, writer = Memory(llm=prov, config=cfg), Memory(llm=prov, config=cfg)
    try:
        p = _ep()
        reader.store.add_episode(p)
        if cached_body:
            assert line in reader.recall(U, "Lisbon", semantic=False).grounded
        done = []

        def write():
            writer.store.add_episode(p.model_copy(update={"provenance": p.provenance.model_copy(
                update={"disclosure": Disclosure.QUARANTINED})}))
            done.append(True)
        _arm(reader, monkeypatch, timing, write, done)
        r = reader.recall(U, "Lisbon", semantic=False)
        assert done and not [e for e in writer.store.episodes(U) if e.assertable]
        assert line not in r.grounded, r.grounded
    finally:
        reader.close(); writer.close()


@pytest.mark.parametrize("keep", ["counters", "confidence", "note", "needs_confirmation"])
def test_a_retaining_same_id_write_keeps_the_cached_body(tmp_path, keep):
    """Research's S1 KEEP controls at the recall level: a same-ID write outside the view leaves the cached row and the
    served body exactly as they were (W3: the staleness counter refreshes it, not an eviction)."""
    reader, writer = _pair(tmp_path)
    try:
        e = _edge()
        reader.store.add_edge(e)
        assert LINE in reader.recall(U, "Lisbon", semantic=False).grounded
        row = reader.store.get_wiki(U)
        upd = {"counters": {"times_used": 3, "outcome_counts": {"confirmed": 1}, "last_outcome": Outcome.CONFIRMED,
                            "last_outcome_at": _NOW},
               "confidence": {"provenance": e.provenance.model_copy(update={"confidence": 0.4})},
               "note": {"note": "since the spring"},
               "needs_confirmation": {"needs_confirmation": True}}[keep]
        writer.store.add_edge(e.model_copy(update=upd))
        assert writer.store.get_wiki(U) == row
        assert LINE in reader.recall(U, "Lisbon", semantic=False).grounded
    finally:
        reader.close(); writer.close()


# ---------------------------------------------------------------------------------------------------------------------
# 4. D2: a rejected compiled body is not served back from its own cache row (defence in depth)
# ---------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("d2", [True, False], ids=["with-d2", "without-d2"])
def test_d2_a_rejected_compile_is_not_served_back_from_its_own_row(tmp_path, monkeypatch, d2):
    """0047 INV-R18 ("let the rejected compiled body re-enter through the cache on the retry", its v1.17 mutant) and
    0004 W13; research's S3: with D1 complete, every rejection cause evicts at its write, so D2 is unreachable through the
    public writers. This cell disables D1's eviction at its site, then lands a same-ID retirement between the compile
    and the bind's snapshot: the compiled body fails its bind; without D2 the retry is served that body from the
    row the rejected compile published (red), with D2 that row is discarded and the retry recompiles (green)."""
    reader, writer = _pair(tmp_path)
    try:
        for st in (reader.store, writer.store):
            monkeypatch.setattr(st, "_evict_wiki_on_view_change", lambda *a, **k: None)
        if not d2:
            monkeypatch.setattr(reader.store, "discard_wiki", lambda *a, **k: False)
        reader.store.add_edge(_edge())
        done = []

        def write():
            writer.store.add_edge(_replacement("retire"))
            done.append(True)
        _arm(reader, monkeypatch, "before_snapshot", write, done)
        r = reader.recall(U, "Lisbon", semantic=False)
        assert done
        served = LINE in r.grounded
        assert served is (not d2), r.grounded
    finally:
        reader.close(); writer.close()


def test_the_discard_never_drops_a_newer_row(tmp_path):
    """W13's conditional (research's stage-1 addendum (b)): discard_wiki deletes only the row it names. A row published
    after the one a withheld compile published survives the discard; the named row itself is deleted."""
    s = SqliteStore(str(tmp_path / "d.db"))
    try:
        s.add_edge(_edge())
        v1 = s.store_version(U)
        assert s.set_wiki(U, "the withheld body", v1)
        s.add_edge(_edge("e-new", "Porto"))
        v2 = s.store_version(U)
        assert s.set_wiki(U, "a newer body", v2)
        assert s.discard_wiki(U, "the withheld body", v1) is False
        assert s.get_wiki(U) == ("a newer body", v2)
        assert s.discard_wiki(U, "a newer body", v2) is True and s.get_wiki(U) is None
    finally:
        s.close()


def test_a_redaction_in_both_windows_ends_as_the_redacted_notice(tmp_path, monkeypatch):
    """0047 INV-R18's redaction window, and the bind's order (research's E2): a redaction changes the redacted record's
    view too, so a bind that compared
    views BEFORE its redaction clause would end a redaction as no wiki rather than 0041 round 10's redacted-during-
    compile notice. A redaction before each of the call's two bound snapshots — the drawn edge, then the drawn
    episode the retry still drew on — fails both attempts by the redaction clause: the call serves the redacted
    notice and asserts neither record. Mutant: the view comparison placed before the redaction check."""
    from veracium import budgets
    line = "User moved to Lisbon."
    cfg = MemoryConfig(db_path=str(tmp_path / "m.db"), require_source_id=False, scope_groups={})
    prov = (lambda p, *, role="compile", **k: line if role == "compile" and "Lisbon" in p else "Nothing recorded.")
    reader, writer = Memory(llm=prov, config=cfg), Memory(llm=prov, config=cfg)
    try:
        reader.store.add_edge(_edge())
        reader.store.add_episode(_ep())
        targets = [{"edge_id": "e-loc"}, {"episode_id": "p-1"}]
        real = reader.store.challenge_snapshot

        def snapshot(uid):
            if sys._getframe(1).f_code.co_name == "bound_wiki" and targets:
                writer.redact(U, reason="subject_request", **targets.pop(0))
            return real(uid)
        monkeypatch.setattr(reader.store, "challenge_snapshot", snapshot)
        r = reader.recall(U, "Lisbon", semantic=False)
        assert not targets
        assert budgets.REDACTED_DURING_COMPILE_NOTICE in r.grounded, r.grounded
        assert line not in r.grounded
    finally:
        reader.close(); writer.close()


@pytest.mark.parametrize("role", ["twin", "own", "unrelated"])
def test_the_snapshot_reads_only_view_fields(tmp_path, role):
    """The bind's cross-module premise (CLAUDE.md item 4): compile._unbound_by asks the call's snapshot about the DRAWN
    object only, once the current row's view equals the drawn one — sound only if the snapshot's twin match reads
    nothing outside the view. For a drawn record that twins a challenged one, IS the challenged one, or is unrelated,
    every KEEP field changed alone leaves `withheld` and the inspection's `challenge_clear` exactly as they were.
    (`id` is excluded: the bind looks the current row up by the drawn id, so the two never differ in it.)"""
    s = SqliteStore(str(tmp_path / "s.db"))
    try:
        s.add_edge(_edge("e-challenged", "Toronto"))
        s.add_reply(U, "e-challenged", kind="challenge", text="Please withhold this.", target=None, actor="user",
                    correlation_id="c-pin")
        snap = s.challenge_snapshot(U)
        drawn = {"twin": _edge("e-drawn", "Toronto"), "own": _edge("e-challenged", "Toronto"),
                 "unrelated": _edge("e-drawn", "Lisbon")}[role]
        expect = snap.withheld(drawn)
        assert expect is (role != "unrelated")                   # the fixture exercises both answers
        changed = [drawn.model_copy(update={f: v}) for f, v in EDGE_MUTATIONS.items()
                   if f in ASSERTION_VIEW_KEEPS["edge"] and f != "id"]
        changed += [drawn.model_copy(update={"provenance": drawn.provenance.model_copy(update={f: v})})
                    for f, v in PROVENANCE_MUTATIONS.items() if f in ASSERTION_VIEW_KEEPS["provenance"]]
        assert len(changed) == len(ASSERTION_VIEW_KEEPS["edge"]) - 1 + len(ASSERTION_VIEW_KEEPS["provenance"])
        for c in changed:
            assert assertion_view(c) == assertion_view(drawn)
            assert snap.withheld(c) is expect, c
            assert snap.inspect(c).challenge_clear is (not expect), c
    finally:
        s.close()


def test_an_out_of_range_replacement_is_refused_before_any_write_and_the_wiki_stays(cached):
    """INVERTED by specs/0048 §4C (the round-2 verdict: "replace or invert the baseline reproduction tests that
    intentionally assert today's defects"). Before 0048 this cell pinned that the eviction never changed what a writer
    may store: a replacement row the model cannot read back (an out-of-range confidence, built through an unvalidated
    copy) was WRITTEN, and the wiki dropped because the row's view was unknown. 0048's validating serialiser now
    refuses that row before any SQL runs, so nothing is written and the cached wiki stays: the eviction still adds no
    rule of its own about what may be stored; 0048 is the rule."""
    e = _edge()
    bad = e.model_copy(update={"provenance": e.provenance.model_copy(update={"confidence": 1.8})})
    before = cached._conn.execute("SELECT json FROM edges WHERE id=?", ("e-loc",)).fetchone()
    with pytest.raises(ValueError):
        cached.add_edge(bad)
    after = cached._conn.execute("SELECT json FROM edges WHERE id=?", ("e-loc",)).fetchone()
    assert after == before, "an out-of-range replacement reached the table"
    assert cached.get_wiki(U) is not None, "a refused write evicted the wiki"
