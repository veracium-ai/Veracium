"""specs/0029 v12 (the reinstatement-reason fold, amendment 0044/0029-reinstated-reason; INV-J1–J3): a `reinstated`
event carries WHY the edge came back, from the closed REINSTATEMENT_REASONS, validated at the emission choke point.

The four implementation gates 0029 §6 names: V-REINSTATE-REASON, -LEGACY, -WRITERS, -VERBATIM. Exercised through the
REAL writer (0022's revocation lift, `_reinstate_edge_row`), never a model.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sqlite3
import uuid

import pytest

from veracium import EvidenceAuthor, SqliteStore
from veracium import why as _why
from veracium.schema import Edge, Episode, Provenance
from veracium.store import revocation as rv
from veracium.store import sqlite as _sqlite_mod
from veracium.store.base import LEGACY_REINSTATEMENT_REASON, REINSTATEMENT_REASONS
from veracium.store.revocation_sweep import digest_of

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
U = "u"
AT = "2026-08-21T00:00:00Z"


def _store(tmp_path):
    return SqliteStore(str(tmp_path / "rr.db"))


def _seed(s, source_id="feed-1"):
    prov = lambda: Provenance(author_of_evidence=EvidenceAuthor.THIRD_PARTY,                      # noqa: E731
                              evidence_ref=f"ev-{uuid.uuid4().hex[:6]}", source_id=source_id)
    s.add_edge(Edge(id="e1", user_id=U, subject="user", relation="located_at", object="Lisbon", provenance=prov()))
    s.add_episode(Episode(id="ep1", user_id=U, date="2026-08-01", summary="the feed said Lisbon", provenance=prov()))
    return digest_of(None, source_id, s.local_origin())


def _events(s, kind=None):
    return [e for e in s.edge_events(U, edge_id="e1") if kind is None or e.kind == kind]


def _revoked_then_lifted(tmp_path):
    s = _store(tmp_path)
    d = _seed(s)
    rv.revoke_source(s, U, d, "revoke", "policy", AT)
    rv.revoke_source(s, U, d, "lift", "policy", AT)
    return s, d


def test_reinstated_reason_is_closed_and_an_invalid_one_unwinds_the_write(tmp_path, monkeypatch):
    """INV-J1 (and 0044's INV-A18, which carries 0029 v12's closed reason). The real lift journals `source_restored`. A reason outside the vocabulary — and NULL on a new write — is
    refused at the choke point, and the WHOLE transaction unwinds: the row's reinstatement does not persist either.
    Mutants: accept any reason; accept NULL on a new write; refuse but commit the row."""
    assert REINSTATEMENT_REASONS == ("source_restored", "arity_reclassified")
    s, _d = _revoked_then_lifted(tmp_path)
    assert [e.reason for e in _events(s, "reinstated")] == ["source_restored"]
    assert s.edges(U)[0].active

    for name, force in (("a reason outside the vocabulary", "not_a_reason"), ("NULL on a new write", None)):
        sub = tmp_path / name.replace(" ", "_"); sub.mkdir()
        s2 = _store(sub)
        d2 = _seed(s2)
        rv.revoke_source(s2, U, d2, "revoke", "policy", AT)
        real = _sqlite_mod.SqliteStore._journal_edge_write

        def forced(self, user_id, edge_id, new_json, prior_json, *, kind=None, reason=None, _force=force):
            return real(self, user_id, edge_id, new_json, prior_json, kind=kind,
                        reason=_force if kind == "reinstated" else reason)

        monkeypatch.setattr(_sqlite_mod.SqliteStore, "_journal_edge_write", forced)
        with pytest.raises(Exception):
            rv.revoke_source(s2, U, d2, "lift", "policy", AT)
        monkeypatch.setattr(_sqlite_mod.SqliteStore, "_journal_edge_write", real)
        e = s2.edges(U, active_only=False)[0]
        assert not e.active and e.invalidation_reason == "revoked_source", f"{name}: the row's reinstatement persisted"
        assert not [ev for ev in s2.edge_events(U, edge_id="e1") if ev.kind == "reinstated"], (
            f"{name}: a reinstated event was written")


def test_pre_v12_null_reinstatement_reads_source_restored_and_is_not_rewritten(tmp_path):
    """INV-J2. A `reinstated` event written before v12 carries NULL: `why` (the one renderer of an event's reason)
    reads it as `source_restored`, and the stored row stays NULL, byte for byte. Mutants: rewrite old events; read
    NULL as unknown."""
    s, _d = _revoked_then_lifted(tmp_path)
    path = str(tmp_path / "rr.db")
    c = sqlite3.connect(path)
    c.execute("UPDATE edge_event SET reason=NULL WHERE kind='reinstated'")          # the pre-v12 shape
    c.commit()
    before = c.execute("SELECT * FROM edge_event WHERE kind='reinstated'").fetchall()
    c.close()
    s2 = SqliteStore(path)
    bio = _why.gather(s2, U, "e1")
    got = [e["reason"] for e in bio.events if e["kind"] == "reinstated"]
    assert got == [LEGACY_REINSTATEMENT_REASON] == ["source_restored"]
    assert "(source_restored)" in _why.render(bio)
    c = sqlite3.connect(path)
    assert c.execute("SELECT * FROM edge_event WHERE kind='reinstated'").fetchall() == before, "an old event was rewritten"
    c.close()


def test_reinstatement_reason_leaves_reconstruction_verbatim(tmp_path):
    """V-REINSTATE-VERBATIM. The reason is a COLUMN: the `state` payload and `edge_state_at`'s reconstruction are
    byte-identical whether the event carries `source_restored` or (pre-v12) NULL. Mutant: write the reason into the
    state payload."""
    s, _d = _revoked_then_lifted(tmp_path)
    ev = _events(s, "reinstated")[0]
    assert "source_restored" not in ev.state and "arity_reclassified" not in ev.state
    with_reason = [s.edge_state_at(U, "e1", e.txn) for e in _events(s)]
    path = str(tmp_path / "rr.db")
    c = sqlite3.connect(path)
    states_before = c.execute("SELECT seq, state FROM edge_event WHERE edge_id='e1' ORDER BY seq").fetchall()
    c.execute("UPDATE edge_event SET reason=NULL WHERE kind='reinstated'")
    c.commit()
    assert c.execute("SELECT seq, state FROM edge_event WHERE edge_id='e1' ORDER BY seq").fetchall() == states_before
    c.close()
    s2 = SqliteStore(path)
    assert [s2.edge_state_at(U, "e1", e.txn) for e in _events(s2)] == with_reason


# ---- V-REINSTATE-WRITERS (INV-J3): every writer of a `reinstated` event and every reader of an event's reason is
# CENSUSED from the source, never listed by hand; the rulings below are the review, and a new site with no ruling fails.

FORWARDER = ("store/sqlite.py", "SqliteStore._reinstate_edge_row")
# 0048 round 4 (R3-02, (a′)): the edges json is written, and its event journaled, through ONE site. Its two bodies
# PASS THROUGH their own `kind`/`reason` parameters to the choke point; the census reads the call sites that reach them
# (a `_write_edge_row(…)` or `emit(…)` call carrying `kind=`) exactly as it read `_journal_edge_write(…)` calls before.
PASS_THROUGH = {("store/sqlite.py", "SqliteStore._write_edge_row"), ("store/sqlite.py", "_DeferredJournal.emit")}
WRITER_RULINGS = {FORWARDER: "<forwarded to its censused callers>",
                  **{s: "<pass-through: kind and reason from the censused write sites>" for s in sorted(PASS_THROUGH)}}
# research's T6 stage-1 read, F1: the reinstate writer FORWARDS its `reason` (required, keyword-only, no default), so
# the census reads its CALLERS — each with a constant reason, ruled here; a non-constant or absent one is a finding.
# 0044's restoration is `arity_reclassified`'s ONE caller (0029 v12 §4b-i point 3): `convert_rows`, §4f's steps 2–4,
# which both `run_data_migration` and a converting import (0044 §4l, T11a) run.
CALLER_RULINGS = {("store/revocation.py", "_apply_statement_effect"): "source_restored",
                  ("store/data_migration.py", "convert_rows"): "arity_reclassified"}
APPEND_EVENT_CALLERS = {("store/sqlite.py", "SqliteStore._journal_edge_write"),     # THE choke point
                        ("store/edge_events.py", "journal_baselines")}              # the v13 baseline, reason NULL
READER_RULINGS = {
    ("why.py", "gather"): "renders it; a pre-v12 NULL on a reinstated event reads as source_restored",
    ("store/sqlite.py", "SqliteStore.edge_events"): "the read API: returns the column as stored",
    ("store/migration.py", "_baseline_problems"): "0013 §4f: checks a baseline event's reason is NULL",
    ("store/sqlite.py", "SqliteStore._quoting_domain"): "reads INVALIDATED events' reasons only (its SQL filters "
        "kind='invalidated'): a reinstated reason is ignored by construction",
}


def _qualnames(tree):
    out = {}
    def walk(node, prefix):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = f"{prefix}.{ch.name}" if prefix else ch.name
                for n in ast.walk(ch):
                    out[id(n)] = q                       # outer first; an inner definition overwrites
                walk(ch, q)
            else:
                walk(ch, prefix)
    walk(tree, "")
    return out


def census(sources: dict):
    """{rel path: source} -> (reinstated writers {(rel, qualname): reason}, append_event callers, reason readers,
    reinstate-writer callers {(rel, qualname): reason})."""
    writers, appenders, readers, callers = {}, set(), set(), {}
    for rel, text in sources.items():
        tree = ast.parse(text)
        q = _qualnames(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                name = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", None)
                kw = {k.arg: k.value for k in n.keywords}
                if name in ("_journal_edge_write", "_write_edge_row", "emit") and "kind" in kw:
                    k = kw["kind"]
                    site = (rel, q.get(id(n), "<module>"))
                    if (site in PASS_THROUGH and name == "_journal_edge_write" and isinstance(k, ast.Name)
                            and k.id == "kind" and isinstance(kw.get("reason"), ast.Name) and kw["reason"].id == "reason"):
                        writers[site] = "<pass-through: kind and reason from the censused write sites>"
                    elif not isinstance(k, ast.Constant):
                        writers[(rel, q.get(id(n), "<module>"))] = "<non-constant kind>"
                    elif k.value == "reinstated":
                        r = kw.get("reason")
                        site = (rel, q.get(id(n), "<module>"))
                        if isinstance(r, ast.Constant):
                            writers[site] = r.value
                        elif site == FORWARDER and isinstance(r, ast.Name) and r.id == "reason":
                            writers[site] = "<forwarded to its censused callers>"
                        else:
                            writers[site] = "<non-constant reason>"
                if name == "_reinstate_edge_row":
                    r = kw.get("reason")
                    callers[(rel, q.get(id(n), "<module>"))] = (
                        r.value if isinstance(r, ast.Constant) else
                        "<no reason>" if r is None else "<non-constant reason>")
                if name == "append_event":
                    appenders.add((rel, q.get(id(n), "<module>")))
                if name == "edge_events" and isinstance(n.func, ast.Attribute):
                    readers.add((rel, q.get(id(n), "<module>")))
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                low = n.value.lower()
                # SQL that reads the column: a SELECT naming `reason`, FROM edge_event (prose that mentions both is not)
                if "reason" in low and re.search(r"\bselect\b", low) and re.search(r"\bfrom\s+edge_event\b", low):
                    readers.add((rel, q.get(id(n), "<module>")))
    return writers, appenders, readers, callers


def _tree_sources():
    return {str(p.relative_to(SRC)): p.read_text() for p in sorted(SRC.rglob("*.py"))}


def test_every_reinstated_writer_and_reason_reader_is_censused():
    writers, appenders, readers, callers = census(_tree_sources())
    assert writers == WRITER_RULINGS, writers
    assert callers == CALLER_RULINGS, callers
    assert [s for s, r in callers.items() if r == "arity_reclassified"] == [("store/data_migration.py", "convert_rows")]
    assert appenders == APPEND_EVENT_CALLERS, appenders
    assert readers == set(READER_RULINGS), readers
    # the census is not vacuous: a new reinstating site, a swapped reason, and a new reader are each found
    src = _tree_sources()
    anchor = 'store._reinstate_edge_row(rid, reason="source_restored")'
    assert src["store/revocation.py"].count(anchor) == 1           # the plant below edits a real literal
    planted = dict(src)
    planted["store/revocation.py"] = src["store/revocation.py"].replace(
        anchor, 'store._reinstate_edge_row(rid, reason="arity_reclassified")', 1)
    assert census(planted)[3] != CALLER_RULINGS                    # a swapped caller reason
    planted = dict(src)
    planted["planted.py"] = ("def sneaky(store):\n    store._journal_edge_write('u', 'e', '{}', '{}', kind='reinstated',"
                             " reason='source_restored')\n    return store.edge_events('u')\n")
    w, _a, r, _c = census(planted)
    assert ("planted.py", "sneaky") in w and ("planted.py", "sneaky") in r
    # F1's vacuity controls: a second caller of the reserved reason, a non-constant caller, a reasonless caller, and
    # a forwarder outside the one ruled method are each found
    for body, want in (("store._reinstate_edge_row('e', reason='arity_reclassified')", "arity_reclassified"),
                       ("store._reinstate_edge_row('e', reason=why)", "<non-constant reason>"),
                       ("store._reinstate_edge_row('e')", "<no reason>")):
        planted = dict(src)
        planted["planted.py"] = f"def caller(store, why):\n    {body}\n"
        assert census(planted)[3].get(("planted.py", "caller")) == want, body
    planted = dict(src)
    planted["planted.py"] = ("def relay(store, reason):\n    store._journal_edge_write('u', 'e', '{}', '{}', "
                             "kind='reinstated', reason=reason)\n")
    assert census(planted)[0].get(("planted.py", "relay")) == "<non-constant reason>"
