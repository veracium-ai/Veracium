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
    ("new", "restore", "present, well-typed, FOREIGN lexicon version",
     "restored VERBATIM — the version field exists to mark provenance, "
     "and recomputation stays diagnostic-only (0026-R6-1: the "
     "unrecognised cell is DISTINCT from malformed — a well-typed "
     "record under another lexicon's version is not garbage, and "
     "refusing it would break restore round-trips of exports made "
     "under older lexicons; readers recompute under the current "
     "lexicon at consumption, per the default-mode rule)"),
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


def _cell(mode: str, state_substr: str) -> str:
    """The unique MATRIX outcome for (mode, state containing substr) —
    the projection render_2c_row builds from, so §2c can only ever say
    what the table says (0026-R5-1: the round-4 renderer hard-coded its
    text BESIDE the table; a mutated matrix regenerated §3d while §2c
    stayed contradictory and the binder returned clean — 'generated
    from the one table' was a name the behavior did not match)."""
    outs = [out for f, m, st, out in MATRIX
            if m == mode and state_substr in st]
    if len(outs) != 1:
        raise LookupError(
            f"MATRIX has {len(outs)} rows for mode={mode!r} "
            f"state~{state_substr!r} — the projection needs exactly one")
    return outs[0]


def _head(outcome: str) -> str:
    """The outcome's operative clause — the text before its rationale
    dash — so the §2c cell embeds the matrix's own words verbatim.

    STATED INVARIANT (research, round-5 pre-seal ask 2): the DECISION
    lives entirely pre-dash; everything after " — " is rationale. The
    §2c projection binds only heads, so `_assert_heads_distinct` below
    refuses a matrix whose heads collide — two rows whose decisions
    differ only in their rationale would project identically, and §2c
    would silently under-distinguish them."""
    return outcome.split(" — ")[0]


def _assert_heads_distinct() -> None:
    """Every MATRIX outcome head must be pairwise distinct — the guard
    that makes head-projection a faithful §2c carrier (round-5 pre-seal
    ask 2: the co-movement test mutated heads only, so nothing defended
    this invariant against a future edit)."""
    heads = [_head(out) for _f, _m, _st, out in MATRIX]
    dupes = sorted({h for h in heads if heads.count(h) > 1})
    if dupes:
        raise LookupError(
            f"MATRIX outcome heads collide: {dupes} — the decision must "
            f"live entirely before ' — ' and be distinct per row, or "
            f"the §2c head-projection under-distinguishes rows")


def render_2c_row() -> str:
    """The §2c untrusted-input row for the imported AgreementRecord,
    PROJECTED from MATRIX cell by cell: every mode-dependent clause is
    the matrix row's own operative text, so editing the table moves
    both renderings together (the source-level mutation test drives
    exactly that)."""
    _assert_heads_distinct()
    default_malformed = _head(_cell("default", "MALFORMED"))
    restore_malformed = _head(_cell("restore", "MALFORMED"))
    default_any = _head(_cell("default", "any state"))
    restore_valid = _head(_cell("restore", "VALID"))
    restore_foreign = _head(_cell("restore", "FOREIGN"))
    return (
        "| an imported `AgreementRecord` (§3d) "
        "| absent → default mode: " + default_any + "; restore: "
        + restore_valid + " (absent stays absent) "
        "| malformed → default: " + default_malformed + "; restore: "
        + restore_malformed + " — the two modes DIFFER by design "
        "(PROJECTED with the §3d matrix from `import_matrix.py`, the "
        "one carrier) "
        "| foreign `lexicon` version → default mode: " + default_any
        + " (incoming version diagnostic only); restore: "
        + restore_foreign + " (0026-R6-1: both modes stated — the cell "
        "was default-only) "
        "| forged markers on marker-free text → default mode: "
        + default_any + "; restore: " + restore_valid + " "
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
