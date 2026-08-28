#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0011_policy_matrix.py::test_contention_checker_cells_cannot_vanish
"""0011 §4c — contention, checked against the SHIPPED SURFACE.

External round 2, R2-3: the previous version of this file validated a
standalone value-list function — a REIMPLEMENTATION of the rule, not the
rule as any reader sees it. The reviewer inserted two active, same-class,
distinct-value edges into a real store and got draft-v5 CONTESTED against
the shipped `Recall.contested`'s **0 groups, 0 exposed members**. A checker
that agrees with its own restatement can do that indefinitely.

So this drives a REAL store and asserts the shipped predicate:
`_live_refusal_contention_edge_ids` — a refusal record exists, both edges
are active and distinct, the relation is functional. That is 0003's
refusal-scoped notion (`compile.py`: "REFUSAL-scoped (Option B), not every
contention"), and §4c now adopts it rather than defining a second one.

Runs under the reviewer's bare offline interpreter — it puts `src` on the
path itself rather than needing the package installed.

Run:  $PY specs/evidence/0011/check_contention_rule.py
"""
from __future__ import annotations

import pathlib
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))

from veracium.compile import _live_refusal_contention_edge_ids   # noqa: E402
from veracium.schema import (Disclosure, Edge, EvidenceAuthor,    # noqa: E402
                             Provenance, DEFAULT_RELATIONS,
                             SupersessionPlan, SupersessionRefusalDraft)
from veracium.store.sqlite import SqliteStore                     # noqa: E402
from veracium.authority import effective, scope_fingerprint       # noqa: E402

U, NOW = "u", datetime(2026, 5, 1, tzinfo=timezone.utc)


def _edge(eid, author, obj, disclosure=Disclosure.MENTIONABLE):
    return Edge(id=eid, user_id=U, subject="user", relation="works_as",
                object=obj, valid_from=NOW, active=True,
                provenance=Provenance(author_of_evidence=author,
                                      evidence_ref=f"r-{eid}", observed_at=NOW,
                                      disclosure=disclosure))


CELLS = ("cell_direct_pair_not_contested", "cell_live_refusal_contested")


def cell_direct_pair_not_contested(td) -> list:
    """The reviewer's R2-3 scenario: two active, same-class, DISTINCT-value
    edges inserted directly. No refusal exists, so the shipped surface
    reports nothing, and §4c must agree."""
    s = SqliteStore(f"{td}/direct.db")
    s.add_edge(_edge("d1", EvidenceAuthor.USER, "CFO at Acme"))
    s.add_edge(_edge("d2", EvidenceAuthor.USER, "CTO at Globex"))
    direct = _live_refusal_contention_edge_ids(s, U, DEFAULT_RELATIONS)
    s.close()
    if direct:
        return [f"direct insertion reported contention {direct} — the "
                f"shipped surface is REFUSAL-scoped and v5's "
                f"any-distinct-pair rule is what R2-3 rejected"]
    return []


def cell_live_refusal_contested(td) -> list:
    """The positive control: a GENUINE refusal must be reported — if this
    cell cannot fire, the negative cell proves nothing."""
    s2 = SqliteStore(f"{td}/refused.db")
    prior = _edge("p1", EvidenceAuthor.USER, "CFO at Acme")
    s2.add_edge(prior)
    inc = _edge("i1", EvidenceAuthor.THIRD_PARTY, "unemployed",
                Disclosure.QUARANTINED)
    s2.apply_supersession_plan(SupersessionPlan(
        incoming_edge=inc, insert_incoming=True, operation_id="op-1",
        expected_state=scope_fingerprint(
            s2.edges(U, subject="user", relation="works_as",
                     active_only=True, include_quarantined=True)),
        refusals=[SupersessionRefusalDraft(
            prior_edge_id=prior.id, incoming_edge_id=inc.id,
            relation="works_as",
            prior_effective=effective(
                prior.provenance.author_of_evidence, None),
            incoming_effective=effective(
                inc.provenance.author_of_evidence, None))]))
    live = _live_refusal_contention_edge_ids(s2, U, DEFAULT_RELATIONS)
    s2.close()
    if {"p1", "i1"} - live:
        return [f"a LIVE refusal reported contention {live}, missing one or "
                f"both edges"]
    return []


def run_cells() -> tuple:
    """Every cell in CELLS, executed, with the RAN list returned so a
    deleted or guarded cell is a registry mismatch rather than a silent
    narrowing (K1/K2, dev's own campaign 2026-08-28: deleting the positive
    control outright, and guarding the reviewer's cell with `if False`,
    both exited 0)."""
    bad, ran = [], []
    with tempfile.TemporaryDirectory() as td:
        for name in CELLS:
            fn = globals().get(name)
            if fn is None:
                bad.append(f"registry names {name} and no such cell exists")
                continue
            bad.extend(fn(td))
            ran.append(name)
    if ran != list(CELLS):
        bad.append(f"ran {ran}, registry declares {list(CELLS)}")
    return bad, ran


def main() -> int:
    bad, ran = run_cells()
    if bad:
        print("0011 §4c contention FAILED against the shipped surface:\n  "
              + "\n  ".join(bad), file=sys.stderr)
        return 1
    print(f"0011 §4c: contention is 0003's REFUSAL-scoped notion — "
          f"{len(ran)} cells on a real store: a direct distinct-value pair "
          f"is NOT contested (the reviewer's cell), a live refusal IS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
