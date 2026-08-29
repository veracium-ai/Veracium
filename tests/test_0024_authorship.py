"""specs/0024 §6 — authorship before structural quarantine (U1–U7),
as amended by A1 (ACCEPTED external round 24, 2026-08-24): the
re-disposition disclosure is UNIFORM USE_ONLY — may inform, never
assert. The frozen invariant surface, each check under its canonical
name, plus the baseline-derived regression shapes (A08 movement to
USE_ONLY; B02/B07 relay preservation with the out-of-scope statement)
and the revoked-floor vector."""

import ast
import json
import pathlib

import pytest

from veracium import EvidenceAuthor, EvidenceContext, SqliteStore
from veracium.ingest import ingest_event
from veracium.schema import (DEFAULT_RELATIONS, Disclosure,
                             QUARANTINE_RELATION, UNCLASSIFIED_RELATION)

U = "u-0024"


def _llm_for(triples):
    payload = json.dumps({"triples": triples, "episode": "e"})

    def llm(prompt, *, system=None, role="distill", json_schema=None):
        if role == "distill-retry":
            return json.dumps({"triples": []})
        return payload
    return llm


def _ingest(store, triples, *, author=EvidenceAuthor.USER, derived=None):
    # pre-E4 tests meant the pre-E4 default: a declared-direct capture when
    # no derivation was stated (specs/0011 §4d migration)
    ctx = EvidenceContext.direct() if derived is None else None
    return ingest_event(store, _llm_for(triples), U, event_text="t",
                        author=author, derived_from=derived, context=ctx,
                        date="2026-08-23", relations=DEFAULT_RELATIONS)


def _tpc(subject, obj="claims something"):
    return {"subject": subject, "relation": QUARANTINE_RELATION,
            "object": obj}


# ---- U1: the complementary domain quarantines ------------------------------

@pytest.mark.parametrize("subject", [
    "landlord", "the user's doctor", "['user']", "{'name': 'user'}",
    "  ", "userx", "the user"])
def test_relayed_third_party_claim_still_quarantines(subject):
    s = SqliteStore(":memory:")
    r = _ingest(s, [_tpc(subject)])
    edges = s.edges(U, active_only=False)
    if not edges:
        return    # falsy-after-parse subjects drop at completeness — fine
    assert all(e.provenance.disclosure == Disclosure.QUARANTINED
               for e in edges), subject
    assert r["redispositioned"] == 0


# ---- U2: EXACT matrix over the full author x derived product ---------------

def _oracle(author, derived):
    """The separately-written EXACT oracle, A1 form (accepted round 24):
    UNIFORM — every non-revoked incoherent cell is USE_ONLY, whatever
    the author or derivation; the revoked floor (tested separately)
    caps at QUARANTINED."""
    return Disclosure.USE_ONLY


def test_author_floor_spans_the_author_domain():
    members = list(EvidenceAuthor)
    for author in members:
        for derived in [None, *members]:
            s = SqliteStore(":memory:")
            _ingest(s, [_tpc("user")], author=author, derived=derived)
            edges = s.edges(U, active_only=False)
            assert len(edges) == 1, (author, derived)
            assert edges[0].provenance.disclosure == _oracle(author,
                                                             derived), (
                author, derived, edges[0].provenance.disclosure)


# ---- U3 + U5: the re-dispositioned record ----------------------------------

def test_redispositioned_triple_is_not_quarantined_by_relation():
    s = SqliteStore(":memory:")
    _ingest(s, [_tpc("user")])
    e = s.edges(U, active_only=False)[0]
    assert e.relation == UNCLASSIFIED_RELATION
    assert not e.quarantined, (
        "the fix that only reordered _disclosure_for would fail here (U3)")


def test_redisposition_carries_the_original_relation():
    s = SqliteStore(":memory:")
    _ingest(s, [_tpc("User  ")])          # canonicalises to "user"
    e = s.edges(U, active_only=False)[0]
    assert e.original_relation == QUARANTINE_RELATION, "U5"
    assert e.subject == "User"            # the SAME canonical conversion


# ---- U4: unreachable when never triggered ----------------------------------

def test_no_quarantine_relation_is_byte_identical():
    s = SqliteStore(":memory:")
    r = _ingest(s, [{"subject": "user", "relation": "works_as",
                     "object": "carpenter"}])
    assert r["redispositioned"] == 0
    e = s.edges(U, active_only=False)[0]
    assert e.original_relation is None
    assert e.relation == "works_as"


# ---- U6: ONE write site — the 0023 N2 sweep, extended ----------------------

def test_single_disclosure_write_site():
    """U6 — the module inventory is 0023 N2's sweep
    (test_disclosure_writers_are_exactly_the_two_known_sites); this extends
    it INSIDE ingest.py rather than duplicating it: edge disclosure is
    ESTABLISHED by exactly one `disclosure = _disclosure_for(...)`
    assignment — the re-disposition selects that call's ARGUMENT, never a
    second write site."""
    tree = ast.parse(
        pathlib.Path("src/veracium/ingest.py").read_text())
    establishments = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "disclosure"
                for t in n.targets)
        and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                and c.func.id == "_disclosure_for"
                for c in ast.walk(n.value))]
    assert len(establishments) == 1, (
        f"{len(establishments)} establishment sites — U6 permits exactly one")


# ---- U7: the count, on every path ------------------------------------------

def test_redisposition_count_is_reported():
    # the movement path
    s = SqliteStore(":memory:")
    r = _ingest(s, [_tpc("user"), _tpc("landlord")])
    assert r["redispositioned"] == 1
    # the no-hit path: key present, zero
    s2 = SqliteStore(":memory:")
    r2 = _ingest(s2, [{"subject": "user", "relation": "works_as",
                       "object": "x"}])
    assert r2["redispositioned"] == 0
    # the unparseable path: key present, zero
    s3 = SqliteStore(":memory:")

    def bad_llm(prompt, **kw):
        return "not json at all"
    r3 = ingest_event(s3, bad_llm, U, event_text="t",
                      author=EvidenceAuthor.USER, date="2026-08-23",
                      relations=DEFAULT_RELATIONS)
    assert r3["redispositioned"] == 0 and r3["unparseable"]


# ---- 0025 §4b-iii step 3: the floors still win (0024 round-3 R3-1) ---------

def test_standing_revocation_floors_the_redispositioned_triple(tmp_path):
    """The pipeline cell round 3 caught in the SPEC: a standing-revoked
    source's incoherent triple must NOT come out MENTIONABLE — the
    coherence rewrite establishes the base (step 2), the accepted N1
    floor lowers it to QUARANTINED (step 3). The re-disposition itself
    still happens and is still counted; only disclosure is floored."""
    from veracium.scope_linkage import identity_digest_of
    from veracium.store import revocation as rv
    s = SqliteStore(str(tmp_path / "r.db"))
    digest = identity_digest_of(None, "src-1", s.local_origin())
    rv.revoke_source(s, U, digest, "revoke", "operator",
                     "2026-08-23T00:00:00Z")
    r = ingest_event(s, _llm_for([_tpc("user")]), U, event_text="t",
                     author=EvidenceAuthor.USER, date="2026-08-23",
                     source_id="src-1", relations=DEFAULT_RELATIONS)
    e = s.edges(U, active_only=False)[0]
    assert e.provenance.disclosure == Disclosure.QUARANTINED, (
        "the standing-revocation floor must win over the coherence rewrite")
    assert e.relation == UNCLASSIFIED_RELATION
    assert e.original_relation == QUARANTINE_RELATION
    assert r["redispositioned"] == 1 and r["quarantined_at_birth"] == 1


# ---- the baseline shapes ----------------------------------------------------

def test_a08_the_movement_cell():
    """The baseline's ONE live conflation shape (A08): a USER-authored
    event whose triple the extractor mislabels third_party_claim with
    subject user — under A1 it is USE_ONLY (may inform, never assert),
    unquarantined, counted. The v7 form asserted MENTIONABLE; the
    measured 4:1 relay population is why A1 withholds assertion."""
    s = SqliteStore(":memory:")
    r = _ingest(s, [_tpc("user", "prefers the window seat")])
    e = s.edges(U, active_only=False)[0]
    assert e.provenance.disclosure == Disclosure.USE_ONLY
    assert not e.quarantined
    assert e.original_relation == QUARANTINE_RELATION
    assert r["redispositioned"] == 1


def test_b07_relay_preservation_and_the_stated_gap():
    """The relay-preservation cell, BOTH halves. (1) A genuine relay the
    extractor labels correctly stays QUARANTINED (U1). (2) THE STATED
    GAP, from the baseline's B02/B07: a genuine relay the extractor
    files under a CONCRETE relation never reaches the quarantine branch
    — it lands at the author floor (USE_ONLY for third-party-derived,
    but MENTIONABLE for a user-authored relay event). 0024's
    decision-order fix is ORTHOGONAL to this path and does not close it;
    the note-vs-label agreement check (#107) owns it. This test PINS the
    pre-existing behaviour so the fix is never blamed for it."""
    # (1) correctly-labelled relay: quarantined, not moved
    s = SqliteStore(":memory:")
    r = _ingest(s, [_tpc("the vet", "Rex is allergic to chicken")])
    assert s.edges(U, active_only=False)[0].provenance.disclosure \
        == Disclosure.QUARANTINED
    assert r["redispositioned"] == 0
    # (2) the B07 shape: concrete relation chosen by the extractor —
    # bypasses quarantine TODAY, before and after this fix (documented)
    s2 = SqliteStore(":memory:")
    _ingest(s2, [{"subject": "Rex", "relation": "has_diet",
                  "object": "allergic to chicken (the vet said)"}])
    e = s2.edges(U, active_only=False)[0]
    assert e.provenance.disclosure == Disclosure.MENTIONABLE
    assert e.original_relation is None    # no re-disposition touched it
