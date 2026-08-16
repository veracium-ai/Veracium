"""specs/0020 slice B — THE READ SURFACES: principal threading and the
visibility relation, checked by the spec's own V-names.

Covered here: V1, V2, V3, V4, V5, V6, V7, V8, V9, V11, V12, V13 — plus §2's
operator row (introspect / export_memory / forget take NO principal, BY
DECISION) recorded as a test rather than left as an omission.

NOT here, and why: V10 is `tests/test_0020_scope_vectors.py` (slice A).
V14/V15/V17/V18 need the 0021 WRITE paths (flattening, reparenting, the
SCHEMA-v8 rows) and live with them. **V16 (import reconstruction is
pre-commit) and V19 (the export reverse link is unique on both sides of a
prune) are PORTABILITY invariants, not read-surface ones** — they are
carried by `tests/test_0021_import_linkage.py`, which already exercises the
pre-commit refusal cells and `derive_absorbed_by`'s zero/one/many
behaviour. Restating them here would duplicate a check, not add one.

The read path is exercised at TWO altitudes on purpose: end-to-end through
`Memory.recall`/`.answer` (which is where a bypass would actually live), and
directly on `ScopeView` for the ledger-evidence cells, whose row shapes the
0021 writers do not yet produce.
"""

from __future__ import annotations

import inspect
import pathlib
import subprocess
import sys
from types import SimpleNamespace

import pytest

from veracium import Memory, gate, scope_read
from veracium.config import MemoryConfig
from veracium.graph import apply_supersession
from veracium.schema import (Disclosure, Edge, Episode, EvidenceAuthor,
                             Provenance)
from veracium.scope import (DECISION_TABLE, SHARED, UNRESOLVED, Identity,
                            ScopeError, validate_policy)
from veracium.scope_read import ScopeView

ROOT = pathlib.Path(__file__).resolve().parents[1]
U = "u1"

A1 = Identity(None, "agent-1")          # the principal, absent origin (I9)
A2 = Identity(None, "agent-2")          # a second scope
A3 = Identity(None, "agent-3")          # a third, never grouped


class _Fake:
    """A provider that records every prompt it is handed — so "the wiki did
    not reach the model" is checked on the actual bytes."""

    def __init__(self, out=""):
        self.out = out
        self.prompts: list[str] = []

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        self.prompts.append(prompt)
        return self.out


def _cfg(tmp_path, name="m.db", *, groups=None, xv=False, wiki=0):
    return MemoryConfig(db_path=str(tmp_path / name),
                        wiki_recompile_after_writes=wiki,
                        scope_groups=groups, cross_scope_visible=xv)


def _mem(tmp_path, name="m.db", *, groups=None, xv=False, wiki=0, llm=None):
    return Memory(llm=llm or _Fake(),
                  config=_cfg(tmp_path, name, groups=groups, xv=xv, wiki=wiki))


def _edge(eid, obj, *, source_id=None, origin=None, relation="works_as",
          subject="user", author=EvidenceAuthor.USER,
          disc=Disclosure.MENTIONABLE, evidence_ref="ev", **kw) -> Edge:
    return Edge(id=eid, user_id=U, subject=subject, relation=relation,
                object=obj,
                provenance=Provenance(author_of_evidence=author,
                                      evidence_ref=evidence_ref,
                                      disclosure=disc, source_id=source_id,
                                      origin=origin), **kw)


def _episode(eid, summary, *, source_id=None, date="2026-08-01", **kw) -> Episode:
    return Episode(id=eid, user_id=U, date=date, summary=summary,
                   provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                         evidence_ref="ev",
                                         source_id=source_id), **kw)


ONE_GROUP = {"team-a": [A1]}


def _mixed_store(mem):
    """One store, three scopes: agent-1 (the principal's), agent-2 (cross),
    and a host-produced identity-less record (the C3 shared floor)."""
    mem.store.add_edge(_edge("e-own", "pilot at Aerodyne", source_id="agent-1"))
    mem.store.add_edge(_edge("e-cross", "cellist at Thornbury", source_id="agent-2",
                             subject="person:tansy", relation="works_as"))
    mem.store.add_edge(_edge("e-shared", "baker at Ovenwright", subject="person:kit"))
    mem.store.add_episode(_episode("ep-own", "pilot roster discussed",
                                   source_id="agent-1"))
    mem.store.add_episode(_episode("ep-cross", "cellist tour discussed",
                                   source_id="agent-2"))


def _ids(records):
    return sorted(r.id for r in records)


# --------------------------------------------------------------------------- #
# V1 — `test_no_principal_is_byte_identical`
# --------------------------------------------------------------------------- #

def test_no_principal_is_byte_identical(tmp_path, monkeypatch):
    """The migration invariant, over a FIXED store state, on the FULL `Recall`
    value — not a summary, not the rendered context alone.

    Two independent proofs, because either alone is weak. (1) EQUALITY:
    configuring a scope policy changes nothing on the unscoped surface —
    every field of the complete `Recall` (context, grounded, unverified,
    edges, episodes, tokens_estimated, truncated, contested) is equal
    against a Memory with no policy at all, over the same database file.
    (2) NON-EXECUTION: with `principal=None` not one line of scope code runs
    — `ScopeView` is replaced by a detonator, and recall still returns."""
    mem = _mem(tmp_path, "fixed.db")
    _mixed_store(mem)
    mem.store.add_edge(_edge("e-flag", "trumpeter at Brasswork",
                             subject="person:rye", needs_confirmation=True))
    mem.close()

    plain = _mem(tmp_path, "fixed.db")
    scoped_cfg = _mem(tmp_path, "fixed.db", groups=ONE_GROUP)
    for query in ("pilot Aerodyne", "cellist", "baker trumpeter", "nothing here"):
        a = plain.recall(U, query)
        b = scoped_cfg.recall(U, query)
        assert a == b, f"configuring a policy changed the UNSCOPED recall for {query!r}"
        # the full value, field by field — an == that silently compared
        # identity would pass vacuously
        assert (a.context, a.grounded, a.unverified, a.tokens_estimated,
                a.truncated) == (b.context, b.grounded, b.unverified,
                                 b.tokens_estimated, b.truncated)
        assert _ids(a.edges) == _ids(b.edges)
        assert _ids(a.episodes) == _ids(b.episodes)
        assert a.contested == b.contested

    class _Detonator:
        def __init__(self, *a, **k):
            raise AssertionError("scope code ran on an unscoped call")

    monkeypatch.setattr(scope_read, "ScopeView", _Detonator)
    assert scoped_cfg.recall(U, "pilot Aerodyne").edges          # still works
    assert scoped_cfg.recall(U) is not None                      # proactive too
    plain.close()
    scoped_cfg.close()


def test_a_principal_without_a_policy_refuses(tmp_path):
    """§2c / R2-2: feature-disabled NEVER silently degrades to an unscoped,
    fully-assertable view."""
    mem = _mem(tmp_path)                                  # no policy configured
    _mixed_store(mem)
    for call in (lambda: mem.recall(U, "pilot", principal=A1),
                 lambda: mem.recall(U, principal=A1),
                 lambda: mem.answer(U, "pilot", principal=A1)):
        with pytest.raises(ScopeError, match="no scope policy is configured"):
            call()


def test_a_source_id_less_principal_refuses(tmp_path):
    """0006 I13: an absent `source_id` yields no groupable identity, so it
    cannot be a principal."""
    mem = _mem(tmp_path, groups=ONE_GROUP)
    _mixed_store(mem)
    with pytest.raises(ScopeError, match="source_id"):
        mem.recall(U, "pilot", principal=Identity("org-a", None))


@pytest.mark.parametrize("bad", ["agent-1", {"source_id": "agent-1"}, 7, object()])
def test_a_non_identity_principal_refuses(tmp_path, bad):
    """Strict types (§2c): a principal is an `Identity`, not a look-alike."""
    mem = _mem(tmp_path, groups=ONE_GROUP)
    with pytest.raises(ScopeError, match="Identity"):
        mem.recall(U, "pilot", principal=bad)


def test_a_malformed_policy_raises_at_config_load_not_at_recall(tmp_path):
    """§7: misconfiguration fails at LOAD. Each cell is refused before any
    Memory exists — there is no state in which a recall can meet it."""
    with pytest.raises(ScopeError):                        # non-Identity member
        MemoryConfig(db_path=str(tmp_path / "x.db"),
                     scope_groups={"g": ["agent-1"]})
    with pytest.raises(ScopeError):                        # I13 non-groupable
        MemoryConfig(db_path=str(tmp_path / "x.db"),
                     scope_groups={"g": [Identity("org-a", None)]})
    with pytest.raises(ScopeError):                        # a SET is not a rule grammar
        MemoryConfig(db_path=str(tmp_path / "x.db"),
                     scope_groups={"g": {A1}})
    with pytest.raises(ScopeError):                        # digest overlap
        MemoryConfig(db_path=str(tmp_path / "x.db"),
                     scope_groups={"g": [A1], "h": [A1]})
    with pytest.raises(ValueError):                        # not a REAL bool
        MemoryConfig(db_path=str(tmp_path / "x.db"), scope_groups={},
                     cross_scope_visible=1)
    with pytest.raises(ValueError):                        # a flag with no policy
        MemoryConfig(db_path=str(tmp_path / "x.db"), cross_scope_visible=True)
    # and the CONFIGURED-EMPTY state is valid, not a malformation
    mem = _mem(tmp_path, groups={})
    _mixed_store(mem)
    r = mem.recall(U, "pilot Aerodyne baker cellist", principal=A1)
    assert "e-own" in _ids(r.edges) and "e-shared" in _ids(r.edges)
    assert "e-cross" not in _ids(r.edges)                  # ungrouped ⇒ CROSS


# --------------------------------------------------------------------------- #
# V2 — `test_same_scope_grants_nothing`
# --------------------------------------------------------------------------- #

def test_same_scope_grants_nothing(tmp_path):
    """§4b, RESTRICT-ONLY, by ENUMERATED TEMPTATION.

    The predicate first: over the FULL cross-product of the decision table
    and the 0011 seam's values, no cell ever turns a non-assertable record
    assertable. Then the tempting cells by name, through a real scoped
    recall — most of all THE OWN-INFERENCE RE-ASSERTABILITY CELL: a
    third-party inference (`use_only`) that the principal's OWN source
    produced is still not assertable. Owning the source is not confirming
    the claim."""
    for name, decision in DECISION_TABLE.items():
        for ent in (None, True, False):
            assert gate.scoped_assertable(False, decision,
                                          subject_entitlement=ent) is False, (
                f"{name} × entitlement={ent} GRANTED assertability")
        # and the visible/own cells never invent it either
        assert gate.scoped_assertable(True, decision) is (
            decision[0] and decision[1] != "third-party-shaped")

    mem = _mem(tmp_path, groups=ONE_GROUP)
    # every temptation, all OWN-scope (the principal's own source_id)
    mem.store.add_edge(_edge("t-useonly", "consultant at Vale", source_id="agent-1",
                             subject="person:vale", disc=Disclosure.USE_ONLY))
    mem.store.add_edge(_edge("t-quar", "owes 900", source_id="agent-1",
                             subject="org:scamco", relation="third_party_claim",
                             author=EvidenceAuthor.THIRD_PARTY,
                             disc=Disclosure.QUARANTINED))
    mem.store.add_edge(_edge("t-stale", "cook at Ember", source_id="agent-1",
                             subject="person:ash", needs_confirmation=True))
    mem.store.add_edge(_edge("t-ungrounded", "sailor at Keel", source_id="agent-1",
                             subject="person:brae", ungrounded=True))
    q = "consultant Vale owes 900 cook Ember sailor Keel"
    r = mem.recall(U, q, principal=A1)
    by_id = {e.id: e for e in r.edges}
    assert set(by_id) >= {"t-useonly", "t-quar", "t-stale", "t-ungrounded"}
    # NOTHING is lifted by being same-scope:
    assert by_id["t-useonly"].use_only and not by_id["t-useonly"].assertable
    assert by_id["t-quar"].quarantined and not by_id["t-quar"].assertable
    assert by_id["t-stale"].needs_confirmation is True
    assert by_id["t-ungrounded"].ungrounded is True
    assert by_id["t-useonly"].provenance.disclosure is Disclosure.USE_ONLY
    assert by_id["t-quar"].provenance.disclosure is Disclosure.QUARANTINED
    # and the rendered partition agrees: own-scope fenced material stays fenced
    assert "consultant at Vale" not in r.grounded
    assert "consultant at Vale" in r.unverified


# --------------------------------------------------------------------------- #
# V3 — `test_existence_non_leakage`
# --------------------------------------------------------------------------- #

def test_existence_non_leakage(tmp_path):
    """N-1: a principal-facing response is INDISTINGUISHABLE between
    nothing-exists and everything-withheld — equality over the FULL `Recall`
    value, every structured carrier included. A scope-blinded agent saying
    "no record" is isolation WORKING, not abstention failing."""
    empty = _mem(tmp_path, "empty.db", groups=ONE_GROUP)
    withheld = _mem(tmp_path, "withheld.db", groups=ONE_GROUP)
    # everything out of scope: cross-scope records, an UNRESOLVED derivative,
    # and a live CONTENTION between two out-of-scope parties
    withheld.store.add_edge(_edge("w1", "cellist at Thornbury", source_id="agent-2",
                                  subject="person:tansy"))
    withheld.store.add_episode(_episode("wep", "tour discussed", source_id="agent-2"))
    withheld.store.add_edge(_edge("w-legacy", "system digest", source_id="agent-2",
                                  subject="person:mo", author=EvidenceAuthor.SYSTEM,
                                  evidence_ref="op-0123456789ab"))
    withheld.store.add_edge(_edge("wp", "CFO at Acme", source_id="agent-2",
                                  subject="person:cross"))
    apply_supersession(withheld.store,
                       _edge("wi", "unemployed", source_id="agent-2",
                             subject="person:cross", author=EvidenceAuthor.SYSTEM),
                       withheld.config.relations)

    for query in ("cellist Thornbury", "CFO Acme unemployed", "anything"):
        a = empty.recall(U, query, principal=A1)
        b = withheld.recall(U, query, principal=A1)
        assert a == b, (f"withheld differs from empty on {query!r}:\n"
                        f"{a!r}\n{b!r}")
        assert b.edges == [] and b.episodes == [] and b.contested == []
        assert "Thornbury" not in b.context and "Acme" not in b.context
    # the unscoped surface still sees all of it — withholding is the
    # PRINCIPAL's view, never a deletion
    assert withheld.recall(U, "cellist Thornbury").edges


# --------------------------------------------------------------------------- #
# V4 — `test_cross_scope_supersession_rendering`
# --------------------------------------------------------------------------- #

def test_cross_scope_supersession_rendering(tmp_path):
    """N-2 on EVERY carrier: supersession/contention STATUS is global truth
    and renders; the cross-scope party's CONTENT and ATTRIBUTION do not.

    The group survives (the principal owns a member), the invisible
    challenger degrades to content-free `ContestedLinkage`, and its value
    appears nowhere — not in `context`, not in `Recall.edges`, not in the
    serialized group."""
    mem = _mem(tmp_path, groups=ONE_GROUP)
    mem.store.add_edge(_edge("p", "CFO at Acme", source_id="agent-1"))
    apply_supersession(mem.store,
                       _edge("i", "unemployed at Thornbury", source_id="agent-2",
                             author=EvidenceAuthor.SYSTEM),
                       mem.config.relations)

    unscoped = mem.recall(U, "CFO Acme unemployed")
    assert len(unscoped.contested) == 1
    assert _ids(unscoped.contested[0].exposed) == ["i", "p"]      # both, today

    r = mem.recall(U, "CFO Acme unemployed", principal=A1)
    assert len(r.contested) == 1, "the contention itself is global truth"
    g = r.contested[0]
    assert _ids(g.exposed) == ["p"]                                # own member only
    assert [lk.edge_id for lk in g.linkage] == ["i"]               # status, not content
    assert "unemployed" not in g.model_dump_json()                 # content-free
    assert "unemployed" not in r.context and "unemployed" not in r.grounded
    assert "i" not in _ids(r.edges)                                # not in the edge set
    assert "CONTESTED" in r.context                                # the status renders

    # and the supersession STATUS of the principal's OWN record is untouched:
    own = next(e for e in r.edges if e.id == "p")
    assert own.active and own.object == "CFO at Acme"


def test_a_group_with_nothing_visible_does_not_exist(tmp_path):
    """The N-1 corollary of N-2: linkage for an invisible challenger is only
    ever attached to a group the principal can SEE. A wholly out-of-scope
    contention produces NO group — otherwise the all-withheld store would be
    distinguishable from the empty one."""
    mem = _mem(tmp_path, groups=ONE_GROUP)
    mem.store.add_edge(_edge("p", "CFO at Acme", source_id="agent-2"))
    apply_supersession(mem.store,
                       _edge("i", "unemployed", source_id="agent-2",
                             author=EvidenceAuthor.SYSTEM),
                       mem.config.relations)
    assert mem.recall(U, "CFO Acme", principal=A1).contested == []
    assert len(mem.recall(U, "CFO Acme").contested) == 1        # unscoped: intact


# --------------------------------------------------------------------------- #
# V5 — `test_scoped_recall_excludes_wiki`
# --------------------------------------------------------------------------- #

MARKER = "WIKI-SYNTHESIS-MARKER-a41f"


def test_scoped_recall_excludes_wiki(tmp_path):
    """§4d: the compiled wiki is a store-wide LLM re-rendering — a synthesis
    path the scope machinery does not control, i.e. a laundering site — so a
    principal-bearing response carries NO wiki content, on the rendered
    context and on the structured carriers, through recall AND answer. Not
    filtered: not compiled, not consulted, not rendered."""
    llm = _Fake(f"{MARKER} the user is a pilot and a cellist.")
    mem = _mem(tmp_path, wiki=1, llm=llm, groups=ONE_GROUP)
    _mixed_store(mem)

    unscoped = mem.recall(U, "pilot Aerodyne")
    assert MARKER in unscoped.context, "the fixture must actually compile a wiki"

    scoped = mem.recall(U, "pilot Aerodyne", principal=A1)
    assert MARKER not in scoped.context
    assert MARKER not in scoped.grounded and MARKER not in scoped.unverified
    assert MARKER not in repr(scoped.edges) + repr(scoped.episodes)
    assert MARKER not in repr(scoped.contested)

    llm.prompts.clear()
    mem.answer(U, "pilot Aerodyne", principal=A1)
    assert all(MARKER not in p for p in llm.prompts), (
        "the wiki reached the gate prompt through answer()")
    # the queryless briefing has never used the wiki, and still does not
    assert MARKER not in mem.recall(U, principal=A1).context


# --------------------------------------------------------------------------- #
# V6 — `test_unknown_identity_is_not_a_principal`
# --------------------------------------------------------------------------- #

def test_unknown_identity_is_not_a_principal(tmp_path):
    """absent == absent is NEVER same-scope (§2c's producers row, C3).

    A host-produced identity-less record is SHARED-visible and gate-unchanged
    — the floor — but it never becomes anyone's OWN scope, and an
    identity-less party can never be a principal at all."""
    mem = _mem(tmp_path, groups=ONE_GROUP)
    _mixed_store(mem)
    view = mem._scope_view(U, A1)
    shared = next(e for e in mem.store.edges(U) if e.id == "e-shared")
    assert view.evidence(shared) is SHARED
    assert view.decision(shared) == (True, "shared")            # visible, not OWN

    # the identity-less record is visible to a DIFFERENT scope too — shared is
    # shared, never "own" by coincidence of both sides being absent
    other = validate_policy({"team-b": [A2]},
                            local_origin=mem.store.local_origin())
    v2 = ScopeView(mem.store, U, A2, other)
    assert v2.evidence(shared) is SHARED and v2.decision(shared)[0]

    # and absence never promotes itself into a principal
    for bad in (Identity(None, None), Identity("org-a", None)):
        with pytest.raises(ScopeError, match="source_id"):
            ScopeView(mem.store, U, bad, view.policy)


# --------------------------------------------------------------------------- #
# V7 — `test_policy_evaluates_resolved_identity`
# --------------------------------------------------------------------------- #

def test_policy_evaluates_resolved_identity(tmp_path):
    """0006 I9: an ABSENT origin resolves to this store's `store_identity`
    singleton BEFORE any comparison — and the policy is evaluated over that
    resolved pair, at BOTH ends.

    The rule is written with the store's EXPLICIT origin, the record and the
    principal carry NONE, and they must still meet: policy-over-identity, not
    policy-over-raw-fields."""
    mem = _mem(tmp_path)
    local = mem.store.local_origin()
    mem.close()
    groups = {"team-a": [Identity(local, "agent-1"),      # explicit origin
                         Identity(local, "agent-2")]}
    mem = _mem(tmp_path, groups=groups)                   # same db file
    mem.store.add_edge(_edge("e-own", "pilot at Aerodyne", source_id="agent-1"))
    mem.store.add_edge(_edge("e-peer", "cellist at Thornbury", source_id="agent-2",
                             subject="person:tansy"))
    mem.store.add_edge(_edge("e-out", "baker at Ovenwright", source_id="agent-3",
                             subject="person:kit"))
    # a FOREIGN origin with the SAME source_id is a different identity — the
    # namespace is the origin, and resolution never collapses it
    mem.store.add_edge(_edge("e-foreign", "forger at Elsewhere", source_id="agent-1",
                             origin="org-elsewhere", subject="person:vex"))

    r = mem.recall(U, "pilot cellist baker forger", principal=A1)   # absent origin
    assert _ids(r.edges) == ["e-own", "e-peer"]
    assert "e-foreign" not in _ids(r.edges) and "e-out" not in _ids(r.edges)


# --------------------------------------------------------------------------- #
# V8 — `test_filter_rails`
# --------------------------------------------------------------------------- #

def test_filter_rails(tmp_path):
    """§4e M-1..M-4.

    M-2 is the load-bearing one: filters run AFTER scope, WITHIN the visible
    set, and narrow only — so a filter naming an out-of-scope record's
    attributes is not an oracle. M-3's empty-result report is computed inside
    the visible set. M-1: a filtered result still carries full disclosure.
    M-4: source fields evaluate over resolved identity, and the grammar is
    CLOSED."""
    mem = _mem(tmp_path, groups=ONE_GROUP)
    mem.store.add_edge(_edge("f-own", "pilot at Aerodyne", source_id="agent-1"))
    mem.store.add_edge(_edge("f-own2", "sailor at Keel", source_id="agent-1",
                             subject="person:brae", needs_confirmation=True))
    mem.store.add_edge(_edge("f-cross", "cellist at Thornbury", source_id="agent-2",
                             subject="person:tansy"))
    q = "pilot sailor cellist"

    # M-2: narrowing within the visible set
    r = mem.recall(U, q, principal=A1, subject="person:brae")
    assert _ids(r.edges) == ["f-own2"]
    # …and a filter that names ONLY out-of-scope material yields nothing —
    # never the record, never a hint that it exists
    r = mem.recall(U, q, principal=A1, subject="person:tansy")
    assert r.edges == []
    assert "Thornbury" not in r.context and "cellist" not in r.context

    # M-3: the empty-result report is principal-facing and counted WITHIN the
    # visible set (2 visible records, not the 3 that exist)
    assert "matched 0 of the 2 records visible to you" in r.context

    # M-1: filters SELECT, never STRIP — the survivor keeps its full disclosure
    r = mem.recall(U, q, principal=A1, source_id="agent-1")
    assert _ids(r.edges) == ["f-own", "f-own2"]
    assert next(e for e in r.edges if e.id == "f-own2").needs_confirmation is True

    # M-4 + the CLOSED grammar
    assert _ids(mem.recall(U, q, principal=A1, relation="works_as").edges) == \
        ["f-own", "f-own2"]
    with pytest.raises(ScopeError, match="CLOSED"):
        mem.recall(U, q, principal=A1, note="pilot")
    with pytest.raises(ScopeError, match="CLOSED"):
        mem.recall(U, q, principal=A1, object="pilot at Aerodyne")
    with pytest.raises(ScopeError, match="non-empty"):
        mem.recall(U, q, principal=A1, subject="")

    # the filters are available UNSCOPED too, and narrow the same way
    assert _ids(mem.recall(U, q, subject="person:tansy").edges) == ["f-cross"]


# --------------------------------------------------------------------------- #
# V9 — `test_gate_seam_reserved_for_0011`
# --------------------------------------------------------------------------- #

def test_gate_seam_reserved_for_0011():
    """V9: the 0011 SUBJECT dimension has a NAMED, INERT seam — and the seam
    can only ever restrict.

    This is the check that fails if a later change quietly deletes the
    parameter (0011 then has nowhere to land) or turns it into a grant."""
    sig = inspect.signature(gate.scoped_assertable)
    p = sig.parameters.get("subject_entitlement")
    assert p is not None, "the 0011 seam parameter is gone"
    assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is None
    assert "0011" in gate.scoped_assertable.__doc__

    # INERT in v1: None and True are the same answer, on every cell
    for decision in DECISION_TABLE.values():
        for record_assertable in (True, False):
            base = gate.scoped_assertable(record_assertable, decision)
            assert gate.scoped_assertable(record_assertable, decision,
                                          subject_entitlement=None) is base
            assert gate.scoped_assertable(record_assertable, decision,
                                          subject_entitlement=True) is base
            # …and the only value that acts, RESTRICTS
            assert gate.scoped_assertable(record_assertable, decision,
                                          subject_entitlement=False) is False


# --------------------------------------------------------------------------- #
# V11 — `test_all_read_surfaces_scoped`
# --------------------------------------------------------------------------- #

def test_all_read_surfaces_scoped(tmp_path):
    """External F3: `answer()` and the proactive briefing THREAD the
    principal, and the structured carriers on every one of them carry only
    visible records.

    `answer` is checked on the bytes the model actually received — a path
    that recalled unscoped and filtered afterwards would still leak into the
    prompt, and this is the check that catches it."""
    llm = _Fake("ok")
    mem = _mem(tmp_path, llm=llm, groups=ONE_GROUP)
    _mixed_store(mem)
    mem.store.add_edge(_edge("e-due", "file taxes by 2026-08-20", source_id="agent-1",
                             subject="task:tax", relation="deadline"))
    mem.store.add_edge(_edge("e-due-cross", "renew visa by 2026-08-19",
                             source_id="agent-2", subject="task:visa",
                             relation="deadline"))

    # --- answer(): the principal reaches the internal recall
    llm.prompts.clear()
    mem.answer(U, "who works where", principal=A1)
    joined = "\n".join(llm.prompts)
    assert "Aerodyne" in joined                                  # own scope arrives
    assert "Thornbury" not in joined                             # cross scope does not
    assert "cellist tour discussed" not in joined                # nor its episodes

    # --- queryless recall → proactive assembly, filtered BEFORE assembly
    p = mem.recall(U, principal=A1)
    assert _ids(p.edges) == ["e-due"]
    assert "renew visa" not in p.context and "visa" not in p.context
    assert all(e.provenance.source_id == "agent-1" for e in p.edges)
    # unscoped, both commitments brief as they always have
    assert _ids(mem.recall(U).edges) == ["e-due", "e-due-cross"]

    # --- query recall: every structured carrier
    r = mem.recall(U, "pilot cellist baker", principal=A1)
    assert _ids(r.edges) == ["e-own", "e-shared"]
    assert _ids(r.episodes) == ["ep-own"]
    for e in r.edges + r.episodes:
        assert e.provenance.source_id in (None, "agent-1")


def test_cross_scope_visible_is_visible_but_never_assertable(tmp_path):
    """The `cross_scope_visible` cell: policy admits the record, and §4b
    pins it to the THIRD-PARTY-TESTIMONY shape — visible, fenced, never
    assertable, and never volunteered by the proactive surface."""
    mem = _mem(tmp_path, groups=ONE_GROUP, xv=True)
    _mixed_store(mem)
    r = mem.recall(U, "pilot cellist", principal=A1)
    cross = next(e for e in r.edges if e.id == "e-cross")
    assert cross.use_only and not cross.assertable            # RESTRICTED, not granted
    assert "cellist at Thornbury" in r.unverified             # under the fence
    assert "cellist at Thornbury" not in r.grounded
    # own-scope material is untouched by the shaping
    own = next(e for e in r.edges if e.id == "e-own")
    assert own.assertable and own.provenance.disclosure is Disclosure.MENTIONABLE
    assert own.provenance.derived_from is None
    # THE OTHER RECORD KIND, and the other routing field: the gate routes an
    # EPISODE on `third_party_influenced`, not on disclosure, so shaping only
    # the edge lever would leave a cross-scope EPISODE in the GROUNDED block.
    cross_ep = next(e for e in r.episodes if e.id == "ep-cross")
    assert cross_ep.provenance.third_party_influenced
    assert "cellist tour discussed" not in r.grounded
    assert "cellist tour discussed" in r.unverified
    own_ep = next(e for e in r.episodes if e.id == "ep-own")
    assert not own_ep.provenance.third_party_influenced
    # proactive VOLUNTEERS, so fenced cross-scope material never surfaces there
    mem.store.add_edge(_edge("x-due", "renew visa by 2026-08-19", source_id="agent-2",
                             subject="task:visa", relation="deadline"))
    assert "visa" not in mem.recall(U, principal=A1).context

    # and the shaping NEVER widens: an already-quarantined cross-scope claim
    # keeps its quarantine rather than being moved to the softer tier
    mem.store.add_edge(_edge("x-quar", "owes 900", source_id="agent-2",
                             subject="org:scamco", relation="third_party_claim",
                             author=EvidenceAuthor.THIRD_PARTY,
                             disc=Disclosure.QUARANTINED))
    r = mem.recall(U, "owes 900", principal=A1)
    q = next(e for e in r.edges if e.id == "x-quar")
    assert q.provenance.disclosure is Disclosure.QUARANTINED and q.quarantined


def test_the_gate_predicate_is_the_authority_not_decoration(tmp_path,
                                                            monkeypatch):
    """§4b puts the relation IN THE GATE. A `scoped_assertable` that nothing
    consults would be a docstring, not a rail — so this replaces it and
    checks that the read path's shaping actually follows it.

    (The substitute grants nothing: it makes the predicate MORE permissive,
    and the assertion is that the fence then does not appear. A predicate the
    shaping ignored would fence anyway and fail here.)"""
    mem = _mem(tmp_path, groups=ONE_GROUP, xv=True)
    _mixed_store(mem)
    assert next(e for e in mem.recall(U, "cellist", principal=A1).edges
                if e.id == "e-cross").use_only          # fenced by default

    monkeypatch.setattr(gate, "scoped_assertable",
                        lambda assertable, decision, **kw: assertable)
    cross = next(e for e in mem.recall(U, "cellist", principal=A1).edges
                 if e.id == "e-cross")
    assert not cross.use_only, (
        "the shaping fenced a record the gate predicate called assertable — "
        "scoped_assertable is not actually the authority")


# --------------------------------------------------------------------------- #
# V12 — `test_read_surface_manifest_is_total`
# --------------------------------------------------------------------------- #

def test_read_surface_manifest_is_total():
    """V12: the generated §4f manifest and the code agree — AND the check
    actually catches a new surface.

    The second half is the point. A gate that only ever runs on the current
    tree proves nothing about the tree that adds a read path, so a synthetic
    module with an un-dispositioned public method is fed to the same
    enumerator; it must be reported."""
    r = subprocess.run([sys.executable, str(ROOT / "specs" / "read_surfaces.py"),
                        "--check"], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, (
        f"the read-surface manifest and the code disagree:\n{r.stdout}\n{r.stderr}\n"
        f"Regenerate with `python3 specs/read_surfaces.py --write` and give "
        f"every new surface a disposition in specs/read_surface_dispositions.py.")

    sys.path.insert(0, str(ROOT / "specs"))
    import read_surfaces
    from read_surface_dispositions import DISPOSITIONS

    synthetic = (
        "class Memory:\n"
        "    def recall(self, user_id, query=None, *, principal=None): ...\n"
        "    def peek_everything(self, user_id) -> list:\n"
        "        return []\n")
    found = read_surfaces.enumerate_surfaces(synthetic, "__init__", "Memory")
    assert "Memory.peek_everything" in found
    bad = read_surfaces.problems(found, DISPOSITIONS)
    assert any("UN-DISPOSITIONED" in b and "peek_everything" in b for b in bad), bad

    # a row that CLAIMS a threading the code does not do is caught too
    lying = read_surfaces.enumerate_surfaces(
        "class Memory:\n    def recall(self, user_id, query=None): ...\n",
        "__init__", "Memory")
    assert any("Memory.recall" in b and "NO `principal`" in b
               for b in read_surfaces.problems(lying, DISPOSITIONS))


def test_operator_surfaces_take_no_principal(tmp_path):
    """§2's operator row, recorded as a DECISION rather than left as an
    omission: `introspect`, `export_memory` and `forget` are the OPERATOR's
    right-to-know / portability / erasure surfaces. They take no principal
    and stay unscoped in v1 — per-principal introspection is a recorded
    widening, and a scoped erasure would leave residue the caller believes
    is gone."""
    sys.path.insert(0, str(ROOT / "specs"))
    from read_surface_dispositions import DISPOSITIONS
    mem = _mem(tmp_path, groups=ONE_GROUP)
    _mixed_store(mem)
    for name in ("introspect", "export_memory", "forget"):
        fn = getattr(Memory, name)
        assert "principal" not in inspect.signature(fn).parameters
        d = DISPOSITIONS[f"Memory.{name}"]
        assert d["principal"] == "none" and "UNSCOPED" in d["disposition"]
    with pytest.raises(TypeError):
        mem.introspect(U, principal=A1)
    # and the unscoped behaviour is the WHOLE store, cross-scope included
    out = mem.introspect(U)
    assert out["facts"] >= 3
    r = mem.export_memory(U, tmp_path / "out.jsonl")
    assert r["edges"] >= 3


# --------------------------------------------------------------------------- #
# V13 — `test_unresolved_derivative_fail_closed`
# --------------------------------------------------------------------------- #

class _RowStore:
    """A store stub carrying LEDGER ROWS the 0021 writers do not yet emit, so
    the read path's evidence chain can be exercised now (§4a-iii)."""

    def __init__(self, local, rows, edges=()):
        self._local, self._rows, self._edges = local, rows, list(edges)

    def local_origin(self):
        return self._local

    def contributions(self, user_id, kind, rid):
        return [SimpleNamespace(site=r.get("site"),
                                identity_digest=r.get("identity_digest"),
                                op_key=r.get("op_key"),
                                contributor_ref=r.get("contributor_ref"),
                                contributor_type=r.get("contributor_type", "edge"),
                                evidence_ref_digest=r.get("evidence_ref_digest"),
                                payload=r.get("payload") or {})
                for r in self._rows.get(rid, [])]

    def edges(self, user_id, active_only=False, include_quarantined=False):
        return list(self._edges)


def test_unresolved_derivative_fail_closed(tmp_path):
    """V13 (external F1): missing membership evidence NEVER silently means
    "shared". An UNRESOLVED derivative is invisible to EVERY scoped
    principal and visible on the unscoped surface — on every carrier.

    Three populations, three cells: the LEGACY pre-0021 output (which still
    carries the copied identity and would otherwise read as own-scope); the
    consolidation output whose ledger evidence is absent/incomplete; and the
    ABSORPTION SURVIVOR whose ledger says another scope contributed."""
    mem = _mem(tmp_path, groups=ONE_GROUP)
    # (1) the legacy derivative: SYSTEM author, `op-<12hex>` evidence_ref, and
    # the INHERITED identity of the principal's own scope — the exact shape
    # that must NOT be believed
    mem.store.add_edge(_edge("d-legacy", "digest of pilot facts", source_id="agent-1",
                             subject="person:mo", author=EvidenceAuthor.SYSTEM,
                             evidence_ref="op-0123456789ab"))
    mem.store.add_edge(_edge("d-ok", "pilot at Aerodyne", source_id="agent-1"))
    mem.store.add_episode(_episode("d-ep", "pilot roster discussed",
                                   source_id="agent-1"))

    scoped = mem.recall(U, "pilot digest consolidated", principal=A1)
    assert "d-legacy" not in _ids(scoped.edges)
    assert "digest of pilot facts" not in scoped.context
    assert _ids(scoped.edges) == ["d-ok"] and _ids(scoped.episodes) == ["d-ep"]

    unscoped = mem.recall(U, "pilot digest consolidated")
    assert "d-legacy" in _ids(unscoped.edges)                 # visible unscoped

    local = mem.store.local_origin()
    from veracium.scope import digest_of
    d1, d2 = digest_of(A1, local), digest_of(A2, local)

    # (2) a consolidation OUTPUT whose ledger evidence is absent — the
    # imported/legacy/recovered population. (The fenced 0010 primitives are
    # the only writers of lineage, so the record is built directly.)
    out_ep = _episode("d-out", "consolidated pilot history",
                      source_id="agent-1", lineage=["hist-ep-1", "hist-ep-2"])
    pol0 = validate_policy({"team-a": [A1]}, local_origin=local)
    no_rows = ScopeView(_RowStore(local, {}), U, A1, pol0)
    assert no_rows.evidence(out_ep) is UNRESOLVED
    assert not no_rows.visible(out_ep) and no_rows.scoped([out_ep]) == []
    # …and INCOMPLETE evidence is the same answer: one row for two contributors
    partial = ScopeView(_RowStore(local, {"d-out": [
        {"site": "consolidation", "identity_digest": d1}]}), U, A1, pol0)
    assert partial.evidence(out_ep) is UNRESOLVED
    # the complete, single-scope case resolves — the check is not vacuous
    complete = ScopeView(_RowStore(local, {"d-out": [
        {"site": "consolidation", "identity_digest": d1},
        {"site": "consolidation", "identity_digest": d1}]}), U, A1, pol0)
    assert complete.evidence(out_ep) == d1 and complete.visible(out_ep)

    # (3) the absorption survivor, on the ledger rows themselves
    survivor = _edge("s", "merged fact", source_id="agent-1")
    policy = validate_policy({"team-a": [A1]}, local_origin=local)

    # a) a CLOSED row set (typed `contributor_ref`, contributor pruned under
    # 0014 A10) whose every digest is the survivor's OWN → resolved, visible
    clean = ScopeView(_RowStore(local, {"s": [{"site": "absorption",
                                               "identity_digest": d1,
                                               "contributor_ref": "b"}]},
                                [survivor]), U, A1, policy)
    assert clean.evidence(survivor) == d1 and clean.visible(survivor)

    # b) the ledger says ANOTHER scope contributed → UNRESOLVED, fail closed
    mixed = ScopeView(_RowStore(local, {"s": [{"site": "absorption",
                                               "identity_digest": d1,
                                               "contributor_ref": "b"},
                                              {"site": "absorption",
                                               "identity_digest": d2,
                                               "contributor_ref": "c"}]},
                                [survivor]), U, A1, policy)
    assert mixed.evidence(survivor) is UNRESOLVED
    assert not mixed.visible(survivor) and mixed.scoped([survivor]) == []

    # c) a REF-LESS legacy row whose contributor record is gone: the closure
    # returns None, and None IS UNRESOLVED — before `membership` ever runs
    orphan = ScopeView(_RowStore(local, {"s": [{"site": "absorption",
                                                "identity_digest": d1,
                                                "contributor_ref": None}]},
                                 [survivor]), U, A1, policy)
    assert orphan.evidence(survivor) is UNRESOLVED
    assert not orphan.visible(survivor)

    # d) the TRANSITIVE cell: C's own row names only B (== C's scope), but the
    # CLOSED set reaches A's foreign digest through the typed ref → UNRESOLVED
    chain = _RowStore(local, {
        "s": [{"site": "absorption", "identity_digest": d1,
               "contributor_ref": "b"},
              {"site": "scope-attribution", "identity_digest": d2,
               "contributor_ref": "a", "payload": {"flattened": True}}],
        "b": [{"site": "absorption", "identity_digest": d2,
               "contributor_ref": "a"}],
    }, [survivor])
    view = ScopeView(chain, U, A1, policy)
    assert view.evidence(survivor) is UNRESOLVED, (
        "the single-level read called this own-scope; the closure must not")
    assert not view.visible(survivor)
