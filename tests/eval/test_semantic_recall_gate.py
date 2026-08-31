"""0027 §6a — the acceptance gate, manifest-driven and modelless.

Pre-committed BEFORE the run (the criteria are the spec's, frozen at
adoption); DETERMINISTIC — the shipped `vectors.json` (pinned
all-MiniLM-L6-v2) replaces the live embedder, so the measurement
reproduces byte-for-byte on every machine. The fixture protocol is the
manifest's frozen `fixture` block: per case an ISOLATED store holding the
target plus its 19 listed `distractor_ids`, frozen edge ids, fixed
instants, empty wiki, no higher-priority classes, `principal=None`,
`max_subgraph_edges=40`, `token_budget=4000`.

Criteria (§6a, accept split only):
  1. recovery: paraphrase recall@10 >= 0.80;
  2. exact-match non-regression: OFF = 1.0, ON >= 0.95 (displacements
     recorded);
  3. classification-entry: each trust-labelled edge retrieved via the
     semantic lane classifies identically to its lexical retrieval.

The tune split's role — choosing `semantic_min_cosine` — happened ONCE at
implementation (2026-08-31); the frozen value is the config default, and
this gate re-verifies the deterministic numbers rather than re-tuning.
"""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

import pytest

from veracium import Memory
from veracium import semantic as sm_mod
from veracium.config import MemoryConfig
from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance

HERE = pathlib.Path(__file__).resolve().parent / "semantic_paraphrase"
MANIFEST = json.loads((HERE / "manifest.json").read_text())
VECTORS = json.loads((HERE / "vectors.json").read_text())
CASES = {c["id"]: c for c in MANIFEST["cases"]}
BY_EDGE = {c["edge_id"]: c for c in MANIFEST["cases"]}
T = datetime(2026, 1, 1, tzinfo=timezone.utc)   # the fixture instant
U = "eval-u"

_DISC = {"MENTIONABLE": Disclosure.MENTIONABLE,
         "USE_ONLY": Disclosure.USE_ONLY,
         "QUARANTINED": Disclosure.QUARANTINED}


def _embedded_text(c) -> str:
    return f"{c['subject']} {c['relation']} {c['object']} {c['note']}"


def test_vector_artifact_matches_the_projection_and_population():
    """The build-time inlined projection cannot drift from the shipped
    veracium.semantic.embedded_text, and the vector population is exactly
    the manifest's (spot-weld — the vectors were computed WITHOUT veracium
    importable)."""
    c = MANIFEST["cases"][0]
    e = _case_edge(c)
    assert sm_mod.embedded_text(e) == _embedded_text(c)
    assert set(VECTORS["targets"]) == {x["edge_id"] for x in MANIFEST["cases"]}
    assert set(VECTORS["queries"]) == {x["id"] for x in MANIFEST["cases"]}
    assert VECTORS["dim"] == len(next(iter(VECTORS["targets"].values())))


class PrecomputedEmbed:
    """§6a determinism: serves the shipped vectors by EXACT text; an
    unknown text is fixture drift and raises rather than approximating."""

    def __init__(self):
        self._by_text = {}
        for c in MANIFEST["cases"]:
            self._by_text[_embedded_text(c)] = VECTORS["targets"][c["edge_id"]]
            self._by_text[c["query"]] = VECTORS["queries"][c["id"]]

    def id(self):
        return VECTORS["embedder_id"]

    def dim(self):
        return VECTORS["dim"]

    def __call__(self, texts):
        return [self._by_text[t] for t in texts]


def _case_edge(c) -> Edge:
    return Edge(id=c["edge_id"], user_id=U, subject=c["subject"],
                relation=c["relation"], object=c["object"], note=c["note"],
                provenance=Provenance(
                    author_of_evidence=EvidenceAuthor.USER,
                    evidence_ref=f"ev-{c['id']}", observed_at=T,
                    disclosure=_DISC[c.get("disclosure", "MENTIONABLE")]),
                valid_from=T)


def _run_case(tmp_path, c, *, semantic="auto"):
    """One isolated fixture store per the frozen protocol; returns the
    Recall."""
    m = Memory(llm=lambda p, **k: "", embed=PrecomputedEmbed(),
               config=MemoryConfig(db_path=str(tmp_path / f"{c['id']}.db"),
                                   wiki_recompile_after_writes=0,
                                   max_subgraph_edges=40))
    m.store.add_edge(_case_edge(c))                 # target first
    for did in c["distractor_ids"]:                 # then the listed 19
        m.store.add_edge(_case_edge(BY_EDGE[did]))
    m.embed_backfill(U)
    r = m.recall(U, c["query"], token_budget=4000, semantic=semantic)
    m.close()
    return r


def _hit_at_10(r, c) -> bool:
    key = c["expected_key"]
    top = [f"{e.subject}|{e.relation}|{e.object}" for e in r.edges[:10]]
    return key in top


def _split(label, split="accept"):
    return [c for c in MANIFEST["cases"]
            if c["split"] == split and c["label"] == label]


def test_recovery_paraphrase_recall_at_10(tmp_path):
    """§6a criterion 1: recall@10 over the 20 held-out entity paraphrase
    cases >= 0.80, with the lexical-only baseline recorded beside it."""
    cases = _split("paraphrase")
    assert len(cases) == 20
    on = sum(_hit_at_10(_run_case(tmp_path, c), c) for c in cases)
    off = sum(_hit_at_10(_run_case(tmp_path, c, semantic=False), c)
              for c in cases)
    print(f"\n§6a recovery: semantic ON {on}/20 (recall@10 {on/20:.2f}); "
          f"lexical baseline {off}/20 ({off/20:.2f})")
    assert on / 20 >= 0.80, (
        f"recovery recall@10 {on/20:.2f} < 0.80 — inspect case quality "
        f"before concluding the fusion is at fault (§9 point 3)")


def test_exact_match_non_regression(tmp_path):
    """§6a criterion 2: with semantic OFF the 20 exact cases are all found
    (byte-identical to today, which finds them); with semantic ON at least
    19/20 — any displacement is recorded by identity."""
    cases = _split("exact")
    assert len(cases) == 20
    off_miss = [c["id"] for c in cases
                if not _hit_at_10(_run_case(tmp_path, c, semantic=False), c)]
    assert off_miss == [], f"the OFF path lost exact matches: {off_miss}"
    on_miss = [c["id"] for c in cases
               if not _hit_at_10(_run_case(tmp_path, c), c)]
    print(f"\n§6a exact non-regression: ON misses {on_miss or 'none'}")
    assert (20 - len(on_miss)) / 20 >= 0.95, (
        f"semantic ON displaced exact matches beyond the bar: {on_miss}")


def test_classification_entry_for_trust_cases(tmp_path):
    """§6a criterion 3: each trust-labelled edge retrieved VIA THE SEMANTIC
    LANE enters render classification with the identical class its lexical
    retrieval gives it (classification-preservation, not partition
    identity)."""
    cases = _split("trust")
    assert len(cases) == 20
    mismatches = []
    for c in cases:
        r_sem = _run_case(tmp_path, c)
        # lexical retrieval of the same edge: query = its own text
        c_lex = dict(c, query=_embedded_text(c), id=c["id"] + "-lex")
        r_lex = _run_case(tmp_path, c_lex, semantic=False)
        sem = {e.id: e for e in r_sem.edges}.get(c["edge_id"])
        lex = {e.id: e for e in r_lex.edges}.get(c["edge_id"])
        assert lex is not None, f"{c['id']}: lexical self-query lost the edge"
        if sem is None:
            continue        # not surfaced semantically — nothing to compare
        if (sem.assertable, sem.quarantined) != (lex.assertable,
                                                 lex.quarantined):
            mismatches.append(c["id"])
    assert mismatches == [], (
        f"the semantic lane changed a trust classification: {mismatches}")
