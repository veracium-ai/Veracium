"""0019's marker on the as-of surface (U5: never severed on any code-rendered surface).

Found by the 0045-0047 round-1 external reviewer (2026-10-10, R1-05's witness): through
`recall(as_of=...)` / `facts_valid_at`, `asof.resolve.render_line` rendered a flagged fact WITHOUT
`[possible extraction error]`, while `graph.render_edges` renders it on every branch. The fix places
the marker exactly where the current renderer does: right after the object, before the note, on every
branch a fact renders through (grounded as of T, fenced as what was believed, indeterminate).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from veracium import Memory, MemoryConfig
from veracium.asof import FENCED_SELF, GROUNDED_OUTCOMES
from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance
from veracium.store.sqlite import SqliteStore

MARKER = "[possible extraction error]"
U = "u"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
D = timedelta(days=1)


def _edge(obj, *, ungrounded, valid_from=T0, supersedes=None, relation="located_at"):
    return Edge(id=f"e-{uuid.uuid4().hex[:10]}", user_id=U, subject="user", relation=relation,
                object=obj, valid_from=valid_from, supersedes=supersedes, ungrounded=ungrounded,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}", source_id="mb-a",
                                      disclosure=Disclosure.MENTIONABLE, observed_at=valid_from))


def _mem(tmp_path):
    store = SqliteStore(str(tmp_path / "asof.db"))
    mem = Memory(llm=lambda *a, **k: "ok", store=store,
                 config=MemoryConfig(db_path=str(tmp_path / "unused.db"), wiki_recompile_after_writes=0))
    return store, mem


def _line(r, obj):
    """The one rendered context line that carries `obj` (asserted unique)."""
    hits = [ln for ln in r.context.splitlines() if obj in ln]
    assert len(hits) == 1, (obj, hits, r.context)
    return hits[0]


def test_a_flagged_fact_renders_its_marker_in_as_of_recall__with_its_controls(tmp_path):
    """The defect, through the public path: a flagged fact grounded as of T renders the marker,
    attached to its own object. Controls: the CURRENT recall of the same fact already carries it (the
    marker is 0019's, not new), and an unflagged fact rendered beside it as of T does not."""
    store, mem = _mem(tmp_path)
    flagged = _edge("Porto", ungrounded=True)
    plain = _edge("violin", ungrounded=False, relation="uses_tool")
    store.add_edge(flagged)
    store.add_edge(plain)
    now = mem.recall(U, "porto violin")
    assert MARKER in _line(now, "Porto") and MARKER not in _line(now, "violin")
    r = mem.recall(U, "porto violin", as_of=T0 + D)
    assert r.as_of.resolution_of(flagged.id).outcome in GROUNDED_OUTCOMES
    assert f"Porto {MARKER}" in _line(r, "Porto"), _line(r, "Porto")
    assert MARKER not in _line(r, "violin")


def test_the_marker_rides_the_fenced_branch_too(tmp_path):
    """U5 is every branch, not the grounded one: a flagged fact that was later superseded renders, as of
    a time after the supersession, as what was BELIEVED (fenced), and keeps its marker, because what was
    believed was an extraction that might have been wrong. Control: its unflagged successor has none."""
    store, mem = _mem(tmp_path)
    old = _edge("Porto", ungrounded=True)
    store.add_edge(old)
    new = _edge("Braga", ungrounded=False, valid_from=T0 + D, supersedes=old.id)
    store.add_edge(new)
    store.invalidate_edge(old.id, T0 + D, "superseded")
    facts = {f.edge.id: f.resolution for f in mem.facts_valid_at(U, "user", "located_at", T0 + D / 2)}
    assert facts[old.id].outcome in GROUNDED_OUTCOMES
    r = mem.recall(U, "porto braga", as_of=T0 + 3 * D)
    fenced = [ln for ln in r.context.splitlines() if "Porto" in ln and "FENCED" in ln]
    if fenced:                                   # rendered as what was believed
        assert all(f"Porto {MARKER}" in ln for ln in fenced), fenced
    assert MARKER not in _line(r, "Braga")
    # the fenced branch exercised DIRECTLY, so the assertion above cannot pass by the line being absent
    from veracium.asof.resolve import render_line
    res = r.as_of.resolution_of(old.id) or facts[old.id]
    from dataclasses import replace
    line = render_line(old, replace(res, outcome=FENCED_SELF), T0 + 3 * D)
    assert line.startswith("[FENCED") and f"Porto {MARKER}" in line, line


def test_the_marker_rides_the_indeterminate_branch_too(tmp_path):
    """The third branch: a fact whose truth as of T cannot be decided renders INDETERMINATE with its
    cause, and a flagged one keeps its marker there as well. Control: unflagged, no marker."""
    from dataclasses import replace
    from veracium.asof import INDETERMINATE
    from veracium.asof.resolve import render_line
    store, mem = _mem(tmp_path)
    flagged, plain = _edge("Porto", ungrounded=True), _edge("Lisbon", ungrounded=False)
    store.add_edge(flagged)
    store.add_edge(plain)
    facts = {f.edge.id: f.resolution for f in mem.facts_valid_at(U, "user", "located_at", T0 + D)}
    for e, want in ((flagged, True), (plain, False)):
        line = render_line(e, replace(facts[e.id], outcome=INDETERMINATE), T0 + D)
        assert line.startswith("[INDETERMINATE"), line
        assert (f"{e.object} {MARKER}" in line) is want, line
