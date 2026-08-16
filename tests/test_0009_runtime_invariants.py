"""specs/0009 §6 runtime invariants — H2, H3, H6–H11.

The append-only *chain* is tested in test_outcomes.py and the import/migration
boundaries in test_0009_import_migration.py; this file covers the RUNTIME
primitive and the `record_outcome` surface built on it: seq-decides-the-head,
the atomic CAS under concurrency, derived aggregates, structural queryability,
the outcome-only field rules, the draft contract, the
store_version bump, and the preserved public surface incl. the HeadMoved retry.
Each test carries the exact name §6 names it (the name is the claim)."""
import json
import tempfile
import threading
from datetime import datetime, timezone

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium.schema import Edge, Episode, Outcome, OutcomeJudgmentDraft, Provenance
from veracium.store.base import HEAD_MOVED
from veracium.store.sqlite import SqliteStore

JAN = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _edge(eid="e1", uid="u"):
    return Edge(id=eid, user_id=uid, subject="user", relation="prefers", object="o",
                valid_from=JAN, active=True,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=eid, observed_at=JAN))


def _draft(author=EvidenceAuthor.SYSTEM, outcome=Outcome.CONCURRED,
           ts="2026-01-01", summary="j", context_ref=None):
    return OutcomeJudgmentDraft(author=author, event_timestamp=ts, outcome=outcome,
                               summary=summary, context_ref=context_ref)


def _store(tmp_path, name="s.db", edge=True):
    s = SqliteStore(str(tmp_path / name))
    if edge:
        s.add_edge(_edge("e1"))
    return s


def _mem(d, store=None):
    mem = Memory(llm=lambda *a, **k: "ok", store=store,
                 config=MemoryConfig(db_path=f"{d}/m.db",
                                     wiki_recompile_after_writes=0))
    e = _edge("e1")
    mem.store.add_edge(e)
    return mem, e


def _outcomes(store, uid="u"):
    return [ep for ep in store.episodes(uid) if ep.kind == "outcome"]


# --- H2: seq decides the head; a host date cannot reorder -------------------

def test_a_backdated_judgment_does_not_become_the_head(tmp_path):
    s = _store(tmp_path)
    root = s.append_outcome_if_head("u", "e1", "run-1", None,
                                    _draft(ts="2026-07-10", summary="first"))
    # a LATER append carrying an EARLIER date — seq (2) still makes it the head
    child = s.append_outcome_if_head("u", "e1", "run-1", root.id,
                                     _draft(author=EvidenceAuthor.USER,
                                            outcome=Outcome.CONFIRMED,
                                            ts="2026-07-01", summary="backdated"))
    head = s._chain_head("u", "e1", "run-1")
    assert head.id == child.id and head.seq == 2
    assert head.date < root.date, "the head's date is earlier — seq, not date, ordered it"


# --- H3: exactly one head — enforced AT the Store primitive under concurrency ---

def test_append_outcome_if_head_is_atomic(tmp_path):
    s = _store(tmp_path)
    N = 8
    errors = []

    def worker(i):
        try:
            while True:
                # the head READ shares the store's single connection, so it holds the
                # same lock the primitive does; the append then re-checks under the
                # lock — a stale expected loses the CAS (HEAD_MOVED) and retries.
                with s._lock:
                    head = s._chain_head("u", "e1", "run-1")
                    expected = head.id if head else None
                res = s.append_outcome_if_head(
                    "u", "e1", "run-1", expected, _draft(summary=f"j{i}"))
                if res is not HEAD_MOVED:
                    break
        except Exception as exc:            # pragma: no cover - surfaced via errors
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors
    outs = _outcomes(s)
    # N concurrent callers → a single linear chain, seqs 1..N, exactly one leaf
    assert sorted(ep.seq for ep in outs) == list(range(1, N + 1))
    referenced = {o.supersedes_episode for o in outs}
    leaves = [o for o in outs if o.id not in referenced]
    assert len(leaves) == 1, "concurrent appends branched the chain"


# --- H6: the authoritative aggregates follow heads --------------------------

def test_edge_aggregates_follow_heads(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        # use r1, upgraded to confirmed; a separate use r2 stays unreviewed
        mem.record_outcome("u", "e1", outcome="unreviewed", evidence_ref="r1")
        mem.record_outcome("u", "e1", outcome="confirmed", actor="user",
                           evidence_ref="r1")
        mem.record_outcome("u", "e1", outcome="unreviewed", evidence_ref="r2")
        e = mem.store.edges("u")[0]
        assert e.times_used == 2, "two distinct uses, not four episodes"
        assert e.outcome_counts.get("confirmed") == 1
        assert e.outcome_counts.get("unreviewed") == 1
        assert not e.outcome_counts.get("challenged")


# --- H7: history is structurally queryable, not prose -----------------------

def test_prior_authorship_is_queryable_without_parsing_a_summary(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        mem.record_outcome("u", "e1", outcome="concurred", actor="system",
                           evidence_ref="r")
        mem.record_outcome("u", "e1", outcome="confirmed", actor="user",
                           evidence_ref="r")
        outs = sorted(_outcomes(mem.store), key=lambda e: e.seq)
        # authorship is a FIELD on each link — a prose-only fix would leave len==1
        assert len(outs) == 2
        assert outs[0].provenance.author_of_evidence is EvidenceAuthor.SYSTEM
        assert outs[1].provenance.author_of_evidence is EvidenceAuthor.USER
        assert outs[0].outcome is Outcome.CONCURRED


# --- H8: seq/supersedes_episode are outcome-only; jtk explicit + state-space --

def test_non_outcome_episode_has_no_seq(tmp_path):
    s = _store(tmp_path, edge=False)
    s.add_episode(Episode(
        id="x", user_id="u", date="2026-01-01", summary="s",
        provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                              evidence_ref="r")))
    got = s.episodes("u")[0]
    assert got.kind != "outcome"
    assert got.seq is None and got.supersedes_episode is None
    assert got.judgment_time_known is None


def test_root_outcome_is_seq_1(tmp_path):
    s = _store(tmp_path)
    root = s.append_outcome_if_head("u", "e1", "run-1", None, _draft())
    assert root.seq == 1 and root.supersedes_episode is None
    assert root.judgment_time_known is True


def _write_v3(path, ep_extra, uid="u"):
    with open(path, "w") as f:
        f.write(json.dumps({"kind": "veracium-export", "version": 3,
                            "user_id": uid, "exported_at": "x"}) + "\n")
        f.write(json.dumps({"record": "edge",
                            **json.loads(_edge("e1").model_dump_json())}) + "\n")
        base = {"id": "o", "user_id": uid, "date": "2026-01-01", "summary": "s",
                "kind": "outcome", "edge_id": "e1", "outcome": "concurred",
                "provenance": {"author_of_evidence": "system", "evidence_ref": "r"}}
        base.update(ep_extra)
        f.write(json.dumps({"record": "episode", **base}) + "\n")


def test_v3_outcome_omitting_judgment_time_known_is_refused(tmp_path):
    from veracium.portability import import_memory
    p = str(tmp_path / "v3.jsonl")
    _write_v3(p, {"seq": 1, "supersedes_episode": None})   # jtk omitted
    with pytest.raises(ValueError, match="judgment_time_known"):
        import_memory(_store(tmp_path, "dst.db", edge=False), p)


def test_non_root_with_unknown_time_is_refused(tmp_path):
    from veracium.portability import import_memory
    p = str(tmp_path / "v3.jsonl")
    # judgment_time_known False is a legacy-ROOT-only state; non-root → refuse
    _write_v3(p, {"seq": 2, "supersedes_episode": "prev",
                  "judgment_time_known": False})
    with pytest.raises(ValueError, match="not a root"):
        import_memory(_store(tmp_path, "dst.db", edge=False), p)


# --- H9: the CAS draft excludes store-owned fields; primitive derives source ---

def test_outcome_draft_has_no_store_owned_fields():
    fields = set(OutcomeJudgmentDraft.model_fields)
    for banned in ("id", "seq", "supersedes_episode"):
        assert banned not in fields, f"draft must not carry store-owned {banned!r}"


def test_corrected_value_survives_the_store_boundary(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        mem.record_outcome("u", "e1", outcome="corrected", actor="user",
                           corrected_value="spam", evidence_ref="r")
        head = mem._outcome_head("u", "e1", "r")
        assert head.outcome is Outcome.CORRECTED and "spam" in head.summary


def test_append_carries_the_draft_author(tmp_path):
    """specs/0016 D2 reshaped: the derived `source_type` is deleted; what the
    primitive still owes the chain is the draft's author, faithfully."""
    s = _store(tmp_path)
    sys_ep = s.append_outcome_if_head("u", "e1", "rs", None,
                                      _draft(author=EvidenceAuthor.SYSTEM))
    usr_ep = s.append_outcome_if_head("u", "e1", "ru", None,
                                      _draft(author=EvidenceAuthor.USER,
                                             outcome=Outcome.CONFIRMED))
    assert sys_ep.provenance.author_of_evidence is EvidenceAuthor.SYSTEM
    assert usr_ep.provenance.author_of_evidence is EvidenceAuthor.USER


# --- H10: append advances store_version in the same atomic transaction -------

def test_append_outcome_bumps_store_version(tmp_path):
    s = _store(tmp_path)
    v0 = s.store_version("u")
    s.append_outcome_if_head("u", "e1", "run-1", None, _draft())
    assert s.store_version("u") > v0, "a cached wiki must read stale after an append"


# --- H11: the public record_outcome surface is preserved --------------------

def test_challenged_sets_needs_confirmation(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        mem.record_outcome("u", "e1", outcome="challenged", actor="system",
                           evidence_ref="r")
        assert mem.store.edges("u")[0].needs_confirmation


def test_actor_outcome_pairing_still_raises(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        with pytest.raises(ValueError, match="human judgment"):
            mem.record_outcome("u", "e1", outcome="confirmed", actor="system",
                               evidence_ref="x")
        with pytest.raises(ValueError, match="system judgment"):
            mem.record_outcome("u", "e1", outcome="challenged", actor="user",
                               evidence_ref="y")


def test_corrected_value_persisted(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        mem.record_outcome("u", "e1", outcome="corrected", actor="user",
                           corrected_value="spam", evidence_ref="r")
        head = mem._outcome_head("u", "e1", "r")
        assert head.outcome is Outcome.CORRECTED and "spam" in head.summary


def test_omitted_context_ref_inherits_not_rejects(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        mem.record_outcome("u", "e1", outcome="unreviewed", evidence_ref="r",
                           context_ref="ctx-A")
        mem.record_outcome("u", "e1", outcome="confirmed", actor="user",
                           evidence_ref="r")           # context_ref omitted
        head = mem._outcome_head("u", "e1", "r")
        assert head.context_ref == "ctx-A", "an omitted context_ref must inherit"


def test_return_upgraded_and_times_used(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        r1 = mem.record_outcome("u", "e1", outcome="unreviewed", evidence_ref="r")
        assert r1["upgraded"] is False and r1["times_used"] == 1
        r2 = mem.record_outcome("u", "e1", outcome="confirmed", actor="user",
                                evidence_ref="r")
        assert r2["upgraded"] is True and r2["times_used"] == 1


def test_late_judgment_on_superseded_edge_is_recorded(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem, edge = _mem(d)
        mem.record_outcome("u", "e1", outcome="unreviewed", evidence_ref="r")
        mem.correct("u", "e1", "new value", date="2026-07-03")
        r = mem.record_outcome("u", "e1", outcome="challenged", actor="system",
                               evidence_ref="r", date="2026-07-04")
        assert r["upgraded"]
        assert any(o.outcome is Outcome.CHALLENGED for o in _outcomes(mem.store))


def test_headmoved_retry_reports_upgraded_and_rebuilds_summary(tmp_path):
    # A no-head-then-HeadMoved winner: record_outcome sees no head, but a concurrent
    # SYSTEM judgment lands first; the retry must report upgraded=True and rebuild the
    # predecessor-dependent prose against the NEW (system) head (round-5 Correction A).
    class RacingStore(SqliteStore):
        _fired = False

        def append_outcome_if_head(self, user_id, edge_id, evref, expected, draft):
            if not self._fired and expected is None:
                self._fired = True
                super().append_outcome_if_head(
                    user_id, edge_id, evref, None,
                    _draft(author=EvidenceAuthor.SYSTEM, outcome=Outcome.CONCURRED,
                           summary="concurrent-system"))
                return HEAD_MOVED
            return super().append_outcome_if_head(
                user_id, edge_id, evref, expected, draft)

    with tempfile.TemporaryDirectory() as d:
        store = RacingStore(f"{d}/m.db")
        mem, edge = _mem(d, store=store)
        r = mem.record_outcome("u", "e1", outcome="confirmed", actor="user",
                               evidence_ref="r")
        assert r["upgraded"] is True, "the retry saw a head, so this is an upgrade"
        head = mem._outcome_head("u", "e1", "r")
        assert head.outcome is Outcome.CONFIRMED
        assert "prior judgment was system-authored" in head.summary, \
            "prose must be rebuilt against the winning (system) head"
