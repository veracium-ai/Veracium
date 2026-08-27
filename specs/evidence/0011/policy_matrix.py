#!/usr/bin/env python3
"""0011 §4b — the entitlement policy as an EXECUTABLE matrix.

Asked for in every round so far, and shipped only now. Each round I fixed the
named field and the reviewer found the same class one field over:

    R1-1  the rule was not representable   -> defined over `source_id`
    R2-1  `source_id` GRANTS (0006 forbids) -> redefined over `derived_from is None`
    R3-1  `derived_from` GRANTS             -> a marker carrying NO authority
                                               bought permission: USER/None and
                                               USER/derived_from=USER have the
                                               SAME effective authority (3) and
                                               the draft refused one, allowed
                                               the other

The common defect is keying on the PRESENCE OR ABSENCE OF AN UNAUTHENTICATED
MARKER. Every fix that swapped one marker for another inherited it. So the
predicate is defined over the AUTHORITY CHAIN, computed by production
`effective()` — the same function 0003's ladder uses:

    self_assertion(e) := effective(author, derived_from) == effective(USER, None)

which reads: the chain carries nothing but the user's own authority. Enumerated
against production authority, exactly two chains satisfy it — (USER, None) and
(USER, USER) — so R3-1's bypass cell is in the refusal set BY CONSTRUCTION, not
by patch. A marker that changes no authority cannot move a decision, because
the decision is a function of authority. A marker that DOES change authority
moves it for a stated reason.

Run:  $PY specs/evidence/0011/policy_matrix.py
      $PY specs/evidence/0011/policy_matrix.py --table   (the rendered matrix)
"""
from __future__ import annotations

import itertools
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))

from veracium.authority import effective                        # noqa: E402
from veracium.schema import EvidenceAuthor as A                  # noqa: E402

AUTHORS = list(A)
DERIVED = [None] + list(A)
SUBJECT_CLASSES = ("SELF", "OTHER")
# source identity is NOT an input. It is enumerated anyway, to PROVE it is
# not an input rather than to assert it (R2-1, and 0006's GROUP-never-GRANT).
SOURCE_STATES = (None, "feed-a", "caller-chosen-anything")
ORIGINS = (None, "foreign-origin-uuid")

USER_CHAIN = effective(A.USER, None)


def self_assertion(author, derived_from) -> bool:
    """The chain carries nothing but the user's own authority."""
    return effective(author, derived_from) == USER_CHAIN


def policy(incoming_author, incoming_derived, prior_subject_class) -> str:
    """§4b. TOTAL: every cell returns REFUSE or ALLOW."""
    if prior_subject_class == "OTHER" and self_assertion(incoming_author,
                                                         incoming_derived):
        return "REFUSE"
    return "ALLOW"


def cells():
    for a, d, sc, src, org in itertools.product(
            AUTHORS, DERIVED, SUBJECT_CLASSES, SOURCE_STATES, ORIGINS):
        yield a, d, sc, src, org, policy(a, d, sc)


def problems() -> list:
    bad = []
    seen = list(cells())

    # 1. TOTALITY — no cell undecided, and the domain is genuinely enumerated
    if any(r not in ("REFUSE", "ALLOW") for *_x, r in seen):
        bad.append("a cell returned neither REFUSE nor ALLOW")
    expected = (len(AUTHORS) * len(DERIVED) * len(SUBJECT_CLASSES)
                * len(SOURCE_STATES) * len(ORIGINS))
    if len(seen) != expected:
        bad.append(f"enumerated {len(seen)} cells, expected {expected}")

    # 2. R3-1, THE NAMED BYPASS: identical authority must decide identically
    a1 = policy(A.USER, None, "OTHER")
    a2 = policy(A.USER, A.USER, "OTHER")
    if not (a1 == a2 == "REFUSE"):
        bad.append(f"R3-1: USER/None -> {a1} but USER/derived(USER) -> {a2}; "
                   f"both carry effective authority {USER_CHAIN} and a marker "
                   f"with no authority must not move the decision")

    # 3. AUTHORITY EQUIVALENCE, generalised: any two chains with the same
    #    effective authority must decide the same way for the same subject
    #    class. This is the CLASS of R2-1/R3-1, not the two named instances.
    by_auth: dict = {}
    for a, d in itertools.product(AUTHORS, DERIVED):
        for sc in SUBJECT_CLASSES:
            by_auth.setdefault((effective(a, d), sc), set()).add(
                policy(a, d, sc))
    for (auth, sc), outcomes in sorted(by_auth.items()):
        if len(outcomes) > 1:
            bad.append(f"authority {auth} / subject {sc} decides {outcomes} "
                       f"— equal authority must decide equally, or some "
                       f"input other than authority is granting")

    # 4. SOURCE-IDENTITY INVARIANCE (0006: may GROUP, never GRANT)
    for a, d, sc in itertools.product(AUTHORS, DERIVED, SUBJECT_CLASSES):
        outs = {policy(a, d, sc) for _src in SOURCE_STATES
                for _org in ORIGINS}
        if len(outs) > 1:
            bad.append(f"{a.value}/{d}/{sc} varies with source identity")

    # 5. THE LAUNDERING CELLS, decided explicitly rather than by default.
    #    derived_from CAPS authority (min); it can never raise a class. So a
    #    lower class marked derived_from=USER stays its own class and is NOT
    #    a user self-assertion.
    for low in (A.SYSTEM, A.ASSISTANT, A.THIRD_PARTY):
        if self_assertion(low, A.USER):
            bad.append(f"{low.value} derived_from=USER counted as the USER's "
                       f"self-assertion — derived_from caps, never grants")
        if effective(low, A.USER) > effective(low, None):
            bad.append(f"derived_from=USER RAISED {low.value}'s authority")

    # 6. SELF-subject priors are never refused by this rule — the widening is
    #    about OTHER-subject facts, and a rule that refused a user editing
    #    their own record would be a different spec.
    for a, d in itertools.product(AUTHORS, DERIVED):
        if policy(a, d, "SELF") != "ALLOW":
            bad.append(f"{a.value}/{d} refused on a SELF-subject prior")
    return bad


def render() -> str:
    out = ["| author | derived_from | effective | subject OTHER | subject SELF |",
           "|---|---|---|---|---|"]
    for a, d in itertools.product(AUTHORS, DERIVED):
        out.append(f"| `{a.value}` | `{d.value if d else 'None'}` | "
                   f"{effective(a, d)} | **{policy(a, d, 'OTHER')}** | "
                   f"{policy(a, d, 'SELF')} |")
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
    n = len(list(cells()))
    refusing = sum(1 for a, d in itertools.product(AUTHORS, DERIVED)
                   if policy(a, d, "OTHER") == "REFUSE")
    print(f"0011 §4b: {n} cells decided, total; {refusing} of "
          f"{len(AUTHORS) * len(DERIVED)} author/derivation chains refuse on "
          f"an OTHER-subject prior; equal authority decides equally; the "
          f"decision is invariant under source identity and origin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
