"""specs/0026 §3d — THE import decision table, as data (0026-R4-2).

Round 3 added the restore-malformed RAISES rule; the fold wrote it into
two prose carriers and they immediately disagreed: §2c said "malformed
under EITHER mode raises" while §3d kept default-mode malformed at
treated-as-absent — and §2c's columns were displaced (the "malformed"
cell described well-formed input). The matrix test stayed green because
it checked selected substrings, not agreement between the carriers.

This module is the ONE carrier. Both spec representations are GENERATED
from `MATRIX` below (byte-bound by `spec_matrix_problems`, which the
packaged suite runs), so the two can no longer diverge — there is
nothing left to hand-edit into contradiction.
"""
from __future__ import annotations

import re

# (format era, mode, imported field state) -> outcome. TOTAL over the
# boundary; the behavior lives in src/veracium/portability.py and is
# exercised row-by-row by test_agreement_import_recomputes.
MATRIX = (
    ("old (pre-agreement)", "either", "absent by construction",
     "no fabrication; default mode floors at establishment as for any "
     "write; restore reproduces the old store verbatim"),
    ("new", "default", "any state (absent/present/forged/malformed/"
     "foreign-version)",
     "RECOMPUTED under the current lexicon (the V6a matrix above); "
     "floor runs; mismatches counted"),
    ("new", "restore", "present AND VALID, or absent",
     "restored VERBATIM, disclosure included (`0005` P2); recomputation "
     "diagnostic-only"),
    ("new", "restore", "present but MALFORMED (wrong types, unknown "
     "keys, markers outside any lexicon's grammar)",
     "**RAISES, nothing written** — verbatim restore into a typed "
     "carrier is impossible for garbage, and flooring it would silently "
     "accept a corrupt export (the R1-4 ruling, applied to the restore "
     "path); validation runs BEFORE any write, so a refused record "
     "leaves no partial state"),
    ("new", "default", "present but MALFORMED",
     "treated as absent; the recomputation governs (the V6a row above) "
     "— default mode never consumed the value anyway, so refusal is "
     "unnecessary and recomputation is total"),
    ("new file, old reader", "—", "—",
     "the reader REFUSES the bumped format (`0025`'s rule) — no silent "
     "field loss is reachable"),
)

_HEAD = "| format | mode | imported field | outcome |\n|---|---|---|---|"


def render_3d_table() -> str:
    """The §3d complete-boundary table, generated."""
    rows = "\n".join(f"| {f} | {m} | {st} | {out} |"
                     for f, m, st, out in MATRIX)
    return ("<!-- GENERATED:import-matrix (import_matrix.py — the ONE "
            "carrier; do not hand-edit) -->\n"
            + _HEAD + "\n" + rows + "\n"
            "<!-- /GENERATED:import-matrix -->")


def render_2c_row() -> str:
    """The §2c untrusted-input row for the imported AgreementRecord,
    generated FROM the same matrix: each §2c column carries the cell the
    matrix actually decides (round 4 found the hand-written row had the
    malformed rule under 'unrecognised' and a well-formed description
    under 'malformed')."""
    return (
        "| an imported `AgreementRecord` (§3d) "
        "| absent → default recomputes; restore keeps it absent "
        "| malformed → **default: treated as absent, recomputation "
        "governs, counted; restore: RAISES, nothing written** — the two "
        "modes DIFFER by design (generated with the §3d matrix from "
        "`import_matrix.py`, the one carrier) "
        "| foreign `lexicon` version → recomputation under the CURRENT "
        "lexicon governs; incoming version diagnostic only "
        "| forged markers on marker-free text → default discards by "
        "recomputation; restore restores the (valid) record verbatim "
        "with recomputation diagnostic-only "
        "| **V6a**: default mode recomputes so a forged record cannot "
        "enter Q5's corpus; restore is 0005-P2-faithful for VALID "
        "fields only, with validation ordered BEFORE any write |")


_BLOCK_RE = re.compile(
    r"<!-- GENERATED:import-matrix .*?/GENERATED:import-matrix -->", re.S)


def spec_matrix_problems(spec_text: str) -> list:
    """Byte-bind both representations to this module (0026-R4-2)."""
    out = []
    blocks = _BLOCK_RE.findall(spec_text)
    if len(blocks) != 1:
        out.append(f"the spec carries {len(blocks)} import-matrix "
                   f"generated blocks — exactly one is the contract")
    elif blocks[0] != render_3d_table():
        out.append("the spec's §3d import-matrix block does not "
                   "byte-match import_matrix.render_3d_table() — "
                   "regenerate, never hand-edit (0026-R4-2)")
    if render_2c_row() not in spec_text:
        out.append("the spec's §2c AgreementRecord row does not "
                   "byte-match import_matrix.render_2c_row() — the two "
                   "carriers must come from the one table (0026-R4-2)")
    return out


if __name__ == "__main__":
    import pathlib
    spec = (pathlib.Path(__file__).parents[2]
            / "0026-label-value-agreement.md")
    probs = spec_matrix_problems(spec.read_text())
    for p in probs:
        print(p)
    raise SystemExit(1 if probs else 0)
