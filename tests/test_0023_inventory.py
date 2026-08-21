"""specs/0023 §6 — N2, N8, N10, N14, N15: the closing invariants (C6)."""

import pathlib
import re
import tempfile
import uuid

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig, SqliteStore
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, Episode,
                             Provenance)
from veracium.scope_linkage import identity_digest_of
from veracium.store import revocation as rv

U = "u"
AT = "2026-08-21T00:00:00Z"
SRC = pathlib.Path("src/veracium")


def _ep(disclosure=Disclosure.MENTIONABLE, summary="s", source=None):
    return Episode(id=f"ep-{uuid.uuid4().hex[:6]}", user_id=U,
                   date="2026-08-01", summary=summary,
                   provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                         evidence_ref="ev", source_id=source,
                                         disclosure=disclosure))


# --- N2: exactly two disclosure writers --------------------------------------

def test_disclosure_writers_are_exactly_the_two_known_sites():
    """One ingest writer plus the one import cap — a third writer anywhere in
    src/ fails, because a disclosure nobody inventoried is a floor nobody
    audits. (The N8 destination cap lives INSIDE the import module: it is the
    import cap's 0023 half, not a third site.)"""
    writers = set()
    for f in sorted(SRC.rglob("*.py")):
        text = f.read_text()
        # ASSIGNMENT only — `(?<![=!])=(?!=)` refuses == and != so property
        # COMPARISONS (schema's derived predicates, scope_read's policy reads)
        # do not count as writers; the first draft matched them, which is the
        # too-wide mirror of the domain class
        if re.search(r"[\"']?disclosure[\"']?\s*(?:(?<![=!])=(?!=)|:)\s*"
                     r"[\(\"']*(Disclosure\.|_disclosure_for)", text):
            writers.add(f.name)
    assert writers == {"ingest.py", "portability.py"}, (
        f"disclosure writers: {sorted(writers)} — N2 permits exactly the "
        f"ingest site and the import cap")


# --- N8: the destination-standing cap on import ------------------------------

def test_import_round_trip_requarantines(tmp_path):
    """Export, REVOKE in the destination, reimport into the SAME store: the
    record arrives QUARANTINED — the file cannot resurrect what the store
    has standing-revoked (§3b: no flag on an import file overrides this
    store's standing state)."""
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        return "wiki"
    m = Memory(llm=llm, config=MemoryConfig(db_path=str(tmp_path / "a.db")))
    ep = _ep(summary="feed said Lisbon", source="feed-1")
    m.store.add_episode(ep)
    out = tmp_path / "x.json"
    m.export_memory(U, out)

    d = identity_digest_of(None, "feed-1", m.store.local_origin())
    rv.revoke_source(m.store, U, d, "revoke", "operator", AT)
    # the sweep retired the original; delete it so reimport is not an id-skip
    m.store._conn.execute("DELETE FROM episodes WHERE id=?", (ep.id,))
    m.store._conn.commit()

    m.import_memory(out, restore=True)     # restore preserves FILE trust —
    #                                        and must NOT override the store's
    #                                        standing state (the §3b half)
    got = m.store.episodes(U, include_retired=True)
    assert got and got[0].provenance.disclosure == Disclosure.QUARANTINED, (
        "an export→revoke→reimport sequence resurrected an assertable copy")


# --- N10: non-revival grants nothing -----------------------------------------

def test_non_revival_grants_nothing(tmp_path):
    """RESTRICT-ONLY, over the enumerated temptations: under a standing
    revocation no record's disclosure widens, nothing inactive activates,
    and no retired episode returns — asserted as a store-state diff, so a
    'grant' anywhere in the swept surface shows."""
    s = SqliteStore(str(tmp_path / "n10.db"))
    quarantined = _ep(Disclosure.QUARANTINED, source="feed-2")
    s.add_episode(quarantined)
    d = identity_digest_of(None, "feed-1", s.local_origin())
    rv.revoke_source(s, U, d, "revoke", "operator", AT)
    rv.revoke_source(s, U, d, "lift", "operator", AT)
    got = s.episodes(U, include_retired=True)[0]
    assert got.provenance.disclosure == Disclosure.QUARANTINED, (
        "a revocation cycle WIDENED an unrelated record's disclosure")


# --- N14: not assertable at EVERY consumer, parametrised over the surfaces ---

def _surface_recall(quarantined, grounded):
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        return "wiki"
    d = tempfile.mkdtemp()
    m = Memory(llm=llm, config=MemoryConfig(db_path=f"{d}/m.db"))
    m.store.add_episode(quarantined); m.store.add_episode(grounded)
    ctx = m.recall(U, "what happened").context
    return (grounded.summary in ctx
            and ctx.index(grounded.summary) < ctx.index(quarantined.summary))


def _surface_gate(quarantined, grounded):
    from veracium.gate import partition_parts
    _, ep_lines, _, tp_ep_lines = partition_parts([], [quarantined, grounded])
    return (not any(quarantined.summary in l for l in ep_lines)
            and any(quarantined.summary in l for l in tp_ep_lines))


def _surface_compile(quarantined, grounded):
    from veracium.compile import _grounded_inputs
    d = tempfile.mkdtemp()
    s = SqliteStore(f"{d}/c.db")
    s.add_episode(quarantined); s.add_episode(grounded)
    _, eps = _grounded_inputs(s, U, DEFAULT_RELATIONS)
    ids = {e.id for e in eps}
    return quarantined.id not in ids and grounded.id in ids


def _surface_proactive(quarantined, grounded):
    from veracium.proactive import assemble
    d = tempfile.mkdtemp()
    s = SqliteStore(f"{d}/p.db")
    q = quarantined.model_copy(update={"date": "2026-08-21"})
    g = grounded.model_copy(update={"date": "2026-08-21"})
    s.add_episode(q); s.add_episode(g)
    from datetime import datetime, timezone
    text = str(assemble(s, U, MemoryConfig(db_path=f"{d}/x.db"),
                        now=datetime(2026, 8, 21, tzinfo=timezone.utc)))
    return quarantined.summary not in text


def _surface_scope_read(quarantined, grounded):
    from veracium.scope_read import _asserted_today
    return (not _asserted_today(quarantined)) and _asserted_today(grounded)


@pytest.mark.parametrize("surface", [
    _surface_recall, _surface_gate, _surface_compile,
    _surface_proactive, _surface_scope_read,
], ids=["recall-render", "gate-partition", "wiki-input", "proactive",
        "scope-read"])
def test_quarantined_episode_is_not_assertable_anywhere(surface):
    """N14, one assertion per site ON THE SURFACE — a store-level assertion
    passes with all five broken (F1)."""
    q = _ep(Disclosure.QUARANTINED, summary="CLAIMED-BY-FEED-XX")
    g = _ep(summary="USER-SAID-SO-XX")
    assert surface(q, g), "the quarantined episode reached this surface"


# --- N15: the inventory, generated from CONSUMPTION, and its bite ------------

_DISPOSITIONED = {
    # routed through Episode.assertable (C2)
    "__init__.py", "gate.py", "compile.py", "proactive.py", "scope_read.py",
    # EXPLICIT non-assertability uses — each with its reason:
    "lifecycle.py",     # R3-3: maintenance excludes on STANDING REVOCATION,
                        # not assertability — the read predicate over-excludes
                        # in a regime this spec promises to leave untouched
    "ingest.py",        # writes summaries, reads none into a prompt
    "portability.py",   # export/import carries records verbatim — a transport,
                        # not a consumer; the N8 cap governs what arrives
    "introspect.py",    # the provenance-inspection surface REPORTS records
                        # with their flags; suppressing there would hide the
                        # very state an operator audits
    "store",            # the store package: persistence, not consumption
    "revocation.py", "revocation_sweep.py",   # 0022's sweep projects records
    "graph.py",         # renders EDGES; episode summary reads are outcome
                        # bookkeeping, not prompt text
    "schema.py",        # the type itself
}


def _episode_text_consumers():
    found = set()
    for f in sorted(SRC.rglob("*.py")):
        text = f.read_text()
        if re.search(r"\.summary\b", text) or re.search(
                r"episodes\s*\(", text):
            found.add("store" if f.parent.name == "store" else f.name)
    return found


def test_episode_text_consumers_are_exhaustive():
    """N15 (v5 form, F4): swept by CONSUMPTION — any read of `.summary` or
    any episode collection — never by a condition string, which is blind to
    a consumer that never had one. Two legitimate dispositions exist
    (assertable-routed, explicit non-assertability use); a file with neither
    fails."""
    undispositioned = _episode_text_consumers() - _DISPOSITIONED
    assert not undispositioned, (
        f"episode-text consumers with NO disposition: "
        f"{sorted(undispositioned)} — route through Episode.assertable or "
        f"add an explicit non-assertability entry WITH ITS REASON")


def test_the_inventory_gate_bites(tmp_path):
    """The ADVERSARIAL FIXTURE: an unguarded consumer reading only
    `ep.summary` must FAIL the sweep. A gate nobody has watched fail is a
    gate nobody has tested."""
    rogue = SRC / "zz_rogue_consumer_fixture.py"
    rogue.write_text('def leak(eps):\n    return "\\n".join(ep.summary for ep in eps)\n')
    try:
        undispositioned = _episode_text_consumers() - _DISPOSITIONED
        assert "zz_rogue_consumer_fixture.py" in undispositioned, (
            "the sweep did NOT catch an unguarded ep.summary consumer — "
            "N15's gate is decorative")
    finally:
        rogue.unlink()
