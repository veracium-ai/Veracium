"""Lifecycle: expiry, reinforcement, consolidation (offline, time-controlled)."""

import json
import tempfile
from datetime import datetime, timezone

from veracium import Memory, MemoryConfig, EvidenceAuthor
from veracium import lifecycle


class Fake:
    def __init__(self, scripts):
        self._s = list(scripts); self.i = 0
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        out = self._s[self.i]; self.i += 1
        return out if isinstance(out, str) else json.dumps(out)


def _mem(d, scripts):
    return Memory(llm=Fake(scripts),
                  config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0))


def test_expiry_lapse_confirm_and_reinforcement():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [
            # transient illness + durable employer
            {"triples": [{"subject": "user", "relation": "health_state", "object": "flu", "volatility": "transient"},
                         {"subject": "user", "relation": "works_as", "object": "designer at Acme", "volatility": "durable"}],
             "episode": "User is sick with flu; works as a designer at Acme."},
        ])
        mem.remember("u", "USER: I've got the flu. I'm a designer at Acme.", date="2026-01-01")

        # 60 days later: transient flu should LAPSE, durable employer stays active
        now = datetime(2026, 3, 2, tzinfo=timezone.utc)
        rep = lifecycle.expire(mem.store, "u", mem.config, now=now)
        assert rep["lapsed"] == 1
        assert not any(e.object == "flu" for e in mem.store.edges("u"))          # gone (active)
        assert any(e.object == "flu" for e in mem.store.edges("u", active_only=False))  # retained
        assert any("designer at Acme" in e.object for e in mem.store.edges("u"))  # durable survives

        # 800 days later: durable employer past lifetime → flagged, not dropped
        now2 = datetime(2028, 3, 15, tzinfo=timezone.utc)
        rep2 = lifecycle.expire(mem.store, "u", mem.config, now=now2)
        assert rep2["flagged_for_confirmation"] == 1
        emp = [e for e in mem.store.edges("u") if "Acme" in e.object][0]
        assert emp.needs_confirmation and emp.active  # surfaced as stale, still present
        mem.close()


def test_reinforcement_refreshes_not_duplicates():
    with tempfile.TemporaryDirectory() as d:
        script = {"triples": [{"subject": "user", "relation": "health_state", "object": "flu", "volatility": "transient"}],
                  "episode": "still sick"}
        mem = _mem(d, [script, script])
        mem.remember("u", "sick", date="2026-01-01")
        mem.remember("u", "still sick", date="2026-01-05")  # re-stated → persisted (0012)
        active = sorted(mem.store.edges("u", relation="health_state"),
                        key=lambda e: e.provenance.observed_at)
        # specs/0012 Design 1: the restatement is its own edge with its own provenance;
        # the fact stays live THROUGH the new edge (each ages against its own observed_at),
        # and the first edge's first-known date is byte-untouched.
        assert len(active) == 2
        assert active[0].valid_from.date().isoformat() == "2026-01-01"
        assert active[0].provenance.observed_at.date().isoformat() == "2026-01-01"
        assert active[1].provenance.observed_at.date().isoformat() == "2026-01-05"
        mem.close()


def test_reinforcement_matches_paraphrased_values():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [
            {"triples": [{"subject": "user", "relation": "has_pet", "object": "dog named Ollie", "volatility": "durable"}],
             "episode": "has a dog named Ollie"},
            {"triples": [{"subject": "user", "relation": "has_pet", "object": "dog Ollie", "volatility": "durable"}],
             "episode": "mentioned the dog again"},
        ])
        mem.remember("u", "I have a dog named Ollie.", date="2026-01-01")
        mem.remember("u", "My dog Ollie is great.", date="2026-01-05")  # paraphrase matched
        active = sorted(mem.store.edges("u", relation="has_pet"),
                        key=lambda e: e.provenance.observed_at)
        # the paraphrase is RECOGNISED as the same value (the reinforcement branch matched)
        # and, per 0012 Design 1, persisted as its own edge — no absorption, no contention.
        assert len(active) == 2
        assert active[0].valid_from.date().isoformat() == "2026-01-01"   # first-known intact
        assert all(e.invalidated_at is None for e in active)
        mem.close()


def test_paraphrase_match_stays_order_sensitive():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [
            {"triples": [{"subject": "user", "relation": "prefers", "object": "tea over coffee", "volatility": "durable"}],
             "episode": "prefers tea"},
            {"triples": [{"subject": "user", "relation": "prefers", "object": "coffee over tea", "volatility": "durable"}],
             "episode": "prefers coffee now"},
        ])
        mem.remember("u", "I prefer tea over coffee.", date="2026-01-01")
        mem.remember("u", "Actually I prefer coffee over tea.", date="2026-01-05")
        active = mem.store.edges("u", relation="prefers")
        assert len(active) == 1                              # functional → superseded
        assert active[0].object == "coffee over tea"         # NOT merged with the old value
        hist = mem.store.edges("u", relation="prefers", active_only=False)
        assert any(not e.active and e.object == "tea over coffee" for e in hist)
        mem.close()


def test_consolidation_preserves_and_compresses():
    with tempfile.TemporaryDirectory() as d:
        # 10 cold episodes; consolidation returns 3 (a failure, its fix, a routine merge)
        extract = [{"triples": [], "episode": f"Routine work day {i}."} for i in range(10)]
        consolidated = {"records": [
            {"date": "2026-01-02", "summary": "Build failed on the export step (first occurrence)."},
            {"date": "2026-01-05", "summary": "Fixed the export by switching tools."},
            {"date": "2026-01-06", "summary": "Several routine work days."}]}
        mem = _mem(d, extract + [consolidated])
        for i in range(10):
            mem.remember("u", f"day {i}", date=f"2026-01-{i+1:02d}")
        assert len(mem.store.episodes("u")) == 10

        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        rep = lifecycle.consolidate(mem.store, mem.llm, "u", mem.config, now=now)
        assert rep == {"consolidated": 10, "into": 3, "recovered": 0}
        eps = mem.store.episodes("u")
        assert len(eps) == 3
        assert all(e.lineage for e in eps)          # specs/0010: outputs carry lineage
        assert any("first occurrence" in e.summary for e in eps)  # guard held
        mem.close()


if __name__ == "__main__":
    test_expiry_lapse_confirm_and_reinforcement()
    test_reinforcement_refreshes_not_duplicates()
    test_reinforcement_matches_paraphrased_values()
    test_paraphrase_match_stays_order_sensitive()
    test_consolidation_preserves_and_compresses()
    print("lifecycle OK")


# --- 0.4.6: the two defects found verifying 0002's external review ----------

def _one_edge(m, valid_from):
    from veracium.schema import Edge, Provenance
    from veracium.schema import _SourceType as SourceType
    e = Edge(id="e-t", user_id="u", subject="user", relation="likes", object="tea",
             valid_from=valid_from,
             provenance=Provenance(source_type=SourceType.STATED,
                                   author_of_evidence=EvidenceAuthor.USER,
                                   evidence_ref="x", observed_at=valid_from))
    m.store.add_edge(e)
    return e


def test_confirm_returns_the_real_valid_from_not_the_confirmation_date():
    """M2 removed the false date from the model's context and left it in the
    return contract a host UI reads."""
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [])
        _one_edge(m, datetime(2026, 1, 1, tzinfo=timezone.utc))
        r = m.confirm("u", "e-t", date="2026-03-15")
        assert r["valid_from"] == "2026-01-01", "returned the confirmation date again"
        assert r["confirmed_at"] == "2026-03-15"
        stored = [x for x in m.store.edges("u") if x.id == "e-t"][0]
        assert r["valid_from"] == stored.valid_from.date().isoformat()


def test_a_future_event_date_is_rejected():
    import pytest
    from veracium.ingest import _event_dt
    with pytest.raises(ValueError, match="in the future"):
        _event_dt("2099-01-01")


def test_clock_skew_is_tolerated_but_a_typo_is_not():
    import pytest
    from veracium.ingest import _event_dt, MAX_FUTURE_SKEW
    from veracium.schema import utcnow
    _event_dt((utcnow() + MAX_FUTURE_SKEW / 2).date().isoformat())   # must not raise
    with pytest.raises(ValueError):
        _event_dt((utcnow() + MAX_FUTURE_SKEW * 10).date().isoformat())


def test_a_future_confirmation_cannot_freeze_an_edge_out_of_the_lifecycle():
    """observed_at only ever advances, so before the clamp a single future date
    was unrecoverable: no later confirmation could lower it."""
    import pytest
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [])
        _one_edge(m, datetime(2026, 1, 1, tzinfo=timezone.utc))
        with pytest.raises(ValueError):
            m.confirm("u", "e-t", date="2099-01-01")
        stored = [x for x in m.store.edges("u") if x.id == "e-t"][0]
        assert stored.provenance.observed_at.year < 2099, "the write must not land"


def test_a_future_date_cannot_enter_through_ingest_either():
    """The clamp is at _event_dt, not in confirm(): remember() reaches
    valid_from AND observed_at, so it was the wider of the two doors."""
    import pytest
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [{"triples": [{"subject": "user", "relation": "works_as",
                                   "object": "CFO"}], "episode": "said"}])
        with pytest.raises(ValueError, match="in the future"):
            m.remember("u", "I am CFO at Acme", date="2099-01-01")


def test_past_and_today_still_work():
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [])
        _one_edge(m, datetime(2026, 1, 1, tzinfo=timezone.utc))
        assert m.confirm("u", "e-t", date="2026-02-01")["confirmed"] == "e-t"


def test_a_malformed_event_date_is_rejected_not_silently_now():
    """It used to fall back to utcnow(), which is the same manufacture as
    accepting a future date, in a quieter form: a malformed statement about when
    an event happened is not evidence that it happened now. The fallback could
    refresh a stale fact and relieve lifecycle pressure."""
    import pytest
    from veracium.ingest import _event_dt
    for bad in ("not-a-date", "", "2026-13-45", "01/02/2026"):
        with pytest.raises(ValueError, match="not an ISO date"):
            _event_dt(bad)


def test_omitting_the_date_still_means_now():
    """Absence is the only thing that means now — the escape hatch the
    rejection above depends on."""
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [])
        _one_edge(m, datetime(2026, 1, 1, tzinfo=timezone.utc))
        r = m.confirm("u", "e-t")          # no date=
        assert r["confirmed"] == "e-t"


def test_a_malformed_date_cannot_enter_through_ingest():
    import pytest
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [{"triples": [], "episode": "said"}])
        with pytest.raises(ValueError, match="not an ISO date"):
            m.remember("u", "hello", date="yesterday")


def test_an_offset_bearing_timestamp_is_converted_not_relabelled():
    """`.replace(tzinfo=utc)` discarded an existing offset, so `T20:00-12:00`
    was checked as if it were 20:00 UTC when the instant is 08:00 the next day.
    Measured at 12 hours of skew-limit bypass; up to 26 across the legal offset
    range."""
    import pytest
    from veracium.ingest import _event_dt
    from veracium.schema import utcnow
    from datetime import timedelta
    now = utcnow()
    future = (now + timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%S") + "-12:00"
    with pytest.raises(ValueError, match="in the future"):
        _event_dt(future)


def test_a_legitimate_offset_timestamp_is_accepted_and_converted():
    from veracium.ingest import _event_dt
    from veracium.schema import utcnow
    from datetime import timedelta, timezone
    past = (utcnow() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"
    got = _event_dt(past)
    assert got.tzinfo == timezone.utc
    assert got < utcnow()


def test_a_naive_date_still_means_utc():
    from veracium.ingest import _event_dt
    from datetime import timezone
    assert _event_dt("2026-01-01").tzinfo == timezone.utc


def test_consolidation_output_is_no_stronger_than_its_weakest_input():
    """N9b (spec 0002). `confidence` was a flat 0.9, so a batch containing a 0.2
    episode produced a summary at 0.9 — confidence manufactured from
    recognition, the same defect M5 forbids at T2."""
    from veracium.lifecycle import consolidate
    from veracium.schema import Episode, Provenance, Disclosure
    from veracium.schema import _SourceType as SourceType
    from veracium.store.sqlite import SqliteStore
    from datetime import timedelta
    import os, json
    with tempfile.TemporaryDirectory() as d:
        st = SqliteStore(os.path.join(d, "t.db"))
        old = datetime.now(timezone.utc) - timedelta(days=90)
        for i in range(8):
            st.add_episode(Episode(
                id=f"ep{i}", user_id="u", date=old.date().isoformat(),
                summary=f"thing {i}",
                provenance=Provenance(
                    source_type=SourceType.STATED,
                    author_of_evidence=EvidenceAuthor.USER, evidence_ref="x",
                    observed_at=old,
                    confidence=0.2 if i == 3 else 0.95,
                    disclosure=(Disclosure.USE_ONLY if i == 5
                                else Disclosure.MENTIONABLE))))
        llm = lambda *a, **k: json.dumps(
            {"records": [{"date": old.date().isoformat(), "summary": "s"}]})
        consolidate(st, llm, "u", MemoryConfig(consolidate_after_days=30,
                                               consolidate_min_batch=8))
        out = [e for e in st.episodes("u") if e.id.startswith("epc")][0]
        assert out.provenance.confidence == 0.2, "confidence manufactured"
        assert out.provenance.disclosure == Disclosure.USE_ONLY, "disclosure widened"
        assert out.provenance.observed_at <= old, "currency manufactured"
        assert out.provenance.author_of_evidence == EvidenceAuthor.SYSTEM


def test_consolidated_provenance_is_internally_consistent():
    """A SYSTEM-authored summary reported `source_type=STATED` and the FIRST
    input's `evidence_ref`, because both were inherited from cold[0] — M1's
    original defect surviving on two fields the 0.4.7 test never inspected."""
    from veracium.lifecycle import consolidate
    from veracium.schema import Episode, Provenance
    from veracium.schema import _SourceType as SourceType
    from veracium.store.sqlite import SqliteStore
    from datetime import timedelta
    import os, json
    with tempfile.TemporaryDirectory() as d:
        st = SqliteStore(os.path.join(d, "t.db"))
        old = datetime.now(timezone.utc) - timedelta(days=90)
        for i in range(8):
            st.add_episode(Episode(
                id=f"e{i}", user_id="u", date=old.date().isoformat(), summary=f"s{i}",
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"event-{i}", observed_at=old)))
        consolidate(st, lambda *a, **k: json.dumps(
            {"records": [{"date": old.date().isoformat(), "summary": "S"}]}),
            "u", MemoryConfig(consolidate_after_days=30, consolidate_min_batch=8))
        p = [e for e in st.episodes("u") if e.id.startswith("epc")][0].provenance
        assert p.author_of_evidence == EvidenceAuthor.SYSTEM
        assert p.model_dump()["source_type"] == "inferred", "a summary is not STATED"
        assert not p.evidence_ref.startswith("event-"), \
            "evidence_ref still points at one arbitrary input"
        # specs/0010 X23: the store binds evidence_ref to the consolidation OPERATION
        # (its operation_id), computed at the fenced write boundary — not an input event.
        assert p.evidence_ref.startswith("op-")


def test_an_offset_timestamp_survives_every_public_entry_point():
    """`_event_dt` converted offsets correctly while `remember()` still raised,
    because `prompts.date_context` parsed the raw string with
    `date.fromisoformat`. One input, two parsers."""
    from veracium.schema import Edge, Provenance
    from veracium.schema import _SourceType as SourceType
    from datetime import date as _date
    with tempfile.TemporaryDirectory() as d:
        m = _mem(d, [{"triples": [], "episode": "x"}])
        # 23:00-08:00 is 07:00 the NEXT day in UTC — same-day offsets prove nothing
        m.remember("u", "hello", date="2026-01-01T23:00:00-08:00")
        ep = m.store.episodes("u")[-1]
        assert ep.date == "2026-01-02", f"not normalised: {ep.date}"
        _date.fromisoformat(ep.date)          # every downstream consumer does this

        m.store.add_edge(Edge(
            id="e", user_id="u", subject="user", relation="likes", object="tea",
            valid_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
            provenance=Provenance(source_type=SourceType.STATED,
                                  author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref="x",
                                  observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc))))
        r = m.confirm("u", "e", date="2026-03-15T23:00:00-08:00")
        assert r["confirmed_at"] == "2026-03-16", "the response echoed the caller"
        _date.fromisoformat(m.store.episodes("u")[-1].date)


# --- N9's transition rule (specs/0002, seventh review finding 3) ------------

def _n9():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "specs"))
    import monotone
    return monotone


# A FIXED instant, not now(). Two calls to now() differ by microseconds, and
# N9 compares observed_at — so a helper that stamps the clock twice makes every
# pair look like it advanced currency.
_T0 = datetime(2025, 1, 1, tzinfo=timezone.utc)


def _edge(**kw):
    from veracium.schema import Edge, Provenance, Volatility
    from veracium.schema import _SourceType as SourceType
    old = _T0
    e = Edge(id="e", user_id="u", subject="user", relation="works_at", object="Acme",
             volatility=Volatility.TRANSIENT, valid_from=old,
             provenance=Provenance(source_type=SourceType.STATED,
                                   author_of_evidence=EvidenceAuthor.USER,
                                   evidence_ref="x", observed_at=old))
    for k, v in kw.items():
        setattr(e, k, v)
    return e


def test_n9_permits_the_retirement_the_trust_matrix_calls_clean():
    """v7 required post.invalidation_reason == pre.invalidation_reason, which
    forbids expiry: it moves that field from None to 'lapsed'. The rule
    forbade the operation the same document listed as clean."""
    M = _n9()
    old = _T0
    assert M.holds(_edge(), _edge(invalidated_at=old, invalidation_reason="lapsed"))


def test_n9_still_forbids_reactivation_and_reason_rewriting():
    M = _n9()
    old = _T0
    retired = _edge(invalidated_at=old, invalidation_reason="lapsed")
    assert "reactivated" in " ".join(M.violations(retired, _edge()))
    rewritten = _edge(invalidated_at=old, invalidation_reason="decayed")
    assert "rewritten" in " ".join(M.violations(retired, rewritten))


def test_n9_refuses_a_retirement_with_no_reason():
    M = _n9()
    old = _T0
    assert M.violations(_edge(), _edge(invalidated_at=old))


def test_an_evidence_free_operation_cannot_claim_a_reason_it_did_not_earn():
    """`superseded` means new evidence arrived; `corrected`/`disputed` mean an
    authorised act. None of those is evidence-free, so maintenance may not
    label its own retirement with them."""
    M = _n9()
    old = _T0
    sup = _edge(invalidated_at=old, invalidation_reason="superseded")
    assert M.violations(_edge(), sup, evidence_free=True)
    assert M.holds(_edge(), sup, evidence_free=False)


def test_the_real_expire_path_satisfies_n9():
    """Against the running code, not a constructed pair."""
    import copy, os
    from veracium.lifecycle import expire
    from veracium.store.sqlite import SqliteStore
    M = _n9()
    with tempfile.TemporaryDirectory() as d:
        st = SqliteStore(os.path.join(d, "t.db"))
        st.add_edge(_edge(id="e1"))
        pre = copy.deepcopy(st.edges("u", active_only=False)[0])
        expire(st, "u", MemoryConfig())
        post = st.edges("u", active_only=False)[0]
        assert not post.active and post.invalidation_reason == "lapsed"
        assert M.holds(pre, post), M.violations(pre, post)
