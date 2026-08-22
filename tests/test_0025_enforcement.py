"""specs/0025 (accepted v13) — X1–X12 for the core enforcement.

X13's five per-surface receipt tests land with the cross-era receipt slice.
The registry construction is differentially checked against
specs/evidence/0025/reference_enforcement.py (the vector-harness
discipline); the enforcement loop is driven through the REAL ingest_event
with a stub provider.
"""
import json

import pytest

from veracium.ingest import ingest_event
from veracium.registry import (RegistryError, effective_registry,
                               render_prompt_relations)
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, EvidenceAuthor,
                             QUARANTINE_RELATION, Relation,
                             RESERVED_RELATIONS, UNCLASSIFIED_RELATION)
from veracium.store.sqlite import SqliteStore

U = "u-0025"
DATE = "2026-08-22"


class StubLLM:
    """Captures every call; returns the main extraction, then the retry."""

    def __init__(self, main: dict, retry: dict | None = None,
                 retry_raises: Exception | None = None):
        self.main, self.retry = main, retry
        self.retry_raises = retry_raises
        self.calls = []

    def __call__(self, prompt, **kw):
        self.calls.append((prompt, kw))
        if kw.get("role") == "distill-retry":
            if self.retry_raises is not None:
                raise self.retry_raises
            return json.dumps(self.retry if self.retry is not None
                              else {"triples": []})
        return json.dumps(self.main)


def _main(triples):
    return {"triples": triples, "episode": "the day's summary"}


def _ingest(llm, **kw):
    s = SqliteStore(":memory:")
    r = ingest_event(s, llm, U, event_text="event text",
                     author=kw.pop("author", EvidenceAuthor.USER),
                     date=DATE, **kw)
    return s, r


def _edges(s):
    return s.edges(U, active_only=False, include_quarantined=True)


# ---- the registry construction (X5, X8, X9, X11) ---------------------------

def test_empty_registry_is_refused():
    with pytest.raises(RegistryError):
        effective_registry({})


def test_mismatched_key_is_refused():
    with pytest.raises(RegistryError):
        effective_registry({"jobs": Relation(name="works_as",
                                             functional=True)})


def test_reserved_members_are_always_resident():
    host = {"works_on": Relation(name="works_on")}
    reg = effective_registry(host)
    assert UNCLASSIFIED_RELATION in reg and QUARANTINE_RELATION in reg
    assert not reg[UNCLASSIFIED_RELATION].functional
    assert not reg[QUARANTINE_RELATION].functional


def test_conflicting_reserved_shadow_is_refused():
    base = {"works_on": Relation(name="works_on")}
    canon = RESERVED_RELATIONS[QUARANTINE_RELATION]
    # a functional shadow, a drifted gloss, and an OMITTED gloss all refuse
    for bad in (Relation(name=QUARANTINE_RELATION, functional=True,
                         desc=canon.desc),
                Relation(name=QUARANTINE_RELATION, desc="assert freely"),
                Relation(name=QUARANTINE_RELATION)):
        with pytest.raises(RegistryError):
            effective_registry(dict(base, **{QUARANTINE_RELATION: bad}))
    # the exactly-canonical form is accepted — and the SHIPPED registry
    # passes verbatim (round 4, R4-1: the actual objects, no stand-in)
    reg = effective_registry(dict(base, **{QUARANTINE_RELATION: canon}))
    assert reg[QUARANTINE_RELATION].desc == canon.desc
    assert QUARANTINE_RELATION in effective_registry(DEFAULT_RELATIONS)


def test_registry_snapshot_is_immutable():
    host = {"works_as": Relation(name="works_as", functional=True)}
    reg = effective_registry(host)
    host.clear()                                  # caller-side mutation
    assert reg["works_as"].functional is True
    with pytest.raises(TypeError):
        reg["injected"] = None                    # through the mapping
    with pytest.raises(AttributeError):
        reg["works_as"].functional = False        # through the record


def test_construction_agrees_with_the_reference():
    """Differential: the product construction and the reference harness
    agree cell-for-cell on the acceptance and refusal cells."""
    import importlib.util
    import pathlib
    spec = importlib.util.spec_from_file_location(
        "ref_enf", pathlib.Path(__file__).parent.parent /
        "specs/evidence/0025/reference_enforcement.py")
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    # accept: the shipped registry
    ours = effective_registry(DEFAULT_RELATIONS)
    theirs = ref.effective_registry(DEFAULT_RELATIONS)
    assert set(ours) == set(theirs)
    assert all(ours[k].functional == theirs[k].functional for k in ours)
    # refuse: empty and conflicting-shadow, both sides
    for bad_host in ({}, dict(DEFAULT_RELATIONS,
                              **{UNCLASSIFIED_RELATION: Relation(
                                  name=UNCLASSIFIED_RELATION,
                                  functional=True)})):
        with pytest.raises(Exception):
            effective_registry(bad_host)
        with pytest.raises(Exception):
            ref.effective_registry(bad_host)


# ---- the prompt (§4b-iv; X6's second carrier) ------------------------------

def test_prompt_renders_selectable_set_in_insertion_order():
    reg = effective_registry(DEFAULT_RELATIONS)
    rendered = render_prompt_relations(reg)
    # byte-identical to the pre-0025 inline rendering of the default registry
    legacy = "\n".join(f"- {n}: {r.desc}" if r.desc else f"- {n}"
                       for n, r in DEFAULT_RELATIONS.items())
    assert rendered == legacy
    assert UNCLASSIFIED_RELATION not in rendered
    assert QUARANTINE_RELATION in rendered        # hearsay stays selectable
    # a custom-ORDERED registry renders in ITS order (round 4, R4-2)
    host = {"zeta_rel": Relation(name="zeta_rel", desc="z"),
            "alpha_rel": Relation(name="alpha_rel", desc="a")}
    lines = render_prompt_relations(effective_registry(host)).splitlines()
    assert lines[0].startswith("- zeta_rel") and lines[1].startswith("- alpha_rel")


# ---- enforcement through the live write path (X1, X2, X3, X10) -------------

def test_every_stored_relation_is_in_the_registry():
    """X1, over adversarial extractor output: garbage strings, a direct
    `unclassified` emission (§4b-iv — not selectable), and a registry
    member all land registry-resident."""
    llm = StubLLM(_main([
        {"subject": "user", "relation": "invented_rel", "object": "a"},
        {"subject": "user", "relation": UNCLASSIFIED_RELATION, "object": "b"},
        {"subject": "user", "relation": "works_on", "object": "c"},
    ]))
    s, r = _ingest(llm)
    reg = effective_registry(DEFAULT_RELATIONS)
    stored = _edges(s)
    assert len(stored) == 3
    assert all(e.relation in reg for e in stored)
    assert r["invalid"] == 2 and r["residual"] == 2


def test_reserved_relation_never_supersedes():
    """X2: two different values under off-vocabulary relations accumulate —
    the reserved member is non-functional, nothing is retired."""
    s = SqliteStore(":memory:")
    for i, obj in enumerate(("carpenter", "plumber")):
        ingest_event(s, StubLLM(_main([{"subject": "user",
                                        "relation": "occupation",
                                        "object": obj}])),
                     U, event_text="e", author=EvidenceAuthor.USER, date=DATE)
    active = s.edges(U, active_only=True, include_quarantined=True)
    assert sorted(e.object for e in active) == ["carpenter", "plumber"]


def test_offvocab_original_relation_survives_typed():
    """X3: the typed carrier, never note prose; None on ordinary edges."""
    llm = StubLLM(_main([
        {"subject": "user", "relation": "occupation", "object": "carpenter",
         "note": "extractor note"},
        {"subject": "user", "relation": "works_on", "object": "chess"},
    ]))
    s, _ = _ingest(llm)
    by_obj = {e.object: e for e in _edges(s)}
    redisp = by_obj["carpenter"]
    assert redisp.relation == UNCLASSIFIED_RELATION
    assert redisp.original_relation == "occupation"
    assert "occupation" not in redisp.note        # NOT the note carrier
    assert by_obj["chess"].original_relation is None


def test_vocabulary_fallback_never_changes_disclosure():
    """X10: disclosure is established from the ORIGINAL relation before the
    fallback and retained through it — the laundering cell stays closed
    because `third_party_claim` is registry-resident."""
    llm = StubLLM(_main([
        {"subject": "the landlord", "relation": QUARANTINE_RELATION,
         "object": "user owes $500"},                      # genuine hearsay
        {"subject": "user", "relation": "ThirdPartyClaim", "object": "x"},
    ]))
    s, r = _ingest(llm)
    by_obj = {e.object: e for e in _edges(s)}
    hearsay = by_obj["user owes $500"]
    assert hearsay.relation == QUARANTINE_RELATION         # never re-filed
    assert hearsay.provenance.disclosure is Disclosure.QUARANTINED
    near_miss = by_obj["x"]                                # off-vocabulary
    assert near_miss.relation == UNCLASSIFIED_RELATION
    # established from the ORIGINAL relation (exact-match quarantine test
    # fails on "ThirdPartyClaim") via the author rules, and the fallback
    # did not touch it
    assert near_miss.provenance.disclosure is Disclosure.MENTIONABLE
    assert r["invalid"] == 1


# ---- the retry (§4b(1)) ----------------------------------------------------

def test_retry_is_one_call_and_repairs_by_content_pair():
    llm = StubLLM(
        _main([{"subject": "user", "relation": "job", "object": "carpenter"},
               {"subject": "user", "relation": "hobby", "object": "chess"}]),
        retry={"triples": [
            {"subject": "User", "relation": "works_as",
             "object": "carpenter "},              # repairs by content pair
            {"subject": "user", "relation": "invented", "object": "new"}]})
    s, r = _ingest(llm)
    retry_calls = [c for c in llm.calls
                   if c[1].get("role") == "distill-retry"]
    assert len(retry_calls) == 1                   # exactly ONE per event
    by_obj = {e.object: e for e in _edges(s)}
    assert by_obj["carpenter"].relation == "works_as"
    assert by_obj["carpenter"].original_relation == "job"
    assert by_obj["chess"].relation == UNCLASSIFIED_RELATION
    assert "new" not in by_obj                     # discards, never adds
    assert (r["invalid"], r["retried"], r["recovered"], r["residual"]) == \
        (2, 2, 1, 1)


def test_duplicate_pairs_consume_one_to_one():
    llm = StubLLM(
        _main([{"subject": "user", "relation": "job", "object": "carpenter"},
               {"subject": "User", "relation": "occupation",
                "object": "Carpenter"}]),
        retry={"triples": [{"subject": "user", "relation": "works_as",
                            "object": "carpenter"}]})
    s, r = _ingest(llm)
    rels = sorted(e.relation for e in _edges(s))
    assert rels == sorted(["works_as", UNCLASSIFIED_RELATION])
    assert r["recovered"] == 1 and r["residual"] == 1


def test_reserved_retry_answer_is_residual_not_recovered():
    llm = StubLLM(
        _main([{"subject": "user", "relation": "job", "object": "carpenter"}]),
        retry={"triples": [{"subject": "user",
                            "relation": UNCLASSIFIED_RELATION,
                            "object": "carpenter"}]})
    s, r = _ingest(llm)
    assert r["recovered"] == 0 and r["residual"] == 1
    e = _edges(s)[0]
    assert e.relation == UNCLASSIFIED_RELATION
    assert e.original_relation == "job"


def test_provider_failures_degrade_recorded_never_raised():
    for bad in (dict(retry_raises=ValueError("provider down")),
                dict(retry={"not_triples": []})):
        llm = StubLLM(_main([{"subject": "user", "relation": "job",
                              "object": "carpenter"}]), **bad)
        s, r = _ingest(llm)
        assert (r["retried"], r["recovered"], r["residual"]) == (1, 0, 1)
        assert _edges(s)[0].relation == UNCLASSIFIED_RELATION


# ---- the counters (X4, X12) ------------------------------------------------

PUBLIC_COUNTERS = ("invalid", "retried", "recovered", "residual",
                   "redispositioned")


def test_offvocab_counts_are_reported_separately():
    """X4: every §4c public key on every path, zeros present, and
    invalid = recovered + residual reconciles."""
    llm = StubLLM(_main([{"subject": "user", "relation": "works_on",
                          "object": "chess"}]))
    _, clean = _ingest(llm)
    for k in PUBLIC_COUNTERS:
        assert clean[k] == 0                       # zeros PRESENT
    llm = StubLLM(_main([{"subject": "user", "relation": "job",
                          "object": "carpenter"}]))
    _, dirty = _ingest(llm)
    assert dirty["invalid"] == dirty["recovered"] + dirty["residual"]
    # the unparseable path carries the keys too — an absent key is not a zero
    class Garbage:
        def __call__(self, prompt, **kw):
            return "not json at all {{{"
    _, bad = _ingest(Garbage())
    assert bad.get("unparseable") is True
    for k in PUBLIC_COUNTERS:
        assert bad[k] == 0


def test_public_counter_projection_is_exact():
    """X12: the result's counter additions are PRECISELY the §4c public
    keys — `retry_calls` (and any other internal) is absent."""
    llm = StubLLM(_main([{"subject": "user", "relation": "works_on",
                          "object": "chess"}]))
    _, r = _ingest(llm)
    pre_0025 = {"episode", "facts", "quarantined", "supersessions",
                "reinforcements"}
    assert set(r) == pre_0025 | set(PUBLIC_COUNTERS)
    assert "retry_calls" not in r


# ---- X6: the two preserved byte carriers ------------------------------------

def test_unaffected_edge_bytes_exact():
    """An edge the enforcement never touched serializes byte-identically to
    its pre-0025 shape — the None-omission rule at work."""
    llm = StubLLM(_main([{"subject": "user", "relation": "works_on",
                          "object": "chess"}]))
    s, _ = _ingest(llm)
    e = _edges(s)[0]
    dumped = e.model_dump_json()
    assert "original_relation" not in dumped
    # and an AFFECTED edge carries the field
    llm = StubLLM(_main([{"subject": "user", "relation": "job",
                          "object": "carpenter"}]))
    s2, _ = _ingest(llm)
    assert '"original_relation":"job"' in _edges(s2)[0].model_dump_json()


# ---- X7: the polarity, structurally -----------------------------------------

def test_no_unvalidated_relation_path():
    """The write site is reached only through the enforcement: ONE Edge
    construction in the triple loop, its relation drawn from the enforced
    row, with the effective registry built before it — the structural form
    0004 W7 and 0023 N2 use."""
    import ast
    import pathlib
    src = (pathlib.Path(__file__).parent.parent /
           "src/veracium/ingest.py").read_text()
    assert src.index("reg = effective_registry(") < src.index("edge = Edge(")
    tree = ast.parse(src)
    edge_calls = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Call)
                  and getattr(n.func, "id", "") == "Edge"]
    # exactly ONE Edge construction site in the whole write path
    assert len(edge_calls) == 1
    kw = {k.arg: k.value for k in edge_calls[0].keywords}
    # its relation kwarg is the bare enforced local, nothing rawer
    assert isinstance(kw["relation"], ast.Name) and \
        kw["relation"].id == "relation"
    # and that local is assigned ONLY from the enforced row
    assigns = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
               for t in n.targets
               if isinstance(t, ast.Name) and t.id == "relation"]
    assert len(assigns) == 1
    v = assigns[0].value
    assert isinstance(v, ast.Subscript) and v.slice.value == "relation"
