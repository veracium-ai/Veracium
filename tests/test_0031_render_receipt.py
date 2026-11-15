"""specs/0031 §4f §4b, INV-TT3: the render receipt — `recall(..., render_receipt=True)` returns one unit per record the
renderer ADMITTED, built at the admission points, with the text exactly as admitted, the partition and the
annotations; nothing the renderer withheld; wiki text with no ids. Off by default, leaving recall byte-identical.

Every expectation below is an INDEPENDENT fixture (the ids, partitions and annotations this test planted), never a
search of the prose; the only reads of `context` check that the receipt's text is a substring of it (as admitted)
and that turning the receipt on does not move a byte.
"""
import json
from datetime import datetime, timedelta, timezone

import pytest

import veracium
from veracium.budgets import ELISION_MARKER
from veracium.config import MemoryConfig
from veracium.graph import apply_supersession
from veracium.schema import Disclosure, Edge, Episode, EvidenceAuthor, Provenance, Volatility
from veracium.scope import Identity

U = "u"
NOW = datetime(2026, 11, 10, tzinfo=timezone.utc)
A = Identity(None, "src-a")
B = Identity(None, "src-b")


def _edge(eid, obj, *, author=EvidenceAuthor.USER, disc=Disclosure.MENTIONABLE, rel="works_as", subject="user",
          flag=False, days=1, source_id=None, ungrounded=False):
    t = NOW - timedelta(days=days)
    return Edge(id=eid, user_id=U, subject=subject, relation=rel, object=obj, volatility=Volatility.SLOW,
                valid_from=t, needs_confirmation=flag, ungrounded=ungrounded,
                provenance=Provenance(author_of_evidence=author, evidence_ref=f"ev-{eid}", disclosure=disc,
                                      observed_at=t, source_id=source_id))


def _ep(eid, summary, *, date="2026-11-01", author=EvidenceAuthor.USER, source_id=None, disc=Disclosure.MENTIONABLE):
    return Episode(id=eid, user_id=U, date=date, summary=summary,
                   provenance=Provenance(author_of_evidence=author, evidence_ref=f"ev-{eid}", disclosure=disc,
                                         source_id=source_id))


def _mem(tmp_path, **cfg):
    tmp_path.mkdir(parents=True, exist_ok=True)
    cfg.setdefault("wiki_recompile_after_writes", 0)
    return veracium.Memory(llm=lambda p, **k: "## USER MODEL\n- A fact.",
                           config=MemoryConfig(db_path=str(tmp_path / "m.db"), require_source_id=False, **cfg))


def _ids(units, **where):
    return [u["id"] for u in units if all(u.get(k) == v for k, v in where.items())]


def _check_as_admitted(r):
    for u in r.render_receipt:
        assert u["text"] in r.context, u


# ------------------------------------------------------------------ off by default; on, the text does not move
@pytest.mark.parametrize("query", ["engineer", None])
def test_the_receipt_is_off_by_default_and_on_it_changes_no_byte(tmp_path, query):
    """Mutant: the receipt on by default; the receipt changing the rendered text."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-1", "engineer", flag=True))      # stale: the briefing lists it too
    m.store.add_episode(_ep("ep-1", "talked about being an engineer"))
    off = m.recall(U, query)
    on = m.recall(U, query, render_receipt=True)
    assert off.render_receipt is None
    assert (on.context, on.grounded, on.unverified, on.truncated) == (off.context, off.grounded, off.unverified,
                                                                      off.truncated)
    assert isinstance(on.render_receipt, list) and on.render_receipt


# ------------------------------------------------------------------ a whole-record budget drop
def test_a_record_the_budget_dropped_is_not_a_unit(tmp_path):
    """Mutant: returning `Recall.edges` unfiltered (the dropped edges are in `edges`, never in the receipt)."""
    m = _mem(tmp_path)
    pad = " with an intentionally verbose qualifier occupying budget" * 6
    for i in range(12):
        m.store.add_edge(_edge(f"e-{i:02d}", f"engineer {i}{pad}", rel=f"role_{i}"))
    r = m.recall(U, "engineer", token_budget=400, render_receipt=True)
    admitted = set(_ids(r.render_receipt, kind="edge"))
    assert r.truncated and admitted and admitted < {e.id for e in r.edges}
    _check_as_admitted(r)


# ------------------------------------------------------------------ a within-record clamp
def test_a_clamped_record_carries_its_prefix_and_the_elision_marker(tmp_path):
    """Mutant: the raw object for a clamped unit."""
    m = _mem(tmp_path, item_cap_tokens=64)
    long_obj = "engineer " + "x" * 2000
    m.store.add_edge(_edge("e-long", long_obj))
    r = m.recall(U, "engineer", render_receipt=True)
    (u,) = [u for u in r.render_receipt if u["id"] == "e-long"]
    assert ELISION_MARKER in u["text"] and long_obj not in u["text"] and u["text"] in r.context


# ------------------------------------------------------------------ identical text under two ids
def test_identical_text_under_two_ids_is_two_units(tmp_path):
    """Mutant: ids inferred by substring (it would map one text to one id)."""
    m = _mem(tmp_path)
    m.store.add_episode(_ep("ep-a", "we discussed the engineer offer"))
    m.store.add_episode(_ep("ep-b", "we discussed the engineer offer"))
    r = m.recall(U, "engineer", render_receipt=True)
    eps = [u for u in r.render_receipt if u["kind"] == "episode"]
    assert sorted(u["id"] for u in eps) == ["ep-a", "ep-b"] and len({u["text"] for u in eps}) == 1


# ------------------------------------------------------------------ the fenced partition
def test_a_third_party_claim_and_episode_are_fenced(tmp_path):
    """Mutant: the partition dropped (a fenced unit read as grounded)."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-own", "engineer"))
    m.store.add_edge(_edge("e-claim", "engineer at acme", author=EvidenceAuthor.THIRD_PARTY,
                           disc=Disclosure.QUARANTINED, rel="claimed_role"))
    m.store.add_episode(_ep("ep-tp", "an email said the engineer moved", author=EvidenceAuthor.THIRD_PARTY,
                            disc=Disclosure.QUARANTINED))
    r = m.recall(U, "engineer", render_receipt=True)
    part = {u["id"]: u["partition"] for u in r.render_receipt}
    assert part.get("e-own") == "grounded"
    assert part.get("e-claim") == "fenced" and part.get("ep-tp") == "fenced"
    _check_as_admitted(r)


def test_a_cross_visible_episode_is_fenced_and_not_mutable_under_a_principal(tmp_path):
    """Under a principal every unit carries `mutable`, true only for OWN (§3b)."""
    m = _mem(tmp_path, scope_groups={"team-a": [A], "team-b": [B]}, cross_scope_visible=True)
    m.store.add_edge(_edge("e-mine", "engineer", source_id="src-a"))
    m.store.add_episode(_ep("ep-theirs", "the engineer offer, from team b", source_id="src-b"))
    r = m.recall(U, "engineer", principal=A, render_receipt=True)
    units = {u["id"]: u for u in r.render_receipt}
    assert units["e-mine"]["mutable"] is True and units["e-mine"]["partition"] == "grounded"
    assert units["ep-theirs"]["mutable"] is False and units["ep-theirs"]["partition"] == "fenced"
    unscoped = m.recall(U, "engineer", render_receipt=True)
    assert all("mutable" not in u for u in unscoped.render_receipt)


# ------------------------------------------------------------------ annotations and the subject
def test_annotations_and_a_non_user_subject(tmp_path):
    """Mutant: an annotation dropped; the subject left off a non-user unit (or put on a user unit)."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-stale", "engineer", flag=True))
    m.store.add_edge(_edge("e-alice", "engineer too", subject="person:alice", rel="role_alice"))
    m.store.add_edge(_edge("e-err", "engineer maybe", rel="role_err", ungrounded=True))
    r = m.recall(U, "engineer", render_receipt=True)
    units = {u["id"]: u for u in r.render_receipt}
    assert "stale" in units["e-stale"]["annotations"] and "subject" not in units["e-stale"]
    assert units["e-alice"]["subject"] == "person:alice"
    assert "extraction_error" in units["e-err"]["annotations"]


# ------------------------------------------------------------------ contested members
def _contend(mem):
    tail = " with a qualifier"
    mem.store.add_edge(_edge("p0", f"grounded value{tail}", subject="person:x"))
    mem.store.add_edge(_edge("g0", f"grounded alternative{tail}", subject="person:x", days=2))
    inc = _edge("i0", f"challenge{tail}", author=EvidenceAuthor.THIRD_PARTY, disc=Disclosure.QUARANTINED,
                subject="person:x")
    apply_supersession(mem.store, inc, mem.config.relations)


def test_contested_members_are_contested_units_with_the_group_framing(tmp_path):
    """Mutant: the partition dropped for a contested member; the framing left off a split group."""
    m = _mem(tmp_path)
    _contend(m)
    r = m.recall(U, "grounded value", render_receipt=True)
    contested = [u for u in r.render_receipt if u["partition"] == "contested"]
    assert {u["id"] for u in contested} <= {e.id for g in r.contested for e in g.exposed}
    assert contested, [g for g in r.contested]
    for u in contested:
        assert any(a.startswith("contested: ") for a in u["annotations"]) and u["subject"] == "person:x"
    _check_as_admitted(r)


# ------------------------------------------------------------------ a challenged record is withheld, never a unit
def test_a_challenged_record_is_withheld_and_never_a_unit(tmp_path):
    """Mutant: listing a record in the receipt that the renderer withheld."""
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-ok", "engineer", flag=True))                 # stale, so the briefing lists it
    m.store.add_edge(_edge("e-ch", "engineer lead", rel="role_lead", flag=True))
    m.reply(U, "e-ch", kind="challenge", text="that's wrong")
    for q in ("engineer", None):
        r = m.recall(U, q, render_receipt=True)
        assert "e-ch" not in [u["id"] for u in r.render_receipt]
        assert "e-ok" in [u["id"] for u in r.render_receipt]


# ------------------------------------------------------------------ the proactive path
def test_the_proactive_path_lists_what_the_briefing_admitted(tmp_path):
    m = _mem(tmp_path)
    m.store.add_edge(_edge("e-due", "dentist appointment 2026-11-20", rel="appointment"))
    m.store.add_edge(_edge("e-stale", "engineer", flag=True))
    m.store.add_episode(_ep("ep-1", "planned the dentist visit", date="2026-11-09"))
    r = m.recall(U, None, render_receipt=True)
    ids = [u["id"] for u in r.render_receipt]
    assert {"e-due", "e-stale"} <= set(ids)
    assert set(ids) <= {e.id for e in r.edges} | {e.id for e in r.episodes}
    _check_as_admitted(r)


def test_wiki_text_is_a_unit_with_no_id(tmp_path):
    """The wiki enters the query path's context with no record ids; it is a `wiki` unit."""
    m = _mem(tmp_path, wiki_recompile_after_writes=1)
    m.store.add_edge(_edge("e-1", "engineer"))
    r = m.recall(U, "engineer", render_receipt=True)          # recompilation on: recall compiles the wiki
    wiki = [u for u in r.render_receipt if u["kind"] == "wiki"]
    assert "USER MODEL" in r.context, r.context
    assert len(wiki) == 1 and wiki[0]["id"] is None and wiki[0]["text"] in r.context
    assert m.recall(U, "engineer", principal=None, render_receipt=True).render_receipt is not None


def test_the_receipt_is_refused_with_as_of(tmp_path):
    m = _mem(tmp_path)
    with pytest.raises(ValueError, match="render_receipt"):
        m.recall(U, "engineer", as_of=NOW, render_receipt=True)
