#!/usr/bin/env python3
"""specs/0028 round 5 — THE EXECUTABLE SUCCESSOR-LOOKUP MODEL (R4-1, R4-5, the
reviewer's round-five request).

    python3 specs/evidence/0028/check_successor_lookup.py          # the six states × two principals, the table, the two invariants
    python3 specs/evidence/0028/check_successor_lookup.py --json OUT

WHAT THIS IS, STATED FIRST. `edges_superseding` is UNWRITTEN (src/veracium ships
only asof/). This file is the MODEL of the design v11 specifies for it — the
reference lookup written from the spec, run over six store states built on the
SHIPPED store through public writes, with the observation table and the two
invariants asserted. It is the executable form of the expectation (0029's rule:
research sets the bar, dev runs it); when the accessor is implemented, the
implementation is run against THIS table and these invariants, and the model
becomes the oracle. It does not claim the accessor exists.

THE DESIGN (research, 2026-09-07, folded as 0028 v11 §5.1):
  a successor outside the principal's ScopeView is NOT an omission — it is not
  in the view, indistinguishable in kind from one that does not exist; it
  produces no count and no cause. The result carries a closed three-value
  disposition and the visible successors, and NOTHING ELSE:
    HEAD                   the edge asserts no supersession and none is visible
    SUPERSEDED             >= 1 successor visible IN THIS VIEW
    SUCCESSOR_UNAVAILABLE  the edge asserts supersession (its own row's
                           invalidation_reason == "corrected", a fact the
                           principal already holds); none visible
  Precedence: visible successors → SUPERSEDED; else the edge's own assertion →
  SUCCESSOR_UNAVAILABLE; else HEAD. Total over every store state.
  Causes (DANGLING / CROSS_SCOPE / MALFORMED) survive as OPERATOR-ONLY
  diagnostics on 0031 §4d's precedent (the counters stripped from MCP results)
  and are never a field of a principal-facing result.

THE TWO INVARIANTS:
  V-NO-EXISTENCE-SIGNAL   for a principal without scope, the result from a
                          HIDDEN successor equals, FIELD BY FIELD (whole-object
                          equality, never a flag), the result from a MISSING one
  V-UNAVAILABLE-NEVER-HEAD  SUCCESSOR_UNAVAILABLE is never HEAD: the head
                          predicate is False for it, for any principal, at any T
  (Collapsing the hidden case into HEAD would trade a leak for a lie — B is told
   the chain cannot be closed, never that a superseded edge is current.)

THE STATES — the reviewer's six, plus three the design's own correction added,
built by public writes on ONE store, both principals observing every one:
  head, missing, visible, multiple, hidden (retired `corrected`, successor
  hidden); hidden_superseded and hidden_absorbed (retired `superseded` /
  `absorbed_duplicate` through the public invalidate_edge, successor hidden —
  reachable states that must read exactly as the corrected case does); and
  hidden_unretired — the CONTRAST: an un-retired prior with a hidden successor
  reads HEAD for the principal without scope, and that is correct, because the
  edge's own row asserts nothing, so the view is internally consistent. The
  distinction is whether the edge's own row makes a claim the disposition would
  contradict.
  State "missing" (the successor row gone after a real correction) is
  constructible only by a raw DELETE: no shipped writer produces it — §4b-iii's
  "store state no shipped writer produces" class, and this file says so rather
  than implying the fixture is a reachable path. State "multiple" as built has
  two successor rows naming a prior that was NOT retired (plain add_edge with
  `supersedes`) — a state the public write surface admits; precedence puts
  visible successors first, so it is SUPERSEDED for both principals.

# Mutation-Matrix: tests/test_0028_successor_lookup.py::test_v9_typed_result_reintroduces_the_existence_signal
# (siblings there: a head predicate ignoring the integrity signal; collapsing the hidden
#  case into HEAD; a string admitted into the vocabulary; the observation table itself)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


def _add_src_to_path():
    here = pathlib.Path(__file__).resolve()
    for p in here.parents:
        if (p / "src" / "veracium" / "__init__.py").exists():
            sys.path.insert(0, str(p / "src")); return
_add_src_to_path()

from veracium.graph import plan_correction                              # noqa: E402
from veracium.schema import (CorrectionAuthorisation, Disclosure, Edge,  # noqa: E402
                             EvidenceAuthor, Provenance, correction_digest)
from veracium.scope import Identity, validate_policy                      # noqa: E402
from veracium.scope_read import ScopeView                                 # noqa: E402
from veracium.store.sqlite import SqliteStore                             # noqa: E402

from veracium.schema import DISPOSITIONED_REASONS                          # noqa: E402

U = "u-succ"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
D = timedelta(days=1)

# THE THIRD REGISTRY (v11 §5.1): which invalidation reasons NAME A SUCCESSOR, so
# that an edge retired under them "asserts supersession" and its lookup, with no
# visible successor, is SUCCESSOR_UNAVAILABLE and never HEAD. TOTAL over
# DISPOSITIONED_REASONS under the same build-time equality gate as
# AS_OF_DISPOSITION (schema.py: "every DISPOSITIONED_REASONS key, explicitly"),
# so a producer growing a new reason must disposition it here in the same edit.
# The first cut of this model carried a hand set {"corrected"} — under-inclusive:
# `superseded` (W2, the supersession path) and `absorbed_duplicate` ("0028
# resolves to the absorber", the registry's own comment) also name a successor,
# and an edge retired under either with a hidden successor fell through to HEAD —
# a lie the principal could catch on the edge's own row. Research's finding,
# 2026-09-07. v11 specifies this registry in schema.py; the model carries it
# until the implementation lands.
NAMES_A_SUCCESSOR: dict = {
    "corrected":          True,    # the host replaced the content — a replacement exists
    "superseded":         True,    # W2 — the supersession path
    "absorbed_duplicate": True,    # W8 — 0028 resolves to the absorber
    "disputed":           False,   # trust revoked; no successor is named
    "revoked_source":     False,   # 0022's withdrawal; no successor
    "lapsed":             False,   # staleness
    "decayed":            False,   # staleness
}


def check_registry_total(names_a_successor=None, dispositioned=None):
    """The build-time gate: the registry is total over DISPOSITIONED_REASONS —
    equality, not subset, in both directions."""
    a = set(names_a_successor if names_a_successor is not None else NAMES_A_SUCCESSOR)
    b = set(dispositioned if dispositioned is not None else DISPOSITIONED_REASONS)
    if a != b:
        raise AssertionError(f"NAMES_A_SUCCESSOR is not total over DISPOSITIONED_REASONS: "
                             f"missing {sorted(b - a)}, extra {sorted(a - b)}")


check_registry_total()
ASSERTS_SUPERSESSION = frozenset(r for r, names in NAMES_A_SUCCESSOR.items() if names)


# ------------------------------------------------------------------ the design
class SuccessorDisposition(str, Enum):
    HEAD = "head"
    SUPERSEDED = "superseded"
    SUCCESSOR_UNAVAILABLE = "successor_unavailable"


@dataclass(frozen=True)
class SuccessorLookup:
    disposition: SuccessorDisposition
    successors: tuple            # tuple[Edge, ...]; empty unless SUPERSEDED
    # NO `omitted`. NO `causes`. Their absence is the invariant.


def successor_lookup(store, user_id, edge_id, principal, policy, *, names_successor=None) -> SuccessorLookup:
    """THE MODEL of v11 §5.1's accessor: one user's edges, filtered by the shared
    ScopeView for the principal, precedence as the design states. `names_successor`
    is the registry-derived reason set; injectable so the matrix can plant the
    under-inclusive hand set against the same fixtures."""
    asserts = ASSERTS_SUPERSESSION if names_successor is None else frozenset(names_successor)
    view = ScopeView(store, user_id, principal, policy)
    rows = store.edges(user_id, active_only=False, include_quarantined=True)
    me = next((e for e in rows if e.id == edge_id), None)
    visible = tuple(e for e in rows if e.supersedes == edge_id and view.visible(e))
    if visible:
        return SuccessorLookup(SuccessorDisposition.SUPERSEDED, visible)
    if me is not None and me.invalidation_reason in asserts:
        return SuccessorLookup(SuccessorDisposition.SUCCESSOR_UNAVAILABLE, ())
    return SuccessorLookup(SuccessorDisposition.HEAD, ())


def is_head(lookup: SuccessorLookup) -> bool:
    """The head predicate the pointer walk terminates on (R4-5): HEAD only —
    never SUCCESSOR_UNAVAILABLE (the chain cannot be closed; the resolver's
    INDETERMINATE), never SUPERSEDED."""
    return lookup.disposition is SuccessorDisposition.HEAD


# ---------------------------------------------------------------- the fixtures
def edge(obj, *, source="mb-a", valid_from=T0, supersedes=None):
    return Edge(id=f"e-{uuid.uuid4().hex[:10]}", user_id=U, subject="user", relation="located_at",
                object=obj, valid_from=valid_from, supersedes=supersedes,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}", source_id=source,
                                      disclosure=Disclosure.MENTIONABLE, observed_at=valid_from))


def correct(store, prior, replacement):
    """A real DIRECTED correction through the shipped planner and the 0011 §4e
    binding — the path `Memory.correct` takes, not a bypass."""
    plan, refused = plan_correction(store, prior, replacement, f"op-{uuid.uuid4().hex[:8]}")
    assert not refused, refused
    auth = CorrectionAuthorisation(origin=store.local_origin(), prior_edge_id=prior.id,
                                   replacement_digest=correction_digest(replacement.object),
                                   kind="corrected", principal="user")
    store.apply_supersession_plan(plan, authorisation=auth, acting_principal="user")
    return replacement


def principals(store):
    """A: cross-scope visible. B: not. Real Identities through the real policy
    validator; membership is 0021's shared resolver, exercised, not re-verified."""
    A = (Identity(origin=None, source_id="mb-a"),
         validate_policy({}, cross_scope_visible=True, local_origin=store.local_origin()))
    B = (Identity(origin=None, source_id="mb-a"),
         validate_policy({}, cross_scope_visible=False, local_origin=store.local_origin()))
    return A, B


def build(path) -> tuple:
    """The six states on ONE store. Returns (store, {state: queried edge id})."""
    s = SqliteStore(str(path))
    head = edge("Porto"); s.add_edge(head)
    gone_prior = edge("Braga"); s.add_edge(gone_prior)
    gone_succ = correct(s, gone_prior, edge("Braga (fixed)", supersedes=gone_prior.id, valid_from=T0 + D))
    # "missing": the successor row GONE after a real correction — no shipped writer
    # produces this (§4b-iii's class); a raw DELETE is the only constructor, stated.
    s._conn.execute("DELETE FROM edges WHERE id=?", (gone_succ.id,)); s._conn.commit()
    vis_prior = edge("Lisbon"); s.add_edge(vis_prior)
    correct(s, vis_prior, edge("Lisbon (fixed)", supersedes=vis_prior.id, valid_from=T0 + D))
    multi_prior = edge("Faro"); s.add_edge(multi_prior)
    s.add_edge(edge("Faro (a)", supersedes=multi_prior.id, valid_from=T0 + D))
    s.add_edge(edge("Faro (b)", supersedes=multi_prior.id, valid_from=T0 + 2 * D))
    hid_prior = edge("Coimbra"); s.add_edge(hid_prior)
    correct(s, hid_prior, edge("Coimbra (foreign)", source="other-mailbox",
                               supersedes=hid_prior.id, valid_from=T0 + D))
    # the other two reasons that NAME a successor, each retired through the public
    # `invalidate_edge` with a cross-scope successor row — reachable states, unlike
    # "missing"; both must read as the `corrected` hidden case does
    sup_prior = edge("Aveiro"); s.add_edge(sup_prior)
    s.invalidate_edge(sup_prior.id, T0 + D, "superseded")
    s.add_edge(edge("Aveiro (foreign)", source="other-mailbox", supersedes=sup_prior.id, valid_from=T0 + D))
    abs_prior = edge("Viseu"); s.add_edge(abs_prior)
    s.invalidate_edge(abs_prior.id, T0 + D, "absorbed_duplicate")
    s.add_edge(edge("Viseu (foreign)", source="other-mailbox", supersedes=abs_prior.id, valid_from=T0 + D))
    # the CONTRAST that stays HEAD: an UN-retired prior with a hidden successor —
    # its own row asserts nothing, so B's view is internally consistent
    unret_prior = edge("Guarda"); s.add_edge(unret_prior)
    s.add_edge(edge("Guarda (foreign)", source="other-mailbox", supersedes=unret_prior.id, valid_from=T0 + D))
    return s, {"head": head.id, "missing": gone_prior.id, "visible": vis_prior.id,
               "multiple": multi_prior.id, "hidden": hid_prior.id,
               "hidden_superseded": sup_prior.id, "hidden_absorbed": abs_prior.id,
               "hidden_unretired": unret_prior.id}


EXPECTED = {   # the observation table v11 §5.1 states, (A, B) dispositions and visible counts
    "head":     (("head", 0), ("head", 0)),
    "missing":  (("successor_unavailable", 0), ("successor_unavailable", 0)),
    "visible":  (("superseded", 1), ("superseded", 1)),
    "multiple": (("superseded", 2), ("superseded", 2)),
    "hidden":   (("superseded", 1), ("successor_unavailable", 0)),
    "hidden_superseded": (("superseded", 1), ("successor_unavailable", 0)),
    "hidden_absorbed":   (("superseded", 1), ("successor_unavailable", 0)),
    "hidden_unretired":  (("superseded", 1), ("head", 0)),   # the row asserts nothing: HEAD is consistent
}
HIDDEN_RETIRED = ("hidden", "hidden_superseded", "hidden_absorbed")   # every retired-with-a-named-successor hidden case


def observe(store, ids, A, B):
    out = {}
    for name, eid in ids.items():
        la = successor_lookup(store, U, eid, *A); lb = successor_lookup(store, U, eid, *B)
        out[name] = (la, lb)
    return out


def run(lookup=successor_lookup, head_pred=is_head, workdir=None):
    """Runs the model; returns (ok, report). `lookup`/`head_pred` are injectable so the
    matrix can plant the mutants against the same fixtures."""
    d = pathlib.Path(workdir or tempfile.mkdtemp(prefix="succ-model-"))
    s, ids = build(d / "s.db")
    try:
        A, B = principals(s)
        obs = {n: (lookup(s, U, e, *A), lookup(s, U, e, *B)) for n, e in ids.items()}
        table_ok = all((obs[n][0].disposition.value, len(obs[n][0].successors)) == EXPECTED[n][0]
                       and (obs[n][1].disposition.value, len(obs[n][1].successors)) == EXPECTED[n][1]
                       for n in EXPECTED)
        no_signal = all(obs[n][1] == obs["missing"][1] for n in HIDDEN_RETIRED)   # WHOLE-OBJECT equality, every retired hidden case
        never_head = all(not head_pred(obs[n][1]) for n in ("missing",) + HIDDEN_RETIRED) \
            and not head_pred(obs["missing"][0])
        vocab_closed = all(isinstance(l.disposition, SuccessorDisposition)
                           and set(vars(l)) == {"disposition", "successors"}
                           for pair in obs.values() for l in pair)
        rows = {n: {"A": (obs[n][0].disposition.value, len(obs[n][0].successors)),
                    "B": (obs[n][1].disposition.value, len(obs[n][1].successors))} for n in obs}
        return (table_ok and no_signal and never_head and vocab_closed,
                {"table": rows, "table_matches_spec": table_ok,
                 "V-NO-EXISTENCE-SIGNAL (B: hidden == missing, whole object)": no_signal,
                 "V-UNAVAILABLE-NEVER-HEAD": never_head,
                 "vocabulary closed and result has exactly two fields": vocab_closed})
    finally:
        s.close()


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--json"); a = ap.parse_args(argv)
    ok, rep = run()
    print(f"SUCCESSOR-LOOKUP MODEL over the shipped store — {len(EXPECTED)} states × two principals (A cross-visible, B not)")
    print("the accessor is UNWRITTEN; this is the executable expectation, run against the model lookup")
    print(f"{'state':10} {'A':>28} {'B':>28}")
    for n, r in rep["table"].items():
        print(f"{n:10} {str(r['A']):>28} {str(r['B']):>28}")
    for k, v in rep.items():
        if k != "table":
            print(f"{'PASS' if v else 'FAIL'}  {k}")
    print("MODEL:", "OK" if ok else "FAILED")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({"ok": ok, **rep}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
