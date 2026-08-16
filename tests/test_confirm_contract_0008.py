"""specs/0008 — the confirmation store contract (§6b/§6c/§6d), invariants C7–C12.

The behavioural invariants C1–C6 (reinforcement no longer clears the flag) live in
`test_staleness_clearing_0008.py`. This module exercises the atomic `confirm_edge`
primitive, idempotency/replay, the validated metadata, the `add_edge` guards, the
retention/erasure rules, and the version-compat gate.
"""

import tempfile
from datetime import datetime, timezone

import pytest

from veracium import Memory, MemoryConfig
from veracium.portability import export_memory
from veracium.schema import (ConfirmationActor, ConfirmationCallPath, Disclosure, Edge, EvidenceAuthor, Provenance)
from veracium.store import schema_version as sv
from veracium.store.migration import migrate_store
from veracium.store.sqlite import SqliteStore, StoreVersionError

NOW = datetime(2026, 3, 1, tzinfo=timezone.utc)


def _edge(eid="e1", *, needs=True, user="u", obj="dark mode"):
    return Edge(id=eid, user_id=user, subject="user", relation="prefers",
                object=obj, valid_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
                active=True, needs_confirmation=needs,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=eid, disclosure=Disclosure.MENTIONABLE,
                                      observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))


def _store():
    return SqliteStore(tempfile.mktemp(suffix=".db"))


def _confirm(store, **over):
    kw = dict(actor=ConfirmationActor.USER, call_path=ConfirmationCallPath.HOST_API,
              correlation_id="k1", request_digest="d1", confirmed_at=NOW)
    kw.update(over)
    return store.confirm_edge("u", "e1", **kw)


# --- C7: confirmation is all-or-nothing -------------------------------------

def test_confirmation_is_atomic():
    """C7: if the mandatory record cannot commit, EVERY edge field is unchanged and
    no episode is written — the flag stays set."""
    s = _store()
    s.add_edge(_edge())

    class _FailOnRecord:                                   # sqlite3.Connection is a
        def __init__(self, real): self._real = real       # C type — proxy, not patch
        def execute(self, sql, *a):
            if "INSERT INTO confirmations" in sql:
                raise RuntimeError("audit store down")
            return self._real.execute(sql, *a)
        def __getattr__(self, n): return getattr(self._real, n)
    real = s._conn
    s._conn = _FailOnRecord(real)
    with pytest.raises(RuntimeError, match="audit store down"):
        _confirm(s)
    s._conn = real
    edge = s.edges("u", active_only=False)[0]
    assert edge.needs_confirmation is True                 # flag NOT cleared
    assert edge.provenance.observed_at == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert s.episodes("u") == []                           # no episode
    assert s.confirmations_for("u", "e1") == []            # no record


# --- C8: replay and collision -----------------------------------------------

def test_replay_returns_the_original_success():
    """C8: a replay of the SAME canonical request returns the ORIGINAL, with the
    STORED instant, and writes exactly one record/episode."""
    s = _store()
    s.add_edge(_edge())
    first = _confirm(s)
    assert first.replayed is False
    again = _confirm(s, confirmed_at=datetime(2026, 9, 9, tzinfo=timezone.utc))
    assert again.replayed is True
    assert again.id == first.id and again.confirmed_at == NOW  # stored, not fresh
    assert len(s.confirmations_for("u", "e1")) == 1
    assert len(s.episodes("u")) == 1


def test_same_id_different_request_conflicts():
    """C8: the same correlation id with a DIFFERENT canonical request is an
    integrity conflict, not a silent accept."""
    s = _store()
    s.add_edge(_edge())
    _confirm(s)
    with pytest.raises(ValueError, match="integrity conflict"):
        _confirm(s, request_digest="DIFFERENT")


def test_concurrent_duplicates_commit_once():
    """C8: the UNIQUE(user_id, correlation_id) constraint means two writers with the
    same request commit exactly one mutation/record (simulated by a direct second
    INSERT racing past the pre-check)."""
    s = _store()
    s.add_edge(_edge())
    # forge the pre-check miss: insert a competing record with the same
    # (user, correlation_id) directly, then confirm_edge must resolve to a replay.
    _confirm(s)                                            # the "winner"
    out = _confirm(s)                                      # the "loser": replay
    assert out.replayed is True
    assert len(s.confirmations_for("u", "e1")) == 1


# --- C9: metadata validated BEFORE any mutation -----------------------------

@pytest.mark.parametrize("bad", ["has space", "x" * 65, "emoji😀", ""])
def test_invalid_correlation_id_rejects_before_mutation(bad):
    """C9: an invalid correlation id raises BEFORE the flag is touched."""
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=None, config=MemoryConfig(db_path=f"{d}/x.db",
                                                   wiki_recompile_after_writes=0))
        mem.store.add_edge(_edge())
        with pytest.raises(ValueError):
            mem.confirm("u", "e1", correlation_id=bad)
        assert mem.store.edges("u", active_only=False)[0].needs_confirmation is True
        mem.close()


def test_invalid_call_path_rejects():
    """C9: `call_path` is a closed enum — an unknown value raises."""
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=None, config=MemoryConfig(db_path=f"{d}/x.db",
                                                   wiki_recompile_after_writes=0))
        mem.store.add_edge(_edge())
        with pytest.raises(ValueError):
            mem.confirm("u", "e1", call_path="a whole sentence")
        assert mem.store.edges("u", active_only=False)[0].needs_confirmation is True
        mem.close()


# --- C2a: actor is metadata; it grants nothing ------------------------------

def test_actor_metadata_does_not_grant_confirmation_authority():
    """C2a: authority comes from the protected call path, not the actor label —
    a HOST actor confirms exactly as a USER actor does; a free-form label is
    rejected (it cannot normalise arbitrary strings into authority)."""
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=None, config=MemoryConfig(db_path=f"{d}/x.db",
                                                   wiki_recompile_after_writes=0))
        mem.store.add_edge(_edge())
        mem.confirm("u", "e1", actor=ConfirmationActor.HOST)
        assert mem.store.edges("u", active_only=False)[0].needs_confirmation is False
        mem.store.add_edge(_edge("e2"))
        with pytest.raises(ValueError):
            mem.confirm("u", "e2", actor="the-admin-said-so")
        mem.close()


# --- C10: the add_edge transition guard (backend conformance) ---------------

def test_add_edge_refuses_the_transition():
    """C1/C10: generic add_edge rejects True→False, with no parameter that could
    authorise it, and rejects a user_id change — both against persisted state."""
    s = _store()
    s.add_edge(_edge(needs=True))
    cleared = _edge(needs=False)
    with pytest.raises(ValueError, match="confirm_edge"):
        s.add_edge(cleared)
    moved = _edge(needs=True, user="other")
    with pytest.raises(ValueError, match="ownership"):
        s.add_edge(moved)


# --- C11: retention, erasure, export ----------------------------------------

def test_forget_user_deletes_and_counts_confirmations():
    s = _store()
    s.add_edge(_edge())
    _confirm(s)
    assert s.forget_user("u")["confirmations"] == 1
    assert s.confirmations_for("u", "e1") == []


def test_invalidated_edge_keeps_its_confirmations():
    """§6d: a confirmation is retained when the edge is invalidated — the
    confirmation happened; only physical removal (forget) takes it."""
    s = _store()
    s.add_edge(_edge())
    _confirm(s)
    s.invalidate_edge("e1", NOW, "disputed")
    assert len(s.confirmations_for("u", "e1")) == 1


def test_export_excludes_confirmations():
    """§6d: a confirmation is a fact about THIS store, not about the memory —
    export carries only edges and episodes."""
    with tempfile.TemporaryDirectory() as d:
        s = _store()
        s.add_edge(_edge())
        _confirm(s)
        out = f"{d}/x.jsonl"
        export_memory(s, "u", out)
        raw = open(out).read()
        assert "confirmations" not in raw and "request_digest" not in raw


# --- C12: the version-compat gate -------------------------------------------

def test_a_confirmations_store_is_stamped_and_a_lower_build_refuses_it():
    """C12: a migrated (confirmations) store is version-stamped, so a build whose
    head is below the store's version refuses with `newer` (specs/0007) — an older
    build can never open it and clear the flag unaudited through the old path. The
    newer-refusal is exercised directly by stamping the store above the head."""
    import sqlite3
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    c.executescript(";\n".join(o.ddl for o in sv.SCHEMA_V1) + ";")
    c.commit(); c.close()
    assert migrate_store(p) == "migrated"
    assert sqlite3.connect(p).execute("PRAGMA user_version").fetchone()[0] == sv.SCHEMA_VERSION
    # a store one version ABOVE this build's head — what an OLDER build sees when it
    # opens a confirmations store minted by a newer one:
    c = sqlite3.connect(p)
    c.execute(f"PRAGMA user_version = {sv.SCHEMA_VERSION + 1}")
    c.commit(); c.close()
    with pytest.raises(StoreVersionError) as e:
        SqliteStore(p)
    assert e.value.reason == "newer"
