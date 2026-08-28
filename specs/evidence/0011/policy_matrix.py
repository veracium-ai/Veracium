#!/usr/bin/env python3
"""0011 §4b — the entitlement policy as an EXECUTABLE, FULL-EDGE oracle.

Round 4 (EVIDENCE-R4-1) found the previous version's source and origin
dimensions were DECORATIVE: enumerated in `cells()` but never passed to
`policy()`, and the invariance check re-called `policy(a, d, sc)` instead of
comparing the EMITTED cells — so a planted source-conditional ALLOW in the
emission stream exited 0 while the oracle printed that source identity was
invariant. An oracle that does not consume its own output certifies its
inputs, not its subject.

This version:

* builds REAL `Edge` objects — the decision's inputs are two edges with full
  `Provenance`, so source_id and origin are genuinely inside the domain;
* derives every check from the ONE emitted stream (`problems()` consumes
  `cells()`), so a mutation in the emission is a mutation in what is judged;
* runs the IMPORT-FLATTENED cell through the production adapter —
  `portability.import_memory` — in both modes, rather than asserting what
  the cap would do;
* is mutation-tested: tests/test_0011_policy_matrix.py plants the round-4
  attack (emitted-cell variance) and requires this oracle to catch it.

The predicate under test is unchanged from v7 (FINITE DESIGN ACCEPTANCE,
round 4 — the authority-chain construction is not reopened):

    self_assertion(e) := effective(author, derived_from) == effective(USER, None)

Run:  $PY specs/evidence/0011/policy_matrix.py
      $PY specs/evidence/0011/policy_matrix.py --table
"""
from __future__ import annotations

import itertools
import pathlib
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))

from veracium.authority import effective                        # noqa: E402
from veracium.schema import (Disclosure, Edge, EvidenceAuthor as A,  # noqa: E402
                             Provenance)

NOW = datetime(2026, 5, 1, tzinfo=timezone.utc)
U = "u"

AUTHORS = list(A)
DERIVED = [None] + list(A)
SUBJECTS = ("user", "user's sister")           # SELF and OTHER, real strings
SOURCES = (None, "feed-a", "caller-chosen-anything")
ORIGINS = (None, "11111111-2222-4333-8444-555555555555")

USER_CHAIN = effective(A.USER, None)


def make_edge(eid, subject, author, derived, source_id, origin):
    return Edge(id=eid, user_id=U, subject=subject, relation="works_as",
                object="CFO at Acme", valid_from=NOW, active=True,
                provenance=Provenance(author_of_evidence=author,
                                      derived_from=derived,
                                      evidence_ref=f"r-{eid}",
                                      source_id=source_id, origin=origin,
                                      observed_at=NOW,
                                      disclosure=Disclosure.MENTIONABLE))


def subject_class(prior: Edge) -> str:
    """The shipped predicate: whole-string casefold equality (0024 §4a)."""
    return ("SELF" if str(prior.subject).strip().casefold() == "user"
            else "OTHER")


def self_assertion(e: Edge) -> bool:
    """The chain carries nothing but the user's own authority."""
    return effective(e.provenance.author_of_evidence,
                     e.provenance.derived_from) == USER_CHAIN


def policy(incoming: Edge, prior: Edge) -> str:
    """§4b, over the FULL EDGES. Total: REFUSE or ALLOW, always."""
    if subject_class(prior) == "OTHER" and self_assertion(incoming):
        return "REFUSE"
    return "ALLOW"


def cells():
    """The emitted stream — EVERYTHING downstream judges only this.

    Incoming and prior carry INDEPENDENT source and origin values, and both
    edges are built for real, so the decision inputs actually contain the
    dimensions the invariance claim is about.
    """
    n = 0
    for a, d, subj, src_in, src_pr, org_in, org_pr in itertools.product(
            AUTHORS, DERIVED, SUBJECTS, SOURCES, SOURCES, ORIGINS, ORIGINS):
        n += 1
        incoming = make_edge(f"i{n}", "user", a, d, src_in, org_in)
        prior = make_edge(f"p{n}", subj, A.THIRD_PARTY, None, src_pr, org_pr)
        yield (a, d, subject_class(prior), src_in, src_pr, org_in, org_pr,
               policy(incoming, prior))


def import_flattened_cells() -> list:
    """The import path, THROUGH THE PRODUCTION ADAPTER (EVIDENCE-R4-1).

    A USER-authored, underived edge is exported clean and imported into a
    fresh store both ways. The 0005 default cap FLATTENS the author to
    THIRD_PARTY; restore=True preserves it. The cell is what the policy
    decides about the edge THE ADAPTER PRODUCED — measured, not asserted.
    Returns (mode, imported_author, decision) triples.
    """
    from veracium import portability as P
    from veracium.store.sqlite import SqliteStore

    out = []
    with tempfile.TemporaryDirectory() as td:
        src = SqliteStore(f"{td}/src.db")
        src.add_edge(make_edge("e1", "user", A.USER, None, "feed-a", None))
        exp = pathlib.Path(td) / "clean.jsonl"
        P.export_memory(src, U, exp)
        src.close()
        prior_other = make_edge("prior", "user's sister", A.THIRD_PARTY,
                                None, "feed-b", None)
        for mode, restore in (("default", False), ("restore", True)):
            dst = SqliteStore(f"{td}/{mode}.db")
            P.import_memory(dst, exp, restore=restore)
            (imported,) = [e for e in dst.edges(U, active_only=False)]
            out.append((mode, imported.provenance.author_of_evidence,
                        policy(imported, prior_other)))
            dst.close()
    return out


def problems(stream=None) -> list:
    """Every check is over the EMITTED stream (or an injected one — which is
    how the mutation test plants the round-4 attack and requires a bite)."""
    bad = []
    seen = list(cells() if stream is None else stream)

    # EVIDENCE-R5-1: a COUNT does not prove COVERAGE. The previous check
    # required 1,440 rows, and replacing one cell with a duplicate of
    # another kept the count while a source/origin combination silently
    # vanished — cardinality-preserving omission. So the EXACT expected
    # Cartesian key set is constructed independently and the emitted keys
    # must equal it: set equality catches a missing key and an alien key,
    # and the separate duplicate check catches the replacement itself
    # (with plain set equality alone, a duplicate would hide behind the
    # missing-key report it causes).
    # M1/M2 (own campaign, 2026-08-28): the expected key set is built from
    # the SAME dimension constants as the emitter, so narrowing a constant
    # shrinks both sides together and set equality stays green while the
    # domain quietly narrows. The enum-derived dimensions grow legitimately
    # with the enum; the HAND-PICKED ones are pinned here as literals, with
    # the members the checks depend on named.
    if len(SOURCES) != 3 or None not in SOURCES or not any(
            s and "caller" in s for s in SOURCES if s):
        bad.append(f"SOURCES narrowed to {SOURCES!r} — the declared domain "
                   f"is 3 states incl. absent and a caller-chosen value")
    if len(ORIGINS) != 2 or None not in ORIGINS:
        bad.append(f"ORIGINS narrowed to {ORIGINS!r} — the declared domain "
                   f"is 2 states incl. absent")
    subj_classes = {("SELF" if s == "user" else "OTHER") for s in SUBJECTS}
    if subj_classes != {"SELF", "OTHER"}:
        bad.append(f"SUBJECTS {SUBJECTS!r} no longer covers both subject "
                   f"classes — every refusal cell would vanish with OTHER")
    expected_keys = {
        (a, d, ("SELF" if subj == "user" else "OTHER"), si, sp, oi, op)
        for a in AUTHORS for d in DERIVED for subj in SUBJECTS
        for si in SOURCES for sp in SOURCES
        for oi in ORIGINS for op in ORIGINS}
    emitted_keys = [row[:-1] for row in seen]
    dupes = {k for k in emitted_keys if emitted_keys.count(k) > 1}
    if dupes:
        k = sorted(map(str, dupes))[0]
        bad.append(f"{len(dupes)} cell key(s) emitted MORE THAN ONCE, e.g. "
                   f"{k} — a duplicate is how a missing cell hides at "
                   f"constant cardinality")
    missing = expected_keys - set(emitted_keys)
    alien = set(emitted_keys) - expected_keys
    if missing:
        bad.append(f"{len(missing)} expected cell key(s) NEVER EMITTED, "
                   f"e.g. {sorted(map(str, missing))[0]}")
    if alien:
        bad.append(f"{len(alien)} emitted key(s) outside the declared "
                   f"domain, e.g. {sorted(map(str, alien))[0]}")
    if any(row[-1] not in ("REFUSE", "ALLOW") for row in seen):
        bad.append("a cell decided neither REFUSE nor ALLOW")

    # AUTHORITY EQUIVALENCE + SOURCE/ORIGIN INVARIANCE, on the EMITTED rows:
    # group by (effective authority, subject class); every emitted outcome in
    # a group must agree. This subsumes the named R3-1 cell and catches a
    # variance planted anywhere in the emission — the round-4 attack.
    groups: dict = {}
    for a, d, sc, _si, _sp, _oi, _op, out in seen:
        groups.setdefault((effective(a, d), sc), set()).add(out)
    for (auth, sc), outs in sorted(groups.items()):
        if len(outs) > 1:
            bad.append(f"authority {auth} / subject {sc} decides {outs} "
                       f"across emitted cells — equal authority must decide "
                       f"equally, and any variance within a group is some "
                       f"non-authority input (source, origin) granting")

    # the named cells, read FROM the stream rather than recomputed
    def emitted(a, d, sc):
        return {row[-1] for row in seen
                if row[0] is a and row[1] is d and row[2] == sc}
    if emitted(A.USER, None, "OTHER") != {"REFUSE"}:
        bad.append("USER/None/OTHER is not uniformly REFUSE in the stream")
    if emitted(A.USER, A.USER, "OTHER") != {"REFUSE"}:
        bad.append("R3-1: USER/derived(USER)/OTHER is not uniformly REFUSE")
    for a, d in itertools.product(AUTHORS, DERIVED):
        if emitted(a, d, "SELF") != {"ALLOW"}:
            bad.append(f"{a.value}/{d}/SELF is not uniformly ALLOW")
            break
    for low in (A.SYSTEM, A.ASSISTANT, A.THIRD_PARTY):
        if emitted(low, A.USER, "OTHER") != {"ALLOW"}:
            bad.append(f"{low.value} derived_from=USER counted as the "
                       f"USER's self-assertion — derived_from caps, never "
                       f"grants")
        if effective(low, A.USER) > effective(low, None):
            bad.append(f"derived_from=USER RAISED {low.value}'s authority")

    # the import-flattened cell, through the production adapter
    imp = import_flattened_cells()
    by_mode = {m: (auth, dec) for m, auth, dec in imp}
    if by_mode.get("default", (None, None))[1] != "ALLOW":
        bad.append(f"import(default): the 0005 cap flattens the author, so "
                   f"the imported edge must NOT be a self-assertion — got "
                   f"{by_mode.get('default')}")
    if by_mode.get("default", (None, None))[0] is A.USER:
        bad.append("import(default): the author arrived UNflattened — the "
                   "production cap did not run")
    if by_mode.get("restore", (None, None))[1] != "REFUSE":
        bad.append(f"import(restore): a faithfully-restored USER edge must "
                   f"still be a self-assertion — got {by_mode.get('restore')}")
    return bad


def render() -> str:
    out = ["| author | derived_from | effective | subject OTHER | subject SELF |",
           "|---|---|---|---|---|"]
    for a, d in itertools.product(AUTHORS, DERIVED):
        pr_o = make_edge("po", "user's sister", A.THIRD_PARTY, None, None, None)
        pr_s = make_edge("ps", "user", A.THIRD_PARTY, None, None, None)
        inc = make_edge("i", "user", a, d, None, None)
        out.append(f"| `{a.value}` | `{d.value if d else 'None'}` | "
                   f"{effective(a, d)} | **{policy(inc, pr_o)}** | "
                   f"{policy(inc, pr_s)} |")
    return "\n".join(out)


def main() -> int:
    if "--table" in sys.argv:
        print(render())
        return 0
    bad = problems()
    if bad:
        print("0011 §4b policy matrix FAILED:\n  " + "\n  ".join(bad),
              file=sys.stderr)
        return 1
    total = (len(AUTHORS) * len(DERIVED) * len(SUBJECTS)
             * len(SOURCES) ** 2 * len(ORIGINS) ** 2)
    print(f"0011 §4b: {total} full-edge cells emitted and judged FROM THE "
          f"STREAM; equal authority decides equally across independent "
          f"incoming/prior source and origin values; the import-flattened "
          f"cell ran through portability.import_memory in both modes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
