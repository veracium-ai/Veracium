#!/usr/bin/env python3
"""0011 §4c — the contention rule, checked against SHIPPED 0012 behaviour.

External round 1, R1-3: v4 defined contention as ">=2 active same-class
edges" and that is FALSE against accepted 0012, which deliberately persists
a same-VALUE restatement as a separate active edge and calls the pair
uncontested. The reviewer executed
`test_a_same_value_restatement_produces_no_contention_artifacts` to show it.

This script checks the FOLD: the rule now requires >=2 distinct normalised
values, using 0012's OWN `_value_key` so the two notions cannot drift apart.
It runs under the reviewer's bare offline interpreter — it puts `src` on the
path itself rather than needing the package installed, which is why it is a
named script rather than a pytest invocation.

Run:  $PY specs/evidence/0011/check_contention_rule.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))

from veracium.graph import _value_key                        # noqa: E402


def contested(values) -> bool:
    """§4c as folded: >=2 active same-class edges carrying >=2 DISTINCT
    normalised values. `values` are the objects of the active same-class set."""
    return len(values) >= 2 and len({_value_key(v) for v in values}) >= 2


CELLS = (
    # (name, active same-class object values, expected)
    ("same_value_restatement_is_NOT_contention",
     ["cat named Minerva", "cat named Minerva"], False),
    ("same_value_after_normalisation_is_NOT_contention",
     ["cat named Minerva", "  Cat Named Minerva  "], False),
    ("two_distinct_values_ARE_contention", ["cat", "dog"], True),
    ("three_values_two_distinct_ARE_contention", ["cat", "cat", "dog"], True),
    ("a_single_edge_is_NOT_contention", ["cat"], False),
    ("no_edges_is_NOT_contention", [], False),
)


def main() -> int:
    bad = []
    for name, values, want in CELLS:
        got = contested(values)
        if got != want:
            bad.append(f"{name}: contested={got}, expected {want}")
    # the normalisation must be 0012's, not a second one: if these ever
    # disagree the rule has drifted from the spec it composes with
    if _value_key("Cat Named Minerva") != _value_key("cat named minerva"):
        bad.append("0012's _value_key no longer normalises case/space — the "
                   "rule's 'distinct value' notion has drifted from 0012's")
    if bad:
        print("0011 §4c contention rule FAILED:\n  " + "\n  ".join(bad),
              file=sys.stderr)
        return 1
    print(f"0011 §4c: {len(CELLS)} cells agree, over 0012's own _value_key — "
          f"same-value restatements are agreement, not contention")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
