"""specs/0008 — what may clear `needs_confirmation`.

The headline invariant: a stored edge's `needs_confirmation` flag transitions
`True → False` ONLY through an explicit confirmation, never through reinforcement
or any provenance value (v1/0.4.5 cleared it whenever the restatement's author
CLASS matched, but same class ≠ same source). This module holds the behavioural
invariants C1–C6 for the core change (§4). The store/confirm-contract invariants
C7–C12 land with the `confirm_edge`/migration commits.
"""

import tempfile

import pytest

from veracium import Memory, MemoryConfig
from veracium.graph import apply_supersession, render_edges
from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance,
                             SourceType)
from datetime import datetime, timezone

JAN = datetime(2026, 1, 15, tzinfo=timezone.utc)
MAR = datetime(2026, 3, 1, tzinfo=timezone.utc)


def _mem(d):
    return Memory(llm=None, config=MemoryConfig(db_path=f"{d}/x.db",
                                                wiki_recompile_after_writes=0))


def _edge(eid, *, author=EvidenceAuthor.USER, obj="dark mode", when=JAN,
          disclosure=Disclosure.MENTIONABLE, source=SourceType.STATED,
          needs=False, subject="user", relation="prefers"):
    return Edge(id=eid, user_id="u", subject=subject, relation=relation,
                object=obj, valid_from=when, active=True, needs_confirmation=needs,
                provenance=Provenance(source_type=source, author_of_evidence=author,
                                      evidence_ref=eid, disclosure=disclosure,
                                      observed_at=when))


def _flag_of(mem, eid):
    return next(e for e in mem.store.edges("u", active_only=False)
               if e.id == eid).needs_confirmation


# --- C1: no provenance VALUE clears the flag --------------------------------

@pytest.mark.parametrize("author", list(EvidenceAuthor))
@pytest.mark.parametrize("source", list(SourceType))
def test_no_provenance_value_clears_staleness(author, source):
    """C1: no value of any provenance field clears `needs_confirmation` — the
    restatement author/source is not evidence of an entitled reaffirmation.
    (A USER/STATED restatement is the same-source case that v1 wrongly cleared;
    every other combination was never entitled to.)"""
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d)
        mem.store.add_edge(_edge("e", author=EvidenceAuthor.USER, needs=True))
        restatement = _edge("e2", author=author, source=source, when=MAR)
        mem.store.add_edge(restatement)
        apply_supersession(mem.store, restatement, mem.config.relations)
        assert _flag_of(mem, "e") is True, \
            f"a {author.value}/{source.value} restatement cleared the flag"
        mem.close()


# --- C6: the cross-author restatement (the 0.4.5 half that was right) --------

def test_cross_author_restatement_does_not_clear():
    """C6 regression: a SYSTEM restatement never clears a USER-addressed flag —
    the case 0.4.5 already got right; it must stay fixed."""
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d)
        mem.store.add_edge(_edge("e", author=EvidenceAuthor.USER, needs=True))
        sys_edge = _edge("e-sys", author=EvidenceAuthor.SYSTEM, when=MAR)
        mem.store.add_edge(sys_edge)
        apply_supersession(mem.store, sys_edge, mem.config.relations)
        assert _flag_of(mem, "e") is True
        mem.close()


# --- C3: reinforcement still refreshes LIVENESS (the permission, not the ban) -

def test_reinforcement_still_advances_observed_at():
    """C3: deleting the flag-clearing conditional must NOT remove the liveness
    refresh — reinforcement still advances `observed_at` (whether it should at all
    is `0012`, neither endorsed nor altered here)."""
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d)
        mem.store.add_edge(_edge("e", author=EvidenceAuthor.USER, needs=True))
        again = _edge("e2", author=EvidenceAuthor.USER, when=MAR)
        mem.store.add_edge(again)
        apply_supersession(mem.store, again, mem.config.relations)
        kept = next(e for e in mem.store.edges("u", active_only=False)
                    if e.id == "e")
        assert kept.provenance.observed_at == MAR      # liveness advanced
        assert kept.needs_confirmation is True         # flag untouched
        mem.close()


# --- C2: confirm() DOES clear it --------------------------------------------

def test_confirm_clears_staleness():
    """C2: an explicit `confirm()` is the path that clears the flag."""
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d)
        mem.store.add_edge(_edge("e", author=EvidenceAuthor.USER, needs=True))
        mem.confirm("u", "e")
        assert _flag_of(mem, "e") is False
        mem.close()


# --- C5: the flag reaches the model when set --------------------------------

def test_stale_marker_renders():
    """C5: a set flag renders into answer context so the model sees the caveat;
    a cleared flag does not."""
    flagged = _edge("e", needs=True)
    fresh = _edge("e2", needs=False)
    assert "possibly stale" in render_edges([flagged])
    assert "possibly stale" not in render_edges([fresh])
