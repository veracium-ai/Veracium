"""specs/0049 v2.2: `edges_since` means learned — round 1's amendments (0049-R1-01..03) as cells.

E5  (R1-01) one snapshot: the timestamp map and the edge listing are read inside the store's `read_window`, so a
    writer committing between them cannot make a complete journal look incomplete. Two cells, one per journal mode,
    because the window behaves differently in each (0028 §5): under WAL the writer commits and the reader keeps its
    snapshot; under the default journal the writer waits for the window to close.
E6  (R1-03) FIRST over a record's lifetime: a later confirm, update or reinstatement of the SAME id does not make it
    newly learned; the cutoff is strict; a migration baseline is an upper bound; an import or a restore is learned
    when THIS store received it. The last-event mutant fails each.
E7  (the owner's ruling, 2026-11-15) introspect's `last_observed`, with `last_recorded` its deprecated alias.

E4a/E4b (R1-02) are in test_host_queries.py beside the returned-value check they extend."""
from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium.schema import ConfirmationActor, Edge, Provenance
from veracium.store.sqlite import SqliteStore

U = "u"


def _clocked(path, start):
    now = {"t": start}
    return SqliteStore(str(path), clock=lambda: now["t"]), now


def _mem(store):
    return Memory(llm=lambda *a, **k: "x", store=store,
                  config=MemoryConfig(db_path=store._path,
                                      require_source_id=False, wiki_recompile_after_writes=0))


def _edge(eid, obj="tea", *, flag=False, source_id=None, observed_at=None):
    return Edge(id=eid, user_id=U, subject="user", relation=f"likes_{eid}", object=obj, needs_confirmation=flag,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"ev-{eid}",
                                      source_id=source_id, **({"observed_at": observed_at} if observed_at else {})))


def _ids(edges):
    return sorted(e.id for e in edges)


def _at(day, month=7, hour=12):
    return datetime(2026, month, day, hour, tzinfo=timezone.utc)


# ------------------------------------------------------------------ E5: one snapshot, per journal mode
def _race(tmp_path, wal):
    db = str(tmp_path / "v.db")
    if wal:
        c = sqlite3.connect(db)
        assert c.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        c.close()
    reader = Memory(llm=lambda *a, **k: "x",
                    config=MemoryConfig(db_path=db, require_source_id=False, wiki_recompile_after_writes=0))
    writer = Memory(llm=lambda *a, **k: "x",
                    config=MemoryConfig(db_path=db, require_source_id=False, wiki_recompile_after_writes=0))
    mode = reader.store._conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == ("wal" if wal else "delete"), mode
    return reader, writer


def test_e5a_under_wal_a_writer_between_the_two_reads_is_not_a_missing_event(tmp_path):
    """The reviewer's schedule (0049-R1-01): the writer commits AFTER the reader's timestamp read and BEFORE its edge
    listing. Under WAL the writer commits and the window keeps its snapshot: the first call is the coherent
    pre-insert result, never ValueError; the next call returns the new edge. Mutant: the two reads outside one
    window (the round-1 candidate)."""
    reader, writer = _race(tmp_path, wal=True)
    real = reader.store.first_recorded_at

    def between(user_id):
        m = real(user_id)
        writer.store.add_edge(_edge("e-new"))                   # commits: WAL does not block on the reader
        return m
    reader.store.first_recorded_at = between
    try:
        first = reader.edges_since(U, "2020-01-01")
    except ValueError as exc:                                   # the defect: a complete journal read as incomplete
        first = f"ValueError: {exc}"
    reader.store.first_recorded_at = real
    assert first == [], first
    assert _ids(reader.edges_since(U, "2020-01-01")) == ["e-new"]
    assert [e.edge_id for e in reader.store.edge_events(U)] == ["e-new"]       # the write landed, journaled


def test_e5b_under_the_default_journal_the_writer_waits_for_the_window(tmp_path):
    """The same schedule under the default (rollback) journal: the reader's window holds its SHARED lock, so the
    writer, on its own thread, waits and commits once the window closes (0028 §5). The first call is coherent (no
    e-new, never ValueError); the write's outcome is asserted (committed, journaled); the next call returns it.
    Mutant: the two reads outside one window (the writer then commits between them: ValueError)."""
    reader, writer = _race(tmp_path, wal=False)
    real = reader.store.first_recorded_at
    outcome = {}

    def write():
        try:
            writer.store.add_edge(_edge("e-new"))
            outcome["w"] = "committed"
        except Exception as exc:                                # pragma: no cover - asserted below
            outcome["w"] = f"{type(exc).__name__}: {exc}"
    t = threading.Thread(target=write)

    def between(user_id):
        m = real(user_id)
        t.start()
        t.join(0.5)                                             # give the writer every chance to land between reads
        return m
    reader.store.first_recorded_at = between
    try:
        first = reader.edges_since(U, "2020-01-01")
    except ValueError as exc:
        first = f"ValueError: {exc}"
    t.join(10)
    reader.store.first_recorded_at = real
    assert first == [], first
    assert outcome == {"w": "committed"}, outcome
    assert _ids(reader.edges_since(U, "2020-01-01")) == ["e-new"]


# ------------------------------------------------------------------ E6: FIRST over a record's lifetime
def test_e6_a_later_confirm_does_not_make_an_old_edge_newly_learned(tmp_path):
    """The reviewer's witness (0049-R1-03): learned July 1, confirmed July 10, asked after July 5. The confirm is a
    later journal event of the SAME id; the first stays July 1, so the edge is not returned.
    Mutant: the LAST journal event instead of the first."""
    store, now = _clocked(tmp_path / "v.db", _at(1))
    m = _mem(store)
    store.add_edge(_edge("e-1", flag=True))
    now["t"] = _at(10)
    m.confirm(U, "e-1", actor=ConfirmationActor.USER)
    assert len(store.edge_events(U, edge_id="e-1")) >= 2                     # a later event of the same id exists
    assert m.edges_since(U, _at(5)) == []
    assert _ids(m.edges_since(U, _at(1, hour=11))) == ["e-1"]


def test_e6_a_later_update_of_the_same_id_does_not_reset_learned(tmp_path):
    """A dispute on July 10 rewrites the same row (a `mutated` event). Not newly learned. Mutant: the last event."""
    store, now = _clocked(tmp_path / "v.db", _at(1))
    m = _mem(store)
    store.add_edge(_edge("e-1"))
    now["t"] = _at(10)
    m.dispute(U, "e-1", reason="not any more")
    assert [e.kind for e in store.edge_events(U, edge_id="e-1")][:1] == ["created"]
    assert len(store.edge_events(U, edge_id="e-1")) >= 2
    assert m.edges_since(U, _at(5)) == []


def test_e6_a_reinstatement_of_the_same_id_does_not_reset_learned(tmp_path):
    """Retired by a source revocation and REINSTATED by its lift on July 10 (the real writer, 0022's revocation lift):
    `invalidated` then `reinstated` events of the same id. Still learned July 1. Mutant: the last event."""
    from veracium.store import revocation as rv
    from veracium.store.revocation_sweep import digest_of
    store, now = _clocked(tmp_path / "v.db", _at(1))
    m = _mem(store)
    store.add_edge(_edge("e-1", source_id="feed-1"))
    d = digest_of(None, "feed-1", store.local_origin())
    now["t"] = _at(8)
    rv.revoke_source(store, U, d, "revoke", "policy", "2026-07-08T00:00:00Z")
    now["t"] = _at(10)
    rv.revoke_source(store, U, d, "lift", "policy", "2026-07-10T00:00:00Z")
    kinds = [e.kind for e in store.edge_events(U, edge_id="e-1")]
    assert kinds[0] == "created" and "reinstated" in kinds, kinds
    assert m.edges_since(U, _at(5)) == []


def test_e6_the_cutoff_is_strict(tmp_path):
    """`since` equal to the first event's recorded_at excludes the edge; a microsecond earlier includes it. Mutant:
    `>=` for `>`."""
    store, now = _clocked(tmp_path / "v.db", _at(1))
    m = _mem(store)
    store.add_edge(_edge("e-1"))
    at = datetime.fromisoformat(store.first_recorded_at(U)["e-1"])
    assert m.edges_since(U, at) == []
    assert _ids(m.edges_since(U, at - timedelta(microseconds=1))) == ["e-1"]


def test_e6_a_migration_baseline_is_an_upper_bound_on_learning(tmp_path):
    """A store that predates the journal is baselined at migration (0029 §4e, the migration's own writer): every edge
    found gets ONE `baseline` event at the migration time. Learned before the baseline cannot be told apart, so a
    cutoff before it RETURNS the edge (the declared conservative behaviour, §4), and a cutoff after it does not."""
    from veracium.store.edge_events import journal_baselines
    store, now = _clocked(tmp_path / "v.db", _at(1))
    m = _mem(store)
    store.add_edge(_edge("e-1"))
    with store._conn:                                           # as found by a migration: no journal yet
        store._conn.execute("DELETE FROM edge_event WHERE user_id=?", (U,))
        assert journal_baselines(store._conn, "2026-08-01T00:00:00+00:00") == 1
    assert [e.kind for e in store.edge_events(U, edge_id="e-1")] == ["baseline"]
    assert _ids(m.edges_since(U, _at(15))) == ["e-1"]          # learned July 1, but the store can only say "by Aug 1"
    assert m.edges_since(U, _at(2, month=8)) == []


@pytest.mark.parametrize("form", ["import_memory", "restore", "cross-user"])
def test_e6_an_import_is_learned_when_this_store_received_it(tmp_path, form):
    """Measured at the pin (dev, 2026-11-15): `import_memory` and `restore=True` each journal `created` at THIS
    store's import time, not the source's; a same-user import keeps the id, a cross-user one mints it."""
    from veracium.portability import export_memory, import_memory
    src, _ = _clocked(tmp_path / "src.db", _at(1))
    src.add_edge(_edge("e-1"))
    export_memory(src, U, tmp_path / "x.jsonl")
    dst, _ = _clocked(tmp_path / "dst.db", _at(20))
    m = _mem(dst)
    to = "v" if form == "cross-user" else U
    import_memory(dst, tmp_path / "x.jsonl", **({"restore": True} if form == "restore" else {}),
                  **({"user_id": to} if form == "cross-user" else {}))
    (e,) = dst.edges(to, active_only=False, include_quarantined=True)
    assert (e.id == "e-1") is (form != "cross-user"), e.id
    assert _ids(m.edges_since(to, _at(10))) == [e.id]
    assert m.edges_since(to, _at(21)) == []


# ------------------------------------------------------------------ E7: introspect's last_observed
def test_e7_last_observed_is_max_observed_at_and_last_recorded_is_its_deprecated_alias(tmp_path):
    """The owner's ruling (2026-11-15), the round-1 verdict's option (b): the value introspect called `last_recorded`
    is max(provenance.observed_at), an OBSERVATION time, not a record time. It is `last_observed`; `last_recorded`
    stays one release as a deprecated alias with the SAME value. Mutants: the alias dropped; the new key computed
    from anything but max(observed_at)."""
    from veracium.introspect import report
    store, now = _clocked(tmp_path / "v.db", _at(1))
    store.add_edge(_edge("e-1", observed_at=_at(3)))
    store.add_edge(_edge("e-2", observed_at=_at(9)))
    out = report(store, U)
    assert out["last_observed"] == _at(9).isoformat(), out["last_observed"]
    assert out.get("last_recorded") == out["last_observed"], sorted(out)
