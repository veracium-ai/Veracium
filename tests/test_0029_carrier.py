"""specs/0029 — the transaction-time carrier: the fourteen §6 invariants as
executable checks, each under the test NAME the spec's §6 table binds it to.

RULE ZERO (the seam model's, kept here): every assertion ships with a negative
control that makes it fail, in this file, and the controls are themselves
asserted — a control that stops discriminating is a test failure, not a
silent green.

Written test-first from the accepted spec (2026-09-05, Quentin's ruling
"start on 0029 and 0030"); the implementation lands behind these.
"""
from __future__ import annotations

import json
import pathlib
import re
import sqlite3
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from veracium import EvidenceAuthor, SqliteStore
from veracium.schema import (DISPOSITIONED_REASONS, Edge, Provenance,
                             SupersessionPlan)
from veracium.store import schema_version as sv
from veracium.store.base import RawEdgeState, store_mutator  # noqa: F401
from veracium.store.migration import migrate_store

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
U = "u"


def _edge(obj="Porto", *, relation="located_at", eid=None, user=U):
    return Edge(id=eid or f"e-{uuid.uuid4().hex[:12]}", user_id=user, subject="user",
                relation=relation, object=obj,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}"))


@pytest.fixture()
def store(tmp_path):
    s = SqliteStore(str(tmp_path / "c.db"))
    yield s
    s.close()


def _events(store, user=U, **kw):
    return store.edge_events(user, **kw)


def _raw(store, edge_id):
    return store._conn.execute("SELECT json FROM edges WHERE id=?", (edge_id,)).fetchone()[0]


# --------------------------------------------------------------------------- #
# V-TOTAL — every site that writes `edges` carries an event ruling
# --------------------------------------------------------------------------- #

# The sweep scans BOTH literal forms and INTERPOLATED table names (v4 F-B: a
# literal-only sweep misses `f"UPDATE {t} ..."`; the benign extant instance is
# erasure's `f"DELETE FROM {table} WHERE user_id=?"`). An interpolated form is
# a site that must carry a ruling naming the tables its variable can take.
RAW_EDGE_WRITE = re.compile(
    r"(UPDATE\s+(?:edges|\{\w+\})|INSERT(?:\s+OR\s+REPLACE)?\s+INTO\s+(?:edges|\{\w+\})|DELETE\s+FROM\s+(?:edges|\{\w+\}))",
    re.I)


def test_every_edge_writing_site_carries_an_event_ruling(store):
    """V-TOTAL: the write-site set is DERIVED — every raw `UPDATE edges` /
    `INSERT ... INTO edges` in the store module plus every `@store_mutator`
    that reaches one — and every such site is inside the journaled write
    transaction and reaches the emission choke point. A new raw site without
    a ruling fails here. The behavioural half: one write of each kind through
    the public API yields exactly its §4b event."""
    src = (SRC / "store" / "sqlite.py").read_text()
    raw_sites = [m.start() for m in RAW_EDGE_WRITE.finditer(src)]
    assert len(raw_sites) >= 6, "the four raw UPDATE sites + the two inserts are the known population"
    from veracium.store.sqlite import EDGE_WRITE_SITE_RULINGS as rulings
    # COVERAGE is site-grain (spec §2: "the gate diffs event-writing sites
    # against every site that writes the edges table"): every raw site's
    # enclosing function carries a ruling. KIND is NOT in the ruling — kind is a
    # property of the WRITE (prior presence × serialization delta; v4 F-A: "no
    # site→kind mapping can be total"), decided by the choke point per write.
    for pos in raw_sites:
        # the enclosing METHOD (class-body indentation) or module function —
        # never a nested helper (`_recompute_edge_row` defines `_parse` inside
        # itself before its UPDATE; an any-`def` scan would attribute the write
        # to the helper and demand a ruling for a function that writes nothing)
        fn = max(src.rfind("\n    def ", 0, pos), src.rfind("\ndef ", 0, pos))
        name = re.match(r"\n\s*def\s+(\w+)", src[fn:]).group(1)
        assert name in rulings, f"raw edges write inside {name!r} has no §4b event ruling"
        assert "kind" not in rulings[name], f"ruling for {name!r} assigns a KIND per site (F-A)"
        if "{" in src[pos:pos + 40]:                       # an interpolated table name
            assert rulings[name].get("tables"), (
                f"{name!r} writes through an interpolated table name and its ruling "
                f"does not enumerate the tables the variable can take")
    # behaviour: each public write kind emits exactly its event
    e = _edge(); store.add_edge(e)
    kinds = [ev.kind for ev in _events(store, edge_id=e.id)]
    assert kinds == ["created"], kinds
    store.invalidate_edge(e.id, datetime.now(timezone.utc), "disputed")
    kinds = [ev.kind for ev in _events(store, edge_id=e.id)]
    assert kinds == ["created", "invalidated"], kinds
    # negative control: a same-bytes re-upsert is NOT an event (full-state basis)
    n = len(_events(store))
    store.add_edge(Edge.model_validate_json(_raw(store, e.id)))
    assert len(_events(store)) == n, "an unchanged serialization must not journal"


# --------------------------------------------------------------------------- #
# V-ATOMIC
# --------------------------------------------------------------------------- #

def test_event_and_mutation_are_one_transaction(store, monkeypatch):
    """V-ATOMIC: a fault injected between the mutation and its event leaves
    NEITHER persisted."""
    e = _edge(); store.add_edge(e)
    n_ev = len(_events(store)); before = _raw(store, e.id)

    real = store._journal_edge_write
    def boom(*a, **k):
        raise RuntimeError("injected between mutation and event")
    monkeypatch.setattr(store, "_journal_edge_write", boom)
    with pytest.raises(RuntimeError):
        store.invalidate_edge(e.id, datetime.now(timezone.utc), "disputed")
    monkeypatch.setattr(store, "_journal_edge_write", real)
    assert _raw(store, e.id) == before, "the mutation persisted without its event"
    assert len(_events(store)) == n_ev
    # negative control: without the fault both persist
    store.invalidate_edge(e.id, datetime.now(timezone.utc), "disputed")
    assert _raw(store, e.id) != before and len(_events(store)) == n_ev + 1


# --------------------------------------------------------------------------- #
# V-APPEND / V-MINT
# --------------------------------------------------------------------------- #

def test_event_log_is_append_only_and_monotone(store):
    """V-APPEND: no code path updates or deletes an event except erasure;
    `seq` strictly monotone per user."""
    src = (SRC / "store" / "sqlite.py").read_text()
    writes = [m.group(0) for m in re.finditer(r"(UPDATE|DELETE\s+FROM)\s+edge_event\b", src, re.I)]
    assert writes == ["DELETE FROM edge_event"], writes  # the ONE deleter is forget_user
    fn_of_delete = re.match(r"def\s+(\w+)", src[src.rfind("def ", 0, src.find("DELETE FROM edge_event")):]).group(1)
    assert fn_of_delete == "forget_user"
    for i in range(5):
        store.add_edge(_edge(f"o{i}"))
    seqs = [ev.seq for ev in _events(store)]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs) and seqs[0] >= 1
    # negative control: a duplicate seq is refused by the backstop PK
    with pytest.raises(sqlite3.IntegrityError):
        store._conn.execute("INSERT INTO edge_event(user_id,seq,txn,edge_id,kind,reason,state,recorded_at) "
                            "VALUES(?,?,?,?,?,?,?,?)", (U, seqs[0], 1, "x", "created", None, "{}", "2026-01-01T00:00:00Z"))


def test_recorded_at_is_store_minted_and_monotone(tmp_path):
    """V-MINT: no public surface accepts a transaction time; `recorded_at` is
    minted from the store clock once per batch; the monotone guard holds under
    a backwards clock step."""
    t = {"now": datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)}
    s = SqliteStore(str(tmp_path / "m.db"), clock=lambda: t["now"])
    try:
        import inspect
        for name in ("add_edge", "invalidate_edge", "apply_supersession_plan", "confirm_edge"):
            assert "recorded_at" not in inspect.signature(getattr(s, name)).parameters
        a = _edge("a"); s.add_edge(a)
        r1 = _events(s)[-1].recorded_at
        t["now"] -= timedelta(hours=1)                      # clock steps BACKWARDS
        s.add_edge(_edge("b"))
        r2 = _events(s)[-1].recorded_at
        assert r2 >= r1, "recorded_at went backwards with the clock"
        # negative control: with a forward clock the mint advances
        t["now"] += timedelta(hours=3); s.add_edge(_edge("c"))
        assert _events(s)[-1].recorded_at > r2
    finally:
        s.close()


# --------------------------------------------------------------------------- #
# V-RECON / V-VERBATIM
# --------------------------------------------------------------------------- #

def test_edge_state_at_reconstructs_byte_exact(store):
    """V-RECON: `edge_state_at(user, edge, K)` returns byte-exactly the
    serialization the edge held after the last txn ≤ K — across the
    recompute-erasure and reinstate-erasure cases (the row forgets; the
    journal must not)."""
    e = _edge(); store.add_edge(e)
    s0 = _raw(store, e.id); k0 = _events(store, edge_id=e.id)[-1].txn
    store.invalidate_edge(e.id, datetime(2026, 9, 1, tzinfo=timezone.utc), "lapsed")
    s1 = _raw(store, e.id); k1 = _events(store, edge_id=e.id)[-1].txn
    with store._write_txn():                                 # the row FORGETS the reason
        store._reinstate_edge_row(e.id)
    assert store.edge_state_at(U, e.id, k0).state == s0
    assert store.edge_state_at(U, e.id, k1).state == s1
    assert json.loads(store.edge_state_at(U, e.id, k1).state)["invalidation_reason"] == "lapsed"
    # negative control: the ROW no longer carries what the journal does
    assert json.loads(_raw(store, e.id))["invalidation_reason"] is None
    # a cutoff before the first event → None, not a fabricated state
    assert store.edge_state_at(U, e.id, k0 - 1) is None or k0 == store.epoch_txn(U)
    # RECOMPUTE-ERASURE (the second named drive): the recompute verb rewrites
    # valid_from/observed_at/confidence in place; the journal keeps the old
    # serialization byte-exact at the earlier cutoff
    r = _edge("r"); store.add_edge(r); s_r0 = _raw(store, r.id); k_r0 = _events(store, edge_id=r.id)[-1].txn
    with store._write_txn():
        store._recompute_edge_row(r.id, {"valid_from": "2026-03-01T00:00:00Z",
                                          "observed_at": "2026-03-01T00:00:00Z", "confidence": 0.4})
    assert _raw(store, r.id) != s_r0 and json.loads(_raw(store, r.id))["provenance"]["confidence"] == 0.4
    assert store.edge_state_at(U, r.id, k_r0).state == s_r0
    assert store.edge_state_at(U, r.id, k_r0 + 1).state == _raw(store, r.id)


def test_edge_state_at_reconstructs_across_the_migrated_span(tmp_path):
    """V-RECON (the third named drive): a MIGRATED edge reconstructs byte-exact
    across its baseline→first-mutation span — at the epoch the state AS FOUND,
    at every cutoff before the first post-upgrade mutation still that state,
    after it the mutated one. Kept HERE, not only in the §6a corpus (research
    red-team F1: an invariant whose coverage lives in the other seat's artifact
    is one amendment away from uncovered)."""
    pre = _edge("Porto"); p = str(tmp_path / "span.db"); _build_v12(p, [pre])
    with sqlite3.connect(p) as c:
        found = c.execute("SELECT json FROM edges WHERE id=?", (pre.id,)).fetchone()[0]
    migrate_store(p); s = SqliteStore(p)
    try:
        epoch = s.epoch_txn(U); assert epoch >= 1
        s.add_edge(_edge("Braga", relation="visits"))                   # another edge: a cutoff between
        between = _events(s)[-1].txn
        mutated = Edge.model_validate_json(found); mutated.note = "moved"; s.add_edge(mutated)
        t_next = _events(s, edge_id=pre.id)[-1].txn
        assert s.edge_state_at(U, pre.id, epoch).state == found
        assert s.edge_state_at(U, pre.id, between).state == found
        assert s.edge_state_at(U, pre.id, t_next).state == _raw(s, pre.id) != found
        with pytest.raises(Exception):
            s.edge_state_at(U, pre.id, epoch - 1)                       # pre-epoch refuses, never fabricates
    finally:
        s.close()


def test_snapshot_carrier_is_raw_and_verbatim(store):
    """V-VERBATIM: the read surface returns the journal payload VERBATIM as the
    raw carrier — no parse, no validation, no normalization; identity is
    ROW-sourced and byte-equal to the columns, never derived from the payload.
    A payload the current model REJECTS still traverses intact."""
    e = _edge(); store.add_edge(e)
    k = _events(store, edge_id=e.id)[-1].txn
    # plant a payload the current Edge model cannot parse (a future model's shape)
    garbage = '{"id": "%s", "user_id": "%s", "not_a_field": {"nested": [1, 2, "three"]}, "invalidation_reason": 17}' % (e.id, U)
    store._conn.execute("UPDATE edge_event SET state=? WHERE user_id=? AND edge_id=? AND txn=?", (garbage, U, e.id, k))
    store._conn.commit()
    r = store.edge_state_at(U, e.id, k)
    assert isinstance(r, RawEdgeState) and r.state == garbage
    assert (r.edge_id, r.user_id) == (e.id, U)
    with pytest.raises(Exception):
        Edge.model_validate_json(r.state)          # the model rejects it; the carrier did not


def test_carrier_identity_comes_from_row_not_payload(store):
    """V-VERBATIM (second named check, C-2): the carrier's `edge_id`/`user_id`
    are authoritative FROM THE ROW COLUMNS and byte-equal to them — a payload
    carrying another edge's id under this row does not move the carrier's
    identity; a mismatched-id probe stays distinguishable from a parse failure."""
    e = _edge(); store.add_edge(e)
    k = _events(store, edge_id=e.id)[-1].txn
    honest = store.edge_state_at(U, e.id, k).state
    forged = honest.replace(e.id, "e-forged").replace(f'"user_id": "{U}"', '"user_id": "mallory"')
    store._conn.execute("UPDATE edge_event SET state=? WHERE user_id=? AND edge_id=? AND txn=?",
                        (forged, U, e.id, k)); store._conn.commit()
    r = store.edge_state_at(U, e.id, k)
    assert (r.edge_id, r.user_id) == (e.id, U), "identity followed the payload"
    assert r.state == forged                       # the payload itself is still verbatim
    # negative control: the payload's embedded copy DOES disagree (so the test discriminates)
    assert json.loads(forged)["id"] != r.edge_id


# --------------------------------------------------------------------------- #
# V-BASELINE / V-EPOCH — the v12 → v13 migration
# --------------------------------------------------------------------------- #

def _build_v12(path: str, edges: list[Edge]):
    c = sqlite3.connect(path)
    for o in sv.SCHEMAS[12]:
        c.execute(o.ddl)
    c.execute("INSERT INTO store_identity(id, origin) VALUES(1, ?)", (uuid.uuid4().hex,))
    for e in edges:
        c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) VALUES(?,?,?,?,?,?,?,?)",
                  (e.id, e.user_id, e.subject, e.relation, e.object, int(e.active), int(e.quarantined), e.model_dump_json()))
    c.execute("PRAGMA user_version = 12"); c.commit(); c.close()


def test_migration_baselines_every_existing_edge_exactly_once(tmp_path):
    """V-BASELINE: after v13 migration every pre-existing edge has EXACTLY ONE
    `baseline` event, in its user's epoch batch, payload equal to the state
    found at migration (bytes); an INACTIVE found edge's event has reason
    NULL while its payload carries the reason (the producer half of
    V-COLUMN-NOT-INPUT); no runtime path emits the kind; crash-retry never
    doubles a baseline."""
    active = _edge("Porto"); inactive = _edge("Lisbon")
    inactive.invalidated_at = datetime(2026, 8, 1, tzinfo=timezone.utc); inactive.invalidation_reason = "superseded"
    other = _edge("Faro", user="v")
    p = str(tmp_path / "v12.db"); _build_v12(p, [active, inactive, other])
    found = {}
    with sqlite3.connect(p) as c:
        for eid, js in c.execute("SELECT id, json FROM edges"):
            found[eid] = js
    assert str(migrate_store(p)) == "migrated"
    s = SqliteStore(p)
    try:
        for user, ids in ((U, [active.id, inactive.id]), ("v", [other.id])):
            evs = _events(s, user)
            assert [ev.kind for ev in evs] == ["baseline"] * len(ids)
            assert len({ev.txn for ev in evs}) == 1, "all of a user's baselines share the epoch txn"
            assert {ev.edge_id for ev in evs} == set(ids)
            for ev in evs:
                assert ev.state == found[ev.edge_id], "baseline payload is the state AS FOUND, byte-exact"
                assert ev.reason is None
            assert s.epoch_txn(user) == evs[0].txn
        inactive_ev = [ev for ev in _events(s) if ev.edge_id == inactive.id][0]
        assert json.loads(inactive_ev.state)["invalidation_reason"] == "superseded" and inactive_ev.reason is None
        # no runtime path emits `baseline`
        s.add_edge(_edge("Braga"))
        assert [ev.kind for ev in _events(s)].count("baseline") == 2
        with pytest.raises(ValueError, match="baseline"):
            with s._write_txn():                 # inside a legitimate scope, so the
                s._journal_edge_write(U, "e-x", "{}", None, kind="baseline")  # refusal is about KIND
    finally:
        s.close()
    # idempotence: a second migrate_store is `current` and mints nothing
    assert str(migrate_store(p)) == "current"
    s = SqliteStore(p)
    try:
        assert [ev.kind for ev in _events(s)].count("baseline") == 2
    finally:
        s.close()


def test_migration_crash_retry_mints_exactly_one_baseline(tmp_path, monkeypatch):
    """V-BASELINE's crash-retry clause, EXERCISED (research red-team F2: the
    docstring claimed it; the body tested idempotence of a COMPLETED
    migration). A fault injected AFTER the baselines are written and BEFORE
    the stamp: the migration's one transaction unwinds — reopen finds
    user_version 12 and ZERO events — and the retried migration mints exactly
    one baseline per edge. Negative control: the fault fires (the first
    attempt does not report `migrated`)."""
    from veracium.store import edge_events as ee
    a = _edge("Porto"); b = _edge("Lisbon", relation="visits")
    p = str(tmp_path / "crash.db"); _build_v12(p, [a, b])
    real = ee.mint_store_epoch
    def fault(conn, now_iso, schema_at):
        assert conn.execute("SELECT COUNT(*) FROM edge_event").fetchone()[0] == 2  # baselines already written
        raise RuntimeError("injected between the baselines and the stamp")
    monkeypatch.setattr(ee, "mint_store_epoch", fault)
    with pytest.raises(Exception):
        migrate_store(p)
    monkeypatch.setattr(ee, "mint_store_epoch", real)
    with sqlite3.connect(p) as c:
        assert c.execute("PRAGMA user_version").fetchone()[0] == 12
        has_table = c.execute("SELECT name FROM sqlite_master WHERE name='edge_event'").fetchone()
        assert has_table is None or c.execute("SELECT COUNT(*) FROM edge_event").fetchone()[0] == 0
    assert str(migrate_store(p)) == "migrated"
    s = SqliteStore(p)
    try:
        evs = _events(s)
        assert sorted(ev.edge_id for ev in evs) == sorted([a.id, b.id]) and {ev.kind for ev in evs} == {"baseline"}
        assert len({ev.txn for ev in evs}) == 1
    finally:
        s.close()


def test_pre_epoch_queries_fail_closed(tmp_path, store):
    """V-EPOCH: `until_txn < epoch_txn(user)` REFUSES (typed) — a migrated
    store fabricates no pre-epoch knowledge; a fully-journaled user
    (epoch_txn == 0) never spuriously refuses."""
    from veracium.store.base import PreEpochQuery
    # fully journaled: epoch 0, nothing refuses
    e = _edge(); store.add_edge(e)
    assert store.epoch_txn(U) == 0
    assert store.edge_state_at(U, e.id, 0) is None           # before any event: None, not a refusal
    # migrated: the epoch is the baseline txn; below it refuses
    pre = _edge("Porto"); p = str(tmp_path / "v12b.db"); _build_v12(p, [pre])
    migrate_store(p); s = SqliteStore(p)
    try:
        epoch = s.epoch_txn(U); assert epoch >= 1
        with pytest.raises(PreEpochQuery):
            s.edge_state_at(U, pre.id, epoch - 1)
        assert s.edge_state_at(U, pre.id, epoch) is not None   # AT the epoch: the baseline
    finally:
        s.close()


# --------------------------------------------------------------------------- #
# V-TXN-ALLOC / V-BATCH
# --------------------------------------------------------------------------- #

def test_concurrent_allocation_across_two_store_instances(tmp_path):
    """V-TXN-ALLOC: two SqliteStore instances on ONE file (their Python locks
    are independent — the round-2 finding) allocate disjoint txn/seq under
    the BEGIN-IMMEDIATE schedule; the DEFERRED variant (the reviewer's own
    reproduction) is the negative control kept from the seam model."""
    p = str(tmp_path / "two.db")
    a = SqliteStore(p); b = SqliteStore(p)
    try:
        go = threading.Barrier(2)
        errs = []
        def writer(s, tag):
            try:
                go.wait()
                for i in range(20):
                    s.add_edge(_edge(f"{tag}{i}"))
            except Exception as ex:  # noqa: BLE001
                errs.append(ex)
        t1 = threading.Thread(target=writer, args=(a, "a")); t2 = threading.Thread(target=writer, args=(b, "b"))
        t1.start(); t2.start(); t1.join(); t2.join()
        assert not errs, errs
        evs = _events(a)
        seqs = [ev.seq for ev in evs]
        assert len(seqs) == 40 and len(set(seqs)) == 40 and seqs == sorted(seqs)
        txns = [ev.txn for ev in evs]
        assert len(set(txns)) == 40, "one txn per event-emitting transaction"
        # STRUCTURAL, not prose (research red-team F3: a substring check on the
        # source matched three comments): a sqlite trace callback records the
        # statements one journaled write actually EXECUTES, and BEGIN IMMEDIATE
        # must precede the FIRST allocation read (MAX over edge_event).
        trace = []
        a._conn.set_trace_callback(trace.append)
        try:
            a.add_edge(_edge("traced"))
        finally:
            a._conn.set_trace_callback(None)
        begins = [i for i, s in enumerate(trace) if s.strip().upper().startswith("BEGIN IMMEDIATE")]
        reads = [i for i, s in enumerate(trace) if "MAX(" in s.upper() and "EDGE_EVENT" in s.upper()]
        assert begins and reads and begins[0] < reads[0], trace
        assert not any(s.strip().upper() == "BEGIN" for s in trace), "a DEFERRED begin on the write path"
        # negative control: the trace discriminates — a deferred schedule on a
        # scratch connection puts its allocation read BEFORE any immediate begin
        scratch = sqlite3.connect(p); scratch.execute("PRAGMA busy_timeout=0")
        seen = []; scratch.set_trace_callback(seen.append)
        scratch.execute("SELECT COALESCE(MAX(seq), 0) FROM edge_event WHERE user_id=?", (U,)).fetchone()
        scratch.set_trace_callback(None); scratch.close()
        assert not any(s.strip().upper().startswith("BEGIN IMMEDIATE") for s in seen)
    finally:
        a.close(); b.close()


def test_deferred_schedule_negative_control(tmp_path):
    """V-TXN-ALLOC (second named check): the seam model's DEFERRED schedule —
    the round-3 reviewer's own reproduction — must KEEP failing, so the
    positive test above cannot pass by accident of a quiet machine."""
    SEAM = ROOT / "specs" / "evidence" / "0029-0030" / "seam_model"
    sys.path.insert(0, str(SEAM))
    from allocation_schedule import deferred_batch, immediate_batch, run_two_connection_schedule  # noqa: E402
    bad1, bad2 = run_two_connection_schedule(str(tmp_path / "deferred.db"), deferred_batch,
                                             busy_timeout_ms=0)
    losers = [r for r in (bad1, bad2) if r.error is not None]
    assert losers and "locked" in losers[0].error, "the DEFERRED reproduction must keep failing"
    assert bad1.maxima_read == bad2.maxima_read, "deferred must read the SAME maxima (the defect)"
    good1, good2 = run_two_connection_schedule(str(tmp_path / "immediate.db"), immediate_batch,
                                               busy_timeout_ms=5000)
    assert good1.error is None and good2.error is None and good1.txn != good2.txn, (
        "the IMMEDIATE schedule is the positive half of the same control")


def test_transaction_batches_never_split(store):
    """V-BATCH: one event-emitting write transaction = one `txn`; a
    supersession's invalidate-A + create-B share it, and every `until_txn`
    read includes or excludes the batch WHOLE."""
    a = _edge("Porto"); store.add_edge(a)
    b = _edge("Lisbon"); b.supersedes = a.id
    plan = SupersessionPlan(incoming_edge=b, insert_incoming=True, operation_id="op-1",
                            expected_state=__import__("veracium.authority", fromlist=["x"]).scope_fingerprint(
                                store.edges(U, subject="user", relation="located_at", active_only=True, include_quarantined=True)),
                            prior_invalidations=[(a.id, b.valid_from, "superseded")])
    store.apply_supersession_plan(plan)
    # the supersession's two writes: A's invalidation and B's creation (A's
    # own earlier creation is a different transaction by construction)
    batch = [ev for ev in _events(store)
             if (ev.edge_id, ev.kind) in ((a.id, "invalidated"), (b.id, "created"))]
    assert len(batch) == 2, batch
    txns = {ev.txn for ev in batch}
    assert len(txns) == 1 and {ev.kind for ev in batch} == {"invalidated", "created"}
    k = txns.pop()
    # whole-batch cutoffs: at K both are visible; at K-1 neither change is
    assert json.loads(store.edge_state_at(U, a.id, k).state)["invalidation_reason"] == "superseded"
    assert store.edge_state_at(U, b.id, k) is not None
    assert json.loads(store.edge_state_at(U, a.id, k - 1).state)["invalidation_reason"] is None
    assert store.edge_state_at(U, b.id, k - 1) is None
    # negative control: two SEPARATE writes get two txns
    store.add_edge(_edge("x")); store.add_edge(_edge("y"))
    last2 = [ev.txn for ev in _events(store)[-2:]]
    assert last2[0] != last2[1]


# --------------------------------------------------------------------------- #
# V-KIND / V-ERASE / V-INERT / V-COMPAT
# --------------------------------------------------------------------------- #

def test_event_kinds_closed_and_reasons_authoritative(store):
    """V-KIND: the kind vocabulary is closed and derived; `invalidated` events
    validate `reason` against DISPOSITIONED_REASONS (all seven); an
    unregistered reason REFUSES the write; `reason` is NULL on every other kind."""
    from veracium.store.base import EVENT_KINDS
    assert set(EVENT_KINDS) == {"created", "mutated", "invalidated", "reinstated", "baseline"}
    e = _edge(); store.add_edge(e)
    for reason in DISPOSITIONED_REASONS:
        f = _edge(reason); store.add_edge(f)
        store.invalidate_edge(f.id, datetime.now(timezone.utc), reason)
        assert _events(store, edge_id=f.id)[-1].reason == reason
    g = _edge("bad"); store.add_edge(g)
    before = _raw(store, g.id)
    with pytest.raises(ValueError):
        store.invalidate_edge(g.id, datetime.now(timezone.utc), "not_a_reason")
    assert _raw(store, g.id) == before, "an unregistered reason must refuse the WRITE, not just the event"
    assert all(ev.reason is None for ev in _events(store) if ev.kind != "invalidated")


def test_forget_user_erases_events(store):
    """V-ERASE: after `forget_user`, zero events for the user remain, in the
    same transaction; another user's events are untouched."""
    for i in range(3):
        store.add_edge(_edge(f"o{i}"))
    store.add_edge(_edge("keep", user="v"))
    assert len(_events(store)) == 3 and len(_events(store, "v")) == 1
    store.forget_user(U)
    assert _events(store) == [] and len(_events(store, "v")) == 1
    src = (SRC / "store" / "sqlite.py").read_text()
    fu = src[src.find("def forget_user"):]
    assert "DELETE FROM edge_event WHERE user_id=?" in fu[:fu.find("def ", 10)], (
        "forget_user must delete the user's events by a literal statement in its own body")


def test_events_are_store_local_and_required():
    """V-INERT: events reach no recall/context/export/MCP surface (a caller
    grep over src outside the store package), and the schema policy is
    REQUIRED (absence = damage, not drift)."""
    callers = []
    for py in SRC.rglob("*.py"):
        if py.parent.name == "store":
            continue
        if re.search(r"edge_events\(|edge_state_at\(|edge_event\b", py.read_text()):
            callers.append(str(py.relative_to(SRC)))
    assert callers == [], f"events reached a non-store surface: {callers}"
    objs = {o.name: o for o in sv.SCHEMAS[13]}
    assert objs["edge_event"].policy == sv.REQUIRED
    assert objs["ix_edge_event_lookup"].policy == sv.REBUILDABLE
    assert objs["ix_edge_event_txn"].policy == sv.REBUILDABLE
    assert sv.SCHEMA_VERSION == 13


# The pre-feature oracle's identity: captured at main 1fc357f4 (the tree BEFORE
# any journaling code), two runs byte-identical, digest recorded at capture
# (specs/evidence/0029/pre_feature_oracle/CAPTURE.md). A regeneration is loud.
PRE_FEATURE_ORACLE_SHA256 = "186a0909df6ac11dc20801800b59d1778e7073fa728f0e42f88a93f398edb947"


def test_no_consumer_behavior_identical(tmp_path):
    """V-COMPAT: with no consumer, every existing surface reproduces the
    frozen PRE-FEATURE oracle byte-identically — 0029's OWN four-surface
    capture (recall, context, export, MCP; research's co-check: the 0027
    oracle covers recall projections only), built by the same builder from
    the same fixed inputs against the JOURNALING store; the export lines are
    compared byte-wise after the two measured non-behaviour substitutions
    (store origin, export clock) the capture names under `excluded`. Plus:
    the recall and export paths import nothing from the events surface."""
    import hashlib
    import importlib.util
    here = ROOT / "specs" / "evidence" / "0029" / "pre_feature_oracle"
    frozen_bytes = (here / "pre_feature_capture.json").read_bytes()
    assert hashlib.sha256(frozen_bytes).hexdigest() == PRE_FEATURE_ORACLE_SHA256, (
        "the frozen pre-feature oracle changed — it may only be captured at the pre-feature tree")
    frozen = json.loads(frozen_bytes)
    spec = importlib.util.spec_from_file_location("oracle_0029", here / "generate_oracle.py")
    orc = importlib.util.module_from_spec(spec); spec.loader.exec_module(orc)
    store = orc.build_store(tmp_path / "oracle.db")
    try:
        got = orc.capture(store, tmp_path)
    finally:
        store.close()
    for surface in ("recall", "context", "export", "mcp", "excluded"):
        assert got[surface] == frozen[surface], f"{surface} drifted from the pre-feature oracle"
    # negative control: the comparison discriminates — one changed export byte fails it
    assert got["export"] != [ln.replace("Porto", "Faro") for ln in frozen["export"]]
    for mod in ("__init__.py", "gate.py", "graph.py", "portability.py", "mcp_server.py", "compile.py"):
        assert "edge_state_at" not in (SRC / mod).read_text() and "edge_events" not in (SRC / mod).read_text()
