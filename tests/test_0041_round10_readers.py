"""specs/0041 round 10 — P-READ: every reader and every derivation of stored content excludes ATTESTED targets at
its read, by the attestation record (round-9 R9-07; sweep E's proactive and expire; sweep A's compile return path).

Interleavings are deterministic hooks into a SECOND `Memory` on the same database file. Every exclusion cell has a
control that shows the same instrument sees the record when it is not redacted.
"""
import contextlib
import importlib.util
import json
import pathlib
import sys
from datetime import date, datetime, timedelta, timezone

import pytest

from veracium import Memory, budgets, redaction as R
from veracium.compile import compile_wiki
from veracium.config import MemoryConfig
from veracium.schema import DEFAULT_RELATIONS, Disclosure, Edge, Episode, EvidenceAuthor, Provenance, Volatility

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("tt41_r10rd", ROOT / "tests" / "test_0041_transition_table.py")
tt = importlib.util.module_from_spec(_spec)
sys.modules["tt41_r10rd"] = tt
_spec.loader.exec_module(tt)

U = "u"
SECRET = "SECRET-READER-4471"
OLD = datetime.now(timezone.utc) - timedelta(days=3000)
# the UTC date, as `Episode.valid_now` compares it: a local `date.today()` made `ep-1` future-dated wherever the local
# date is ahead of UTC (the 0048 round-1 reviewer's R1-05, reproduced under Australia/Brisbane)
TODAY = datetime.now(timezone.utc).date().isoformat()


def _prov(**kw):
    base = dict(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev", disclosure=Disclosure.MENTIONABLE)
    base.update(kw)
    return Provenance(**base)


class _Emb:
    def __init__(self, on_call=None):
        self.seen, self.on_call = [], on_call

    def id(self):
        return "rec@1"

    def dim(self):
        return 3

    def __call__(self, texts):
        self.seen.extend(texts)
        if self.on_call:
            self.on_call(); self.on_call = None
        return [[1.0, float(len(x)), 0.5] for x in texts]


def _cfg(tmp_path, name="r.db"):
    return MemoryConfig(db_path=str(tmp_path / name), wiki_recompile_after_writes=0, scope_groups={},
                        require_source_id=False)


def _vectors(st, eid):
    return st._conn.execute("SELECT COUNT(*) FROM edge_embedding WHERE edge_id=?", (eid,)).fetchone()[0]


# ------------------------------------------------------------------------------------------------ R9-07 backfill
def test_R9_07_an_attested_edge_is_skipped_and_its_tombstone_never_reaches_the_embedder(tmp_path):
    emb = _Emb()
    m = Memory(llm=tt._quiet, embed=emb, config=_cfg(tmp_path))
    m.store.add_edge(Edge(id="e-7", user_id=U, subject="user", relation="works_as", object=SECRET, provenance=_prov()))
    assert m.embed_backfill(U) == 1 and _vectors(m.store, "e-7") == 1          # control: an ordinary edge embeds
    m.redact(U, edge_id="e-7", reason="subject_request")
    assert _vectors(m.store, "e-7") == 0
    emb.seen.clear()
    assert m.embed_backfill(U) == 0 and _vectors(m.store, "e-7") == 0
    assert not any(R.MARKER in t for t in emb.seen)


def test_R9_07_an_unattested_marker_row_follows_its_own_contract_and_is_embedded(tmp_path):
    m = tt._frozen_memory(tmp_path)
    eid = tt._frozen_rows()["unattested_marker"]
    emb = _Emb()
    m2 = Memory(llm=tt._quiet, embed=emb, config=MemoryConfig(db_path=m.config.db_path, wiki_recompile_after_writes=0,
                                                             scope_groups={}, require_source_id=False))
    assert not m2.store._attested_fields(U, "edge", eid)
    m2.embed_backfill(U)
    assert _vectors(m2.store, eid) == 1


def test_R9_07_a_redaction_during_the_embed_call_is_refused_by_the_digest_guard_at_the_upsert(tmp_path):
    """The concurrent case: the read passed the filter, the redaction lands while the embedder runs, and the
    digest-conditional upsert REFUSES the attempted write (observed as its return value, not inferred from absence)."""
    b = Memory(llm=tt._quiet, config=_cfg(tmp_path))
    a = Memory(llm=tt._quiet, embed=_Emb(on_call=lambda: b.redact(U, edge_id="e-7", reason="subject_request")),
               config=_cfg(tmp_path))
    a.store.add_edge(Edge(id="e-7", user_id=U, subject="user", relation="works_as", object=SECRET, provenance=_prov()))
    real, attempts = a.store.upsert_embedding, []

    def recording(**kw):
        ok = real(**kw); attempts.append((kw["edge_id"], ok)); return ok
    a.store.upsert_embedding = recording
    assert a.embed_backfill(U) == 0
    assert attempts == [("e-7", False)] and _vectors(a.store, "e-7") == 0


# ------------------------------------------------------------------------------------------------ E expire
def _aged(m, eid, obj, **kw):
    m.store.add_edge(Edge(id=eid, user_id=U, subject="user", relation=kw.pop("relation", "works_as"), object=obj,
                          volatility=Volatility.SLOW, provenance=_prov(observed_at=OLD), **kw))


def _flags(st):
    return {e.id: e.needs_confirmation for e in st.edges(U, active_only=False)}


def test_E_expire_a_redacted_aged_edge_is_skipped_and_maintain_returns_and_expires_the_rest(tmp_path):
    m = tt._mem(tmp_path)
    _aged(m, "e-1", SECRET)
    _aged(m, "e-2", "tea", relation="likes")
    m.redact(U, edge_id="e-1", reason="subject_request")
    report = m.maintain(U, consolidate=False)                                   # RETURNS
    assert report["expiry"]["flagged_for_confirmation"] == 1
    assert _flags(m.store) == {"e-1": False, "e-2": True}                      # the control edge WAS processed


def test_E_expire_a_redaction_landing_between_the_read_and_the_write_back_is_skipped_not_raised(tmp_path):
    a, b = tt._mem(tmp_path, "g.db"), tt._mem(tmp_path, "g.db")
    _aged(a, "e-1", SECRET)
    _aged(a, "e-2", "tea", relation="likes")
    real, done = a.store.edges, []

    def hooked(*k, **kw):
        got = real(*k, **kw)
        if not done:
            done.append(b.redact(U, edge_id="e-1", reason="subject_request"))
        return got
    a.store.edges = hooked
    report = a.maintain(U, consolidate=False)
    a.store.edges = real
    assert done and report["expiry"]["flagged_for_confirmation"] == 1
    assert _flags(a.store)["e-2"] is True


def test_E_expire_control_an_unredacted_aged_edge_still_expires(tmp_path):
    m = tt._mem(tmp_path)
    _aged(m, "e-1", "Porto")
    assert m.maintain(U, consolidate=False)["expiry"]["flagged_for_confirmation"] == 1


def test_E_expire_any_other_refusal_still_raises(tmp_path, monkeypatch):
    """The skip is decided by a FRESH attestation read: a write-back refused for another reason is not swallowed.
    specs/0048 §4D moved expiry's write into the store's transition (`expiry_transition`), which writes through
    `_upsert_edge_row`, the body `add_edge` wraps, so the refusal is injected there; the 0041 skip itself now lives
    inside that transaction and no `except ValueError` remains to swallow anything (test_0048_decay_bounds.py::
    test_an_unrelated_write_refusal_inside_the_transition_still_raises holds the same property on its own fixture)."""
    m = tt._mem(tmp_path)
    _aged(m, "e-1", "Porto")

    def refuse(_e):
        raise ValueError("refused for an unrelated reason")
    monkeypatch.setattr(m.store, "_upsert_edge_row", refuse)
    with pytest.raises(ValueError, match="unrelated"):
        m.maintain(U, consolidate=False)


# ------------------------------------------------------------------------------------------------ E proactive
def _four_sections(m):
    m.store.add_edge(Edge(id="e-cur", user_id=U, subject="user", relation="mood", object="tired " + SECRET,
                          volatility=Volatility.TRANSIENT, provenance=_prov()))
    m.store.add_edge(Edge(id="e-conf", user_id=U, subject="user", relation="works_as", object="Acme " + SECRET,
                          needs_confirmation=True, provenance=_prov()))
    m.store.add_edge(Edge(id="e-due", user_id=U, subject="user", relation="plans",
                          object=f"submit the form by {TODAY} " + SECRET, provenance=_prov()))
    m.store.add_episode(Episode(id="ep-1", user_id=U, date=TODAY, summary="ep " + SECRET, provenance=_prov()))
    return ["e-conf", "e-cur", "e-due", "ep-1"]


def _returned(r):
    return sorted([e.id for e in r.edges] + [e.id for e in r.episodes])


def test_E_proactive_control_all_four_sections_surface_their_records(tmp_path):
    m = tt._mem(tmp_path)
    ids = _four_sections(m)
    r = m.recall(U)
    assert _returned(r) == ids and SECRET in r.context


def test_E_proactive_a_redacted_record_in_any_section_is_not_returned(tmp_path):
    m = tt._mem(tmp_path)
    ids = _four_sections(m)
    for i in ids:
        m.redact(U, **({"episode_id": i} if i.startswith("ep") else {"edge_id": i}), reason="subject_request")
    r = m.recall(U)
    assert _returned(r) == [] and R.MARKER not in r.context and SECRET not in r.context


def test_E_proactive_the_dated_section_excludes_BY_THE_FILTER_with_the_date_left_intact(tmp_path, monkeypatch):
    """A treatment that leaves `object` (and so its date) intact isolates the filter: the record is attested, its date
    still parses, and it must still not be returned — the exclusion is the read's, not the marker's."""
    m = tt._mem(tmp_path)
    _four_sections(m)
    monkeypatch.setattr(R, "EDGE_REPLACE", tuple(f for f in R.EDGE_REPLACE if f != "object"))
    m.redact(U, edge_id="e-due", reason="subject_request")
    row = json.loads(m.store._conn.execute("SELECT json FROM edges WHERE id='e-due'").fetchone()[0])
    assert TODAY in row["object"] and m.store._attested_fields(U, "edge", "e-due")     # the date is intact
    assert "e-due" not in _returned(m.recall(U))


# ------------------------------------------------------------------------------------------------ A5 compile
def _compile(tmp_path, on_calls):
    a, b = tt._mem(tmp_path, "w.db"), tt._mem(tmp_path, "w.db")
    a.store.add_edge(Edge(id="e-1", user_id=U, subject="user", relation="lives_at", object=SECRET, provenance=_prov()))
    a.store.add_edge(Edge(id="e-2", user_id=U, subject="user", relation="likes", object="green tea", provenance=_prov()))
    calls = []

    def llm(prompt, system=None, role=None):
        calls.append(prompt)
        act = on_calls.get(len(calls))
        if act:
            act(b)
        return "WIKI " + prompt
    body = compile_wiki(a.store, llm, U, DEFAULT_RELATIONS)
    cached = a.store._conn.execute("SELECT text FROM wiki WHERE user_id=?", (U,)).fetchone()
    return body, cached, calls


def test_A5_a_redaction_during_the_compile_is_recompiled_once_and_the_body_never_carries_it(tmp_path):
    body, cached, calls = _compile(tmp_path, {1: lambda b: b.redact(U, edge_id="e-1", reason="subject_request")})
    assert len(calls) == 2 and SECRET in calls[0] and SECRET not in calls[1]
    assert SECRET not in body and "green tea" in body
    assert cached is not None and SECRET not in cached[0]                         # the recompile published


def test_A5_a_second_redaction_in_the_recompile_returns_the_closed_notice_and_does_not_loop(tmp_path):
    body, cached, calls = _compile(tmp_path, {
        1: lambda b: b.redact(U, edge_id="e-1", reason="subject_request"),
        2: lambda b: b.redact(U, edge_id="e-2", reason="subject_request")})
    assert len(calls) == 2                                                        # one recompile, never a loop
    assert body == budgets.REDACTED_DURING_COMPILE_NOTICE and cached is None
    assert SECRET not in body and "green tea" not in body


def test_A5_control_a_plain_concurrent_write_keeps_the_returned_body(tmp_path):
    body, cached, calls = _compile(tmp_path, {1: lambda b: b.store.add_edge(Edge(
        id="e-3", user_id=U, subject="user", relation="likes", object="coffee", provenance=_prov()))})
    assert len(calls) == 1 and cached is None and SECRET in body                  # today's behaviour, unchanged


def test_A5_control_no_interference_publishes(tmp_path):
    body, cached, calls = _compile(tmp_path, {})
    assert len(calls) == 1 and cached is not None and SECRET in body
