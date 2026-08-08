"""specs/0003 — the write guard (§4a): `graph.apply_supersession`.

The reported defect: the functional-supersession loop retired ANY differing value
regardless of who reported it (`graph.py:139`), so third-party content could retire a
user's fact. These pin the guard end-to-end through the write path — retire only when the
incoming edge's recorded effective authority is >= the prior's, else refuse and keep both
(I1–I4). The store primitive the guard drives is tested in test_0003_supersession_store.py.
"""
import itertools

from veracium.authority import effective, permitted
from veracium.graph import apply_supersession
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, EvidenceAuthor,
                             Provenance, SourceType)
from veracium.store.sqlite import SqliteStore

U = "u1"
AUTHORS = list(EvidenceAuthor)
DF_OPTS = [None, *EvidenceAuthor]


def _edge(store, eid, author, obj, df=None, rel="works_as", disc=Disclosure.MENTIONABLE):
    return Edge(id=eid, user_id=U, subject="user", relation=rel, object=obj,
                provenance=Provenance(source_type=SourceType.STATED, author_of_evidence=author,
                                      evidence_ref="ev", disclosure=disc, derived_from=df))


def _prior_and_incoming(tmp_path, name, prior_author, prior_df, inc_author, inc_df,
                        prior_obj="CFO at Acme", inc_obj="unemployed", rel="works_as"):
    """Ingest a prior, then apply a DIFFERING-value incoming edge through the guard."""
    s = SqliteStore(str(tmp_path / f"{name}.db"))
    prior = _edge(s, "p", prior_author, prior_obj, df=prior_df, rel=rel)
    s.add_edge(prior)
    inc = _edge(s, "i", inc_author, inc_obj, df=inc_df, rel=rel)
    apply_supersession(s, inc, DEFAULT_RELATIONS)
    return s


# --- I1: the authority matrix, over the full (author, derived_from) product -----

def test_supersession_authority_matrix(tmp_path):
    """The guard retires the prior iff the incoming EFFECTIVE authority >= the prior's,
    over the ENTIRE (author, derived_from) product — the same rule `specs/ladder.py`
    generates its tables from. A retire leaves one active edge and no refusal; a refusal
    leaves both active and one recorded refusal."""
    for n, (pa, pf, ia, if_) in enumerate(
            itertools.product(AUTHORS, DF_OPTS, AUTHORS, DF_OPTS)):
        s = _prior_and_incoming(tmp_path, f"m{n}", pa, pf, ia, if_)
        active = {e.id for e in s.edges(U, active_only=True)}
        allowed = permitted(pa, pf, ia, if_)
        if allowed:
            assert active == {"i"}, (pa, pf, ia, if_, "should retire prior")
            assert s.supersessions_refused(U) == 0, (pa, pf, ia, if_)
        else:
            assert active == {"p", "i"}, (pa, pf, ia, if_, "should keep both")
            assert s.supersessions_refused(U) == 1, (pa, pf, ia, if_)
            (r,) = s.refusals(U)
            assert r.prior_effective == effective(pa, pf)
            assert r.incoming_effective == effective(ia, if_)


# --- I2: a functional relation does not exempt the rule ------------------------

def test_functional_relation_does_not_bypass_authority(tmp_path):
    # works_as is functional; a lower-authority incoming value still cannot retire.
    assert DEFAULT_RELATIONS["works_as"].functional
    s = _prior_and_incoming(tmp_path, "f", EvidenceAuthor.USER, None,
                            EvidenceAuthor.THIRD_PARTY, None)
    assert {e.id for e in s.edges(U, active_only=True)} == {"p", "i"}
    assert s.supersessions_refused(U) == 1


# --- I3: a refused retirement leaves both edges active (the measured case) ------

def test_refused_supersession_keeps_both(tmp_path):
    """The motivating measurement: an email extracted as works_as=unemployed
    (THIRD_PARTY, eff 0) must NOT retire the user's own works_as=CFO (USER, eff 3)."""
    s = _prior_and_incoming(tmp_path, "keep", EvidenceAuthor.USER, None,
                            EvidenceAuthor.THIRD_PARTY, None,
                            prior_obj="CFO at Acme", inc_obj="unemployed")
    active = {e.object for e in s.edges(U, active_only=True)}
    assert active == {"CFO at Acme", "unemployed"}
    prior = next(e for e in s.edges(U, active_only=True) if e.id == "p")
    assert prior.active and prior.invalidated_at is None       # the user's fact survives


def test_a_system_summary_of_an_attacker_email_retires_nothing(tmp_path):
    """The capping door (§3): a SYSTEM edge derived_from THIRD_PARTY has effective 0, so it
    cannot retire a USER fact even though raw SYSTEM (2) would outrank nothing here."""
    s = _prior_and_incoming(tmp_path, "cap", EvidenceAuthor.USER, None,
                            EvidenceAuthor.SYSTEM, EvidenceAuthor.THIRD_PARTY)
    assert {e.id for e in s.edges(U, active_only=True)} == {"p", "i"}
    assert s.supersessions_refused(U) == 1


# --- I4: the permitted directions STILL work (permissions, not only prohibitions) --

def test_user_authored_ingest_can_supersede_third_party(tmp_path):
    s = _prior_and_incoming(tmp_path, "u_over_tp", EvidenceAuthor.THIRD_PARTY, None,
                            EvidenceAuthor.USER, None)
    active = {e.id for e in s.edges(U, active_only=True)}
    assert active == {"i"}                                     # the third-party prior retired
    assert s.supersessions_refused(U) == 0
    retired = next(e for e in s.edges(U, active_only=False) if e.id == "p")
    assert not retired.active and retired.invalidation_reason == "superseded"


def test_same_author_update_still_supersedes(tmp_path):
    s = _prior_and_incoming(tmp_path, "same", EvidenceAuthor.USER, None,
                            EvidenceAuthor.USER, None, prior_obj="CFO", inc_obj="CEO")
    assert {e.object for e in s.edges(U, active_only=True)} == {"CEO"}
    assert s.supersessions_refused(U) == 0


def test_non_functional_relation_accumulates_no_refusal(tmp_path):
    """A non-functional relation is untouched — differing values accumulate, no
    supersession and no refusal (the guard only governs functional supersession)."""
    assert not DEFAULT_RELATIONS["has_pet"].functional
    s = _prior_and_incoming(tmp_path, "acc", EvidenceAuthor.USER, None,
                            EvidenceAuthor.THIRD_PARTY, None,
                            prior_obj="cat Miso", inc_obj="dog Rex", rel="has_pet")
    assert {e.id for e in s.edges(U, active_only=True)} == {"p", "i"}
    assert s.supersessions_refused(U) == 0                     # accumulation, not refusal
