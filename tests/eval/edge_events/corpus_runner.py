#!/usr/bin/env python3
"""specs/0029 §6a / specs/0030 §6a — the portable BUILDER/RUNNER for the shared
acceptance corpus. Research owns the EXPECTATIONS (`MANIFEST.json`, frozen,
sha256 pinned below); dev owns this file. If one seat authored both, the
corpus would only prove the implementation agrees with itself (README).

Every scenario is built through the store's public write API with PINNED ids
and PER-POSITION instants (the 0027 v2.2 topology discipline); the ACTUAL
event sequence and the ACTUAL reconstructions are recorded and scored against
the manifest. Transaction ids are reported as the manifest's labels
(`t1`, `t2`, … in order of first appearance per user) so the comparison is to
the frozen text, not to allocator integers.

MECHANISMS the manifest left OPEN (now its `OPEN_QUESTIONS_CLOSED`), declared here:
- Scenario 6: equal `recorded_at` is forced through the STORE's injectable
  clock (`SqliteStore(clock=...)`, the 0010 §4b-ii lease clock) held at ONE
  instant across two transactions; §4c mints once per batch from that clock.
- Scenario 10(b): the DEFERRED schedule runs in the seam model's runner (the
  product store has no deferred path); the loser fails with sqlite's verbatim
  `database is locked` (`sqlite3.OperationalError` text) and its batch is absent.

`--check` verifies the manifest digest and runs every scenario; exit 0 iff all
pass. The pytest wrapper (`test_0029_acceptance_corpus.py`) calls `run_all()`.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import threading
import uuid
from datetime import datetime, timedelta, timezone

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ.get("VERACIUM_ROOT") or HERE.parents[2])   # portable: run from anywhere
MANIFEST = HERE / "MANIFEST.json"
# amendment 1 (2026-09-05): the two OPEN mechanism questions folded in as
# OPEN_QUESTIONS_CLOSED; no expectation changed. Supersedes 820cabee48112d8e….
# amendment 2 (2026-09-05): the nine retained v2 scenarios given expectations +
# pass criterion (5) — c4197b598cecf04f…; amendment 3 (same day): V05 corrected to
# ONE shape, three events, one batch, payloads pinned (the executed absorption).
MANIFEST_SHA256 = "9974601d85cdcc7f3d459ae6d1a9c3e47206c23e79aa3c485019b9f7bd834867"

sys.path.insert(0, str(ROOT / "src"))
from veracium import EvidenceAuthor, SqliteStore, graph                # noqa: E402
from veracium.authority import scope_fingerprint                       # noqa: E402
from veracium.schema import (CorrectionAuthorisation, Disclosure, Edge,  # noqa: E402
                             Provenance, SupersessionPlan, correction_digest)
from veracium.source_identity import source_identity_digest            # noqa: E402
from veracium.store import schema_version as sv                        # noqa: E402
from veracium.store.base import PreEpochQuery                          # noqa: E402
from veracium.store.migration import migrate_store                     # noqa: E402
from veracium.store.revocation import revoke_source                    # noqa: E402

U = "corpus-user"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _at(days: int) -> datetime:
    return T0 + timedelta(days=days)


def _z(dt: datetime) -> str:
    """The corpus's canonical Z-suffixed instant (the revocation row's grammar)."""
    return dt.isoformat().replace("+00:00", "Z")


def _edge(eid: str, obj: str, *, relation="located_at", valid_from=None, user=U,
          disclosure=Disclosure.MENTIONABLE, note="", source_id=None) -> Edge:
    return Edge(id=eid, user_id=user, subject="user", relation=relation, object=obj,
                note=note, valid_from=valid_from or T0,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{eid}", observed_at=valid_from or T0,
                                      disclosure=disclosure, source_id=source_id))


def _fresh(clock=None) -> tuple[SqliteStore, pathlib.Path]:
    d = pathlib.Path(tempfile.mkdtemp(prefix="corpus-0029-"))
    return SqliteStore(str(d / "s.db"), clock=clock), d


def _labelled(store, user=U):
    """Actual events as (txn-label, kind, edge_id, reason, recorded_at) with the
    manifest's t1.. labels in order of first appearance; plus label→txn."""
    labels: dict = {}
    out = []
    for ev in store.edge_events(user):
        if ev.txn not in labels:
            labels[ev.txn] = f"t{len(labels) + 1}"
        out.append({"txn": labels[ev.txn], "kind": ev.kind, "edge": ev.edge_id,
                    "reason": ev.reason, "recorded_at": ev.recorded_at})
    return out, {v: k for k, v in labels.items()}


def _state(store, eid, k, user=U):
    r = store.edge_state_at(user, eid, k)
    return None if r is None else json.loads(r.state, object_pairs_hook=_no_dup_pairs)


def _supersede(store, prior_id, incoming: Edge, reason: str, at: datetime):
    incoming.supersedes = prior_id
    plan = SupersessionPlan(
        incoming_edge=incoming, insert_incoming=True, operation_id=f"op-{incoming.id}",
        expected_state=scope_fingerprint(store.edges(
            incoming.user_id, subject="user", relation=incoming.relation,
            active_only=True, include_quarantined=True)),
        prior_invalidations=[(prior_id, at, reason)])
    store.apply_supersession_plan(plan)


def _correct(store, prior: Edge, new: Edge, *, principal="user"):
    """The library's correction path (Memory.correct's construction, 0011 §4e):
    the graph planner's plan + the minted authorisation + the acting principal."""
    plan, refused = graph.plan_correction(store, prior, new, op_id=f"corr-{new.id}")
    assert not refused, "the corpus correction must not be refused"
    auth = CorrectionAuthorisation(origin=store.local_origin(), prior_edge_id=prior.id,
                                   replacement_digest=correction_digest(new.object),
                                   kind="corrected", principal=principal)
    store.apply_supersession_plan(plan, authorisation=auth, acting_principal=principal)


# --------------------------------------------------------------------------- #
# the ten named scenarios — each returns {"events": [...], "checks": {name: bool}}
# --------------------------------------------------------------------------- #

def s01():
    """Backdated correction: the invalidation's TXN is the correction's WRITE."""
    s, _ = _fresh()
    e1 = _edge("E1", "Porto", valid_from=_at(0)); s.add_edge(e1)
    created_payload = s.edge_state_at(U, "E1", s.edge_events(U)[-1].txn).state
    backdated = datetime(2025, 6, 1, tzinfo=timezone.utc)
    _correct(s, e1, _edge("E2", "Lisbon", valid_from=backdated))   # the correction's WRITE is t2
    events, txn = _labelled(s)
    seq = [(e["txn"], e["kind"], e["edge"], e["reason"]) for e in events]
    inv = [e for e in events if e["kind"] == "invalidated"][0]
    at_t2 = _state(s, "E1", txn["t2"])
    return {"events": events, "checks": {
        "sequence": seq == [("t1", "created", "E1", None),
                            ("t2", "invalidated", "E1", "corrected"),
                            ("t2", "created", "E2", None)],
        "invalidation txn is the correction's write (t2), not its valid-time":
            inv["txn"] == "t2" and inv["recorded_at"] >= "2026",
        "E1 at t1 == created payload verbatim":
            s.edge_state_at(U, "E1", txn["t1"]).state == created_payload,
        "E1 at t2 carries invalidated_at + reason INSIDE the json":
            at_t2["invalidation_reason"] == "corrected"
            and at_t2["invalidated_at"] is not None
            and at_t2["invalidated_at"].startswith("2025-06-01"),
    }}


def s02():
    """Revocation then reinstatement; K between recovers the erased fields."""
    s, _ = _fresh()
    s.add_edge(_edge("E1", "Porto", source_id="src:S"))
    digest = source_identity_digest(s.local_origin(), "src:S")
    revoke_source(s, U, digest, "revoke", "operator reason", _z(_at(1)))
    revoke_source(s, U, digest, "lift", "operator reason", _z(_at(2)))
    events, txn = _labelled(s)
    seq = [(e["txn"], e["kind"], e["edge"], e["reason"]) for e in events]
    mid = _state(s, "E1", txn["t2"])
    live = json.loads(s._conn.execute("SELECT json FROM edges WHERE id='E1'").fetchone()[0],
                      object_pairs_hook=_no_dup_pairs)
    return {"events": events, "checks": {
        "sequence": seq == [("t1", "created", "E1", None),
                            ("t2", "invalidated", "E1", "revoked_source"),
                            ("t3", "reinstated", "E1", None)],
        "K=t2 recovers invalidated_at + reason the live row no longer carries":
            mid["invalidation_reason"] == "revoked_source" and mid["invalidated_at"] is not None
            and live["invalidation_reason"] is None and live["invalidated_at"] is None,
    }}


def s03():
    """valid_from changed by recompute — the fourth site; digest-invisible."""
    s, _ = _fresh()
    s.add_edge(_edge("E1", "Porto", valid_from=_at(0)))
    with s._write_txn():                       # the sole recompute writer (0022's verb)
        s._recompute_edge_row("E1", {"valid_from": _z(_at(5)),
                                     "observed_at": _z(_at(5)),
                                     "confidence": 0.7})
    events, txn = _labelled(s)
    seq = [(e["txn"], e["kind"], e["edge"]) for e in events]
    return {"events": events, "checks": {
        "sequence": seq == [("t1", "created", "E1"), ("t2", "mutated", "E1")],
        "pre-recompute valid_from at t1": _state(s, "E1", txn["t1"])["valid_from"].startswith("2026-01-01"),
        "post-recompute valid_from at t2": _state(s, "E1", txn["t2"])["valid_from"].startswith("2026-01-06"),
    }}


def s04():
    """Same text, different disclosure — the serialization changed, the digest did not."""
    s, _ = _fresh()
    s.add_edge(_edge("E1", "Porto", disclosure=Disclosure.MENTIONABLE))
    s.add_edge(_edge("E1", "Porto", disclosure=Disclosure.USE_ONLY))
    events, txn = _labelled(s)
    seq = [(e["txn"], e["kind"], e["edge"]) for e in events]
    return {"events": events, "checks": {
        "sequence": seq == [("t1", "created", "E1"), ("t2", "mutated", "E1")],
        "pre disclosure": _state(s, "E1", txn["t1"])["provenance"]["disclosure"] == "mentionable",
        "post disclosure": _state(s, "E1", txn["t2"])["provenance"]["disclosure"] == "use_only",
    }}


def s05():
    """Multi-edge supersession; no cutoff observes a half-applied batch."""
    s, _ = _fresh()
    s.add_edge(_edge("A", "Porto")); s.add_edge(_edge("B", "Braga", relation="visits"))
    _supersede(s, "A", _edge("C", "Lisbon"), "superseded", _at(3))
    events, txn = _labelled(s)
    seq = [(e["txn"], e["kind"], e["edge"], e["reason"]) for e in events]
    half_applied = []
    for k in range(0, txn["t3"] + 1):
        a = _state(s, "A", k); c = _state(s, "C", k)
        a_inv = a is not None and a["invalidated_at"] is not None
        if a_inv != (c is not None):
            half_applied.append(k)
    return {"events": events, "checks": {
        "sequence": seq == [("t1", "created", "A", None), ("t2", "created", "B", None),
                            ("t3", "invalidated", "A", "superseded"), ("t3", "created", "C", None)],
        "at t2: A active, C absent": _state(s, "A", txn["t2"])["invalidated_at"] is None
                                    and _state(s, "C", txn["t2"]) is None,
        "at t3: A invalidated, C present": _state(s, "A", txn["t3"])["invalidated_at"] is not None
                                          and _state(s, "C", txn["t3"]) is not None,
        "no cutoff observes a half-applied supersession": half_applied == [],
    }}


def s06():
    """Two transactions sharing one recorded_at — txn distinguishes."""
    frozen = _at(10)
    s, _ = _fresh(clock=lambda: frozen)        # OPEN Q1: injected clock, held
    s.add_edge(_edge("E1", "Porto")); s.add_edge(_edge("E2", "Lisbon", relation="visits"))
    events, txn = _labelled(s)
    return {"events": events, "checks": {
        "both batches carry one recorded_at": len({e["recorded_at"] for e in events}) == 1,
        "txn distinguishes them": [e["txn"] for e in events] == ["t1", "t2"],
    }}


def s07():
    """A later dispute applied to an earlier snapshot — 0029 reconstructs the held belief."""
    s, _ = _fresh()
    s.add_edge(_edge("E1", "Porto")); held = s.edge_state_at(U, "E1", 1).state
    s.invalidate_edge("E1", _at(4), "disputed")
    events, txn = _labelled(s)
    seq = [(e["txn"], e["kind"], e["edge"], e["reason"]) for e in events]
    return {"events": events, "checks": {
        "sequence": seq == [("t1", "created", "E1", None), ("t2", "invalidated", "E1", "disputed")],
        "K=t1 is the pre-dispute payload": s.edge_state_at(U, "E1", txn["t1"]).state == held,
    }}


def s08():
    """A payload the current model rejects traverses the RAW carrier verbatim."""
    s, _ = _fresh()
    s.add_edge(_edge("E1", "Porto")); k = s.edge_events(U)[-1].txn
    garbage = '{"id": "E1", "user_id": "%s", "future_field": [1, {"x": null}], "invalidation_reason": 17}' % U
    s._conn.execute("UPDATE edge_event SET state=? WHERE user_id=? AND edge_id='E1'", (garbage, U))
    s._conn.commit()
    r = s.edge_state_at(U, "E1", k)
    rejected = False
    try:
        Edge.model_validate_json(r.state)
    except Exception:  # noqa: BLE001
        rejected = True
    events, _ = _labelled(s)
    return {"events": events, "checks": {
        "journaled like any state (created)": [e["kind"] for e in events] == ["created"],
        "carrier returns the payload verbatim": r.state == garbage,
        "identity from the row columns": (r.edge_id, r.user_id) == ("E1", U),
        "the model rejects it; the carrier did not": rejected,
    }}


def _build_v12(path: str, edges: list) -> dict:
    c = sqlite3.connect(path)
    for o in sv.SCHEMAS[12]:
        c.execute(o.ddl)
    c.execute("INSERT INTO store_identity(id, origin) VALUES(1, ?)", (str(uuid.uuid4()),))
    found = {}
    for e in edges:
        js = e.model_dump_json(); found[e.id] = js
        c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                  "VALUES(?,?,?,?,?,?,?,?)",
                  (e.id, e.user_id, e.subject, e.relation, e.object, int(e.active),
                   int(e.quarantined), js))
    c.execute("PRAGMA user_version = 12"); c.commit(); c.close()
    return found


def s09():
    """Migrated edges AT the epoch, around the first post-upgrade mutation; the
    epoch_txn = 0 contrast cell."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="corpus-0029-")); p = str(d / "v12.db")
    inactive = _edge("OLD", "Faro"); inactive.invalidated_at = _at(2); inactive.invalidation_reason = "superseded"
    found = _build_v12(p, [_edge("PRE", "Porto"), inactive])
    migrate_store(p); s = SqliteStore(p)
    epoch = s.epoch_txn(U)
    s.add_edge(_edge("NEW", "Braga", relation="visits"))            # the "between" cutoff
    between = s.edge_events(U)[-1].txn
    s.add_edge(_edge("PRE", "Coimbra"))                              # the mutation
    t_next = s.edge_events(U)[-1].txn
    events, _ = _labelled(s)
    baselines = [e for e in events if e["kind"] == "baseline"]
    refused = False
    try:
        s.edge_state_at(U, "PRE", epoch - 1)
    except PreEpochQuery:
        refused = True
    s.add_edge(_edge("X", "Porto", user="newcomer"))
    return {"events": events, "checks": {
        "one baseline per pre-existing edge, one batch, reason NULL, payload as found":
            sorted(e["edge"] for e in baselines) == ["OLD", "PRE"]
            and len({e["txn"] for e in baselines}) == 1
            and all(e["reason"] is None for e in baselines)
            and all(s.edge_state_at(U, e["edge"], epoch).state == found[e["edge"]] for e in baselines),
        "found invalidation_reason lives INSIDE the payload": _state(s, "OLD", epoch)["invalidation_reason"] == "superseded",
        "pre-epoch cutoff refuses (typed)": refused,
        "at the epoch: the baseline payload, exact": s.edge_state_at(U, "PRE", epoch).state == found["PRE"],
        "between epoch and t_next: still the baseline": s.edge_state_at(U, "PRE", between).state == found["PRE"],
        "at t_next: the mutated payload": _state(s, "PRE", t_next)["object"] == "Coimbra",
        "the mutation is `mutated`": [e["kind"] for e in events if e["edge"] == "PRE"] == ["baseline", "mutated"],
        "CONTRAST: a post-migration user has epoch_txn == 0 and no cutoff refuses":
            s.epoch_txn("newcomer") == 0 and s.edge_state_at("newcomer", "X", 0) is None
            and s.edge_state_at("newcomer", "X", 1) is not None,
    }}


def s10():
    """Concurrent allocation from two connections — both schedules."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="corpus-0029-")); p = str(d / "two.db")
    a = SqliteStore(p); b = SqliteStore(p); errs = []; go = threading.Barrier(2)

    def writer(st, tag):
        try:
            go.wait()
            for i in range(15):
                st.add_edge(_edge(f"{tag}{i}", f"o{tag}{i}", relation=f"r{tag}{i}"))
        except Exception as ex:  # noqa: BLE001
            errs.append(repr(ex))
    ts = [threading.Thread(target=writer, args=(a, "a")), threading.Thread(target=writer, args=(b, "b"))]
    [t.start() for t in ts]; [t.join() for t in ts]
    evs = a.edge_events(U); seqs = [e.seq for e in evs]; txns = [e.txn for e in evs]
    positive = (not errs and len(seqs) == 30 and seqs == list(range(1, 31)) and len(set(txns)) == 30)
    # (b) NEGATIVE CONTROL — the seam model's DEFERRED reproduction (OPEN Q2)
    sys.path.insert(0, str(ROOT / "specs" / "evidence" / "0029-0030" / "seam_model"))
    from allocation_schedule import deferred_batch, run_two_connection_schedule  # noqa: E402
    bad1, bad2 = run_two_connection_schedule(str(d / "deferred.db"), deferred_batch, busy_timeout_ms=0)
    losers = [r for r in (bad1, bad2) if r.error is not None]
    winners = [r for r in (bad1, bad2) if r.error is None]
    # "no partial batch persists" is a fact about the DATABASE: exactly the
    # winner's rows, one txn, none of the loser's (its seqs are the ones it
    # READ — identical to the winner's, which IS the defect being reproduced)
    c = sqlite3.connect(str(d / "deferred.db"))
    persisted = c.execute("SELECT txn, seq FROM edge_event ORDER BY seq").fetchall(); c.close()
    negative = (len(losers) == 1 and len(winners) == 1
                and "locked" in losers[0].error            # substring: either surface (amendment 1)
                and bad1.maxima_read == bad2.maxima_read
                and [s for _t, s in persisted] == sorted(winners[0].seqs)
                and {t_ for t_, _s in persisted} == {winners[0].txn})
    events, _ = _labelled(a)
    return {"events": events, "checks": {
        "(a) IMMEDIATE: whole distinct batches, gapless seq, zero refusals": positive,
        "(b) DEFERRED control: same maxima read, second fails `database is locked`, no partial batch": negative,
    }}


def _no_dup_pairs(pairs):
    """0026's evidence-boundary rule: a duplicate-key-REFUSING decoder."""
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate key {k!r} in MANIFEST.json")
        d[k] = v
    return d


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(), object_pairs_hook=_no_dup_pairs)


def manifest_ok() -> bool:
    return hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == MANIFEST_SHA256


SCENARIOS = {"S01": s01, "S02": s02, "S03": s03, "S04": s04, "S05": s05,
             "S06": s06, "S07": s07, "S08": s08, "S09": s09, "S10": s10}


# --------------------------------------------------------------------------- #
# the nine RETAINED v2 scenarios (amendment 2, criterion 5) — DATA-DRIVEN:
# each builder performs ONE scored operation and returns the ACTUAL batch it
# wrote as (role, kind, reason) triples (roles: prior/incoming/absorbed/
# survivor or None) plus any extra facts the entry's REQUIRED clauses need;
# the scorer compares against whatever SHAPE the manifest entry carries —
# `expected_events` (ordered), `expected_events_UNORDERED_WITHIN_THE_BATCH`
# (a set), or `cells` (any cell matching). An amendment to the expectations
# changes the pinned digest, never this code.
# --------------------------------------------------------------------------- #

def _batch_after(store, n_before, roles, user=U):
    """The events appended after the first n_before, as (role, kind, reason)."""
    evs = store.edge_events(user)[n_before:]
    txns = {e.txn for e in evs}
    return [(roles.get(e.edge_id), e.kind, e.reason) for e in evs], txns


def _confirm(store, eid, at, corr="c-1"):
    import hashlib
    store.confirm_edge(U, eid, actor="user", call_path="host_api", correlation_id=corr,
                       request_digest=hashlib.sha256(f"confirm:{eid}".encode()).hexdigest(),
                       confirmed_at=at)


def v01_create():
    s, _ = _fresh(); s.add_edge(_edge("E1", "Porto"))
    batch, txns = _batch_after(s, 0, {})
    return {"batch": batch, "one_txn": len(txns) == 1}


def v02_supersede():
    s, _ = _fresh(); s.add_edge(_edge("A", "Porto")); n = len(s.edge_events(U))
    _supersede(s, "A", _edge("B", "Lisbon"), "superseded", _at(2))
    batch, txns = _batch_after(s, n, {"A": "prior", "B": "incoming"})
    return {"batch": batch, "one_txn": len(txns) == 1}


def v03_confirm(cell):
    s, _ = _fresh()
    if cell.startswith("a"):
        e = _edge("E1", "Porto"); e.provenance.confidence = 0.5; s.add_edge(e)   # confirm raises it to 0.9
    else:
        e = _edge("E1", "Porto", valid_from=_at(10)); s.add_edge(e)            # observed_at 10d ≥ confirmed_at
    n = len(s.edge_events(U)); _confirm(s, "E1", _at(5))
    batch, txns = _batch_after(s, n, {})
    return {"batch": batch, "one_txn": len(txns) <= 1}


def v04_note_append():
    s, _ = _fresh(); s.add_edge(_edge("E1", "Porto", note="")); n = len(s.edge_events(U))
    k_prior = s.edge_events(U)[-1].txn
    s.add_edge(_edge("E1", "Porto", note="appended"))
    batch, txns = _batch_after(s, n, {})
    prior_note = _state(s, "E1", k_prior)["note"]
    return {"batch": batch, "one_txn": len(txns) == 1,
            "required": prior_note == "" and _state(s, "E1", k_prior + 1)["note"] == "appended"}


def v05_absorb():
    """The library's real absorption (graph.apply_supersession): prior 'vim'
    absorbed by the more specific 'vim editor' — ONE path (amendment 3): the
    absorbed prior restated then invalidated, the survivor created, one batch."""
    from veracium.schema import DEFAULT_RELATIONS
    s, _ = _fresh(); s.add_edge(_edge("P", "vim", relation="uses_tool")); n = len(s.edge_events(U))
    graph.apply_supersession(s, _edge("S", "vim editor", relation="uses_tool"), DEFAULT_RELATIONS)
    batch, txns = _batch_after(s, n, {"P": "absorbed", "S": "survivor"})
    # REQUIRED_PAYLOADS (amendment 3): content, not seq order — the absorbed edge's
    # `mutated` state carries the EXTENDED note; its `invalidated` state carries that
    # note AND the invalidation fields; REQUIRED_F1: its PRIOR event holds the
    # pre-restate note.
    evs = {(e.edge_id, e.kind): json.loads(e.state, object_pairs_hook=_no_dup_pairs)
           for e in s.edge_events(U)}
    mut, inv, pre = evs.get(("P", "mutated")), evs.get(("P", "invalidated")), evs.get(("P", "created"))
    payloads = (mut is not None and "absorbed_by:S" in mut["note"] and mut["invalidated_at"] is None
                and inv is not None and "absorbed_by:S" in inv["note"]
                and inv["invalidated_at"] is not None and inv["invalidation_reason"] == "absorbed_duplicate"
                and pre is not None and "absorbed_by" not in pre["note"])
    return {"batch": batch, "one_txn": len(txns) == 1, "required": payloads}


def v06_dispute():
    s, _ = _fresh(); s.add_edge(_edge("E1", "Porto")); n = len(s.edge_events(U))
    s.invalidate_edge("E1", _at(3), "disputed")
    batch, txns = _batch_after(s, n, {})
    # C-3 both legs: a LATER event for the edge carries reason NULL in the column
    # while its payload still carries 'disputed'
    with s._write_txn():
        s._recompute_edge_row("E1", {"valid_from": _z(_at(1)), "observed_at": _z(_at(1)), "confidence": 0.6})
    later = s.edge_events(U)[-1]
    return {"batch": batch, "one_txn": len(txns) == 1,
            "required": later.kind == "mutated" and later.reason is None
            and json.loads(later.state, object_pairs_hook=_no_dup_pairs)["invalidation_reason"] == "disputed"}


def v07_expiry(cell):
    reason = "lapsed" if cell.startswith("a") else "decayed"
    s, _ = _fresh(); s.add_edge(_edge("E1", "Porto")); n = len(s.edge_events(U))
    s.invalidate_edge("E1", _at(30), reason)
    batch, txns = _batch_after(s, n, {})
    return {"batch": batch, "one_txn": len(txns) == 1}


def _import_plan(store, edge):
    """The import commit's presence-admitting replace (§4b; v4 F-A's reachable
    instance), reached through the importer's own commit primitive with the
    destination state declared — `portability.import_memory` skips an existing
    id BEFORE the commit, so cells b/c cannot be reached through it."""
    present = store._conn.execute("SELECT 1 FROM edges WHERE id=?", (edge.id,)).fetchone() is not None
    return store.commit_outcome_import_plan(
        U, {"edges": [edge], "episodes": [], "contributions": []},
        {"edge_ids": {edge.id: present}, "episode_records": {}, "chain_heads": {},
         "contribution_state": {}})


def v08_import(cell):
    from veracium.portability import export_memory, import_memory
    s, d = _fresh()
    if cell.startswith("a"):
        src, sd = _fresh(); src.add_edge(_edge("E1", "Porto"))       # a SECOND store exports
        export_memory(src, U, sd / "x.jsonl"); src.close()
        n = len(s.edge_events(U)); import_memory(s, sd / "x.jsonl")
        batch, txns = _batch_after(s, n, {})
        # REQUIRED_ACROSS_CELLS: nothing of the exporting store's journal crossed
        return {"batch": batch, "one_txn": len(txns) == 1,
                "required": all(e.txn == 1 for e in s.edge_events(U))}
    s.add_edge(_edge("E1", "Porto")); n = len(s.edge_events(U))
    live = Edge.model_validate_json(s._conn.execute("SELECT json FROM edges WHERE id='E1'").fetchone()[0])
    if cell.startswith("b"):
        live.note = "one field edited"                                # serialization CHANGED
    _import_plan(s, live)                                             # cell c: byte-identical
    batch, txns = _batch_after(s, n, {})
    return {"batch": batch, "one_txn": len(txns) <= 1}


def v09_erase():
    s, _ = _fresh()
    for i in range(3):
        s.add_edge(_edge(f"E{i}", f"o{i}", relation=f"r{i}"))
    s.add_edge(_edge("K", "keep", user="other"))
    s.forget_user(U)
    rows = s._conn.execute("SELECT COUNT(*) FROM edge_event WHERE user_id=?", (U,)).fetchone()[0]
    other = s._conn.execute("SELECT COUNT(*) FROM edge_event WHERE user_id='other'").fetchone()[0]
    kinds = {r[0] for r in s._conn.execute("SELECT DISTINCT kind FROM edge_event")}
    return {"batch": [], "one_txn": True,
            "required": rows == 0 and other == 1 and kinds <= set(("created", "mutated", "invalidated", "reinstated", "baseline"))}


RETAINED = {"V01": v01_create, "V02": v02_supersede, "V03": v03_confirm, "V04": v04_note_append,
            "V05": v05_absorb, "V06": v06_dispute, "V07": v07_expiry, "V08": v08_import,
            "V09": v09_erase}
CELLED = {"V03", "V07", "V08"}                 # builders taking the manifest's cell label


def _triples(expected, roles_present):
    """Manifest event dicts → (role, kind, reason) triples in the builder's vocabulary."""
    out = []
    for e in expected:
        role = e.get("role", e.get("edge"))          # amendment 3 keys it `role`; V02 `edge`
        out.append((role if roles_present else None, e["kind"], e.get("reason")))
    return out


def _score_shape(entry, got):
    """Compare one manifest shape against one actual batch."""
    if "expected_events_UNORDERED_WITHIN_THE_BATCH" in entry:
        exp = _triples(entry["expected_events_UNORDERED_WITHIN_THE_BATCH"], True)
        return set(exp) == set(got["batch"]) and len(exp) == len(got["batch"]) and got["one_txn"]
    exp = _triples(entry["expected_events"], False)
    actual = [(None, k, r) for _role, k, r in got["batch"]]
    return exp == actual and got["one_txn"]


def run_retained() -> dict:
    m = load_manifest(); results = {}
    for entry in m["retained_v2_scenarios"]:
        sid = entry["id"]; build = RETAINED[sid]; checks = {}
        if "cells" in entry:
            for cell in entry["cells"]:
                got = build(cell["cell"])
                checks[f"cell {cell['cell']}"] = _score_shape(cell, got)
                if "required" in got:
                    checks[f"cell {cell['cell']} · REQUIRED"] = got["required"]
        else:
            got = build()
            checks["events"] = _score_shape(entry, got)
            if "required" in got:
                checks["REQUIRED"] = got["required"]
        results[sid] = {"pass": all(checks.values()), "checks": checks}
    return results


def run_all() -> dict:
    m = load_manifest()
    ids = [sc["id"] for sc in m["scenarios"]]
    results = {}
    for sid in ids:
        r = SCENARIOS[sid]()
        results[sid] = {"pass": all(r["checks"].values()), **r}
    retained = run_retained()
    # criterion (5): every retained id is SCORED — a runner covering fewer than
    # the manifest lists fails here, not silently
    covered = set(retained) == {e["id"] for e in m["retained_v2_scenarios"]} == set(RETAINED)
    ok = manifest_ok() and covered and all(r["pass"] for r in results.values()) \
        and all(r["pass"] for r in retained.values())
    return {"manifest_sha256_ok": manifest_ok(), "scenarios": results, "retained": retained,
            "retained_all_scored": covered, "pass": ok}


def main(argv):
    out = run_all()
    for group in ("scenarios", "retained"):
        for sid, r in out[group].items():
            flag = "PASS" if r["pass"] else "FAIL"
            print(f"{sid} {flag}")
            for name, ok in r["checks"].items():
                if not ok:
                    print(f"    FAILED: {name}")
    print(f"manifest digest {'ok' if out['manifest_sha256_ok'] else 'MISMATCH'} · "
          f"{sum(r['pass'] for r in out['scenarios'].values())}/{len(out['scenarios'])} scenarios · "
          f"{sum(r['pass'] for r in out['retained'].values())}/{len(out['retained'])} retained"
          f"{'' if out['retained_all_scored'] else ' · CRITERION 5 UNMET'}")
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
