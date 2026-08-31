#!/usr/bin/env python3
"""0027 V10 — the frozen legacy-projection oracle, captured PRE-FEATURE.

Generated at the PRE-IMPLEMENTATION tree (commit bd5fdc0, 2026-08-31), before
any refactor of `graph.subgraph_for_query`. V10 claims that with
`principal=None` and `semantic_status != ok`, recall's ordered edge-id list is
byte-identical to today's `subgraph_for_query` — this file IS "today's",
captured while the shipped scan was still the only construction (the 0026
v7-oracle pattern: the oracle must predate the mechanism it judges).

The store is DETERMINISTIC: fixed edge ids, fixed timestamps, no uuid, no
clock. It exercises every selection feature the projection depends on:
user-subject eligibility at zero overlap, entity overlap scoring, the active
bonus, recency tiebreaks, I8 collapse duplicates, the I6 assertable reserve
under truncation (60 edges > max_edges=40), `_cover` time coverage, and a
functional-contention permutation group.

Rerunning REGENERATES the capture from the live tree — run it only at the
pre-feature commit; afterwards the committed JSON is the frozen truth and the
V10 test compares the LIVE pipeline against it.
"""
import json
import pathlib
import sys
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from veracium.schema import Edge, Provenance, EvidenceAuthor, Disclosure  # noqa: E402
from veracium.store.sqlite import SqliteStore                             # noqa: E402
from veracium.graph import subgraph_for_query                             # noqa: E402

U = "v10-oracle-user"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _edge(i, subject, relation, obj, note="", active=True, days=0,
          disclosure=Disclosure.MENTIONABLE):
    t = T0 + timedelta(days=days)
    e = Edge(id=f"v10-{i:03d}", user_id=U, subject=subject, relation=relation,
             object=obj, note=note,
             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                   evidence_ref=f"ev-{i:03d}", observed_at=t,
                                   disclosure=disclosure),
             valid_from=t)
    if not active:
        e = e.model_copy(update={"invalidated_at": t + timedelta(days=1),
                                 "invalidation_reason": "superseded"})
    return e


def build_store(path):
    store = SqliteStore(str(path))
    edges = []
    # 20 user-subject facts (eligible at zero overlap), staggered days
    topics = ["gardening tulips", "chess openings", "marathon training",
              "sourdough baking", "jazz piano", "kayak rivers",
              "star gazing", "wood carving", "rock climbing", "tea ceremony",
              "salsa dancing", "bird watching", "fly fishing", "calligraphy",
              "beekeeping hives", "pottery wheel", "archery range",
              "quilt patterns", "bonsai pruning", "cider pressing"]
    for i, topic in enumerate(topics):
        edges.append(_edge(i, "user", "enjoys", topic, days=i))
    # 20 entity edges, half overlapping the queries below
    for i in range(20, 30):
        edges.append(_edge(i, f"city:{i}", "hosts", f"marathon event {i}",
                           note="race calendar", days=i))
    for i in range(30, 40):
        edges.append(_edge(i, f"org:{i}", "sells", f"widget {i}", days=i))
    # 10 inactive history rows (superseded)
    for i in range(40, 50):
        edges.append(_edge(i, "user", "worked_at", f"employer {i}",
                           active=False, days=i - 40))
    # collapse duplicates: same (subject, relation) same value-key, one noted
    edges.append(_edge(50, "user", "drinks", "oat latte", note="", days=3))
    edges.append(_edge(51, "user", "drinks", "oat latte",
                       note="double shot", days=4))
    # functional contention: same (subject, relation), two DISTINCT values
    edges.append(_edge(52, "user", "timezone", "pacific", days=5))
    edges.append(_edge(53, "user", "timezone", "eastern", days=6))
    # a few more marathon-adjacent entity rows for coverage spread
    for i in range(54, 60):
        edges.append(_edge(i, f"club:{i}", "organises",
                           "marathon training runs", days=(i - 54) * 30))
    for e in edges:
        store.add_edge(e)
    return store


QUERIES = [
    "marathon training schedule",
    "what do i enjoy",
    "oat latte",
    "timezone",
    "widget 33",
    "",
]


def capture(store):
    out = {}
    for q in QUERIES:
        ids = [e.id for e in subgraph_for_query(store, U, q, max_edges=40,
                                                coverage_share=0.25)]
        out[q] = ids
    return out


def main():
    here = pathlib.Path(__file__).resolve().parent
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        store = build_store(pathlib.Path(td) / "oracle.db")
        got = capture(store)
    blob = json.dumps(got, indent=1, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        cur = (here / "legacy_projections.json").read_text()
        print("MATCH" if cur == blob else "DRIFT")
        return 0 if cur == blob else 1
    (here / "legacy_projections.json").write_text(blob)
    print(f"wrote legacy_projections.json ({sum(len(v) for v in got.values())} "
          f"ids across {len(got)} queries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
