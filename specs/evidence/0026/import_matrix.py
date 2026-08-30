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
    ("new", "restore", "present, well-typed, FOREIGN lexicon version "
     "(markers OPAQUE: e.g. markers=['future_marker'] under "
     "lexicon='0026-lex-999')",
     "restored VERBATIM — the version field exists to mark provenance, "
     "and recomputation stays diagnostic-only. GRAMMAR MEMBERSHIP IS "
     "VERSION-SCOPED (0026-R7-1): under a foreign version the reader "
     "CANNOT know that lexicon's vocabulary, so markers are validated "
     "as OPAQUE closed shapes only — nonempty bounded strings, bounded "
     "count, closed record types — never for membership; the "
     "malformed row's out-of-grammar rule applies ONLY under the "
     "CURRENT version, where the vocabulary is known (0026-R6-1: a "
     "well-typed foreign record is not garbage, and refusing it would "
     "break restore round-trips of old exports; readers recompute "
     "under the current lexicon at consumption)"),
    ("new", "restore", "present but MALFORMED (wrong types, unknown "
     "keys, or — under the CURRENT lexicon version only — markers "
     "outside its grammar; foreign-version membership is unknowable "
     "and handled by the opaque rule above, 0026-R7-1)",
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


# 0026-R8-2: "nonempty bounded strings" with no bounds let conforming
# implementations accept DIFFERENT inputs. The shape is DATA now, with a
# RUNNING reference validator — the future Edge.agreement implementation
# must match agreement_shape_problems, and the standing test drives every
# bound at the limit and one beyond.
AGREEMENT_SHAPE = {
    "keys": ("markers", "direction", "lexicon"),   # CLOSED — unknown
                                                   # keys REFUSE
    "markers_type": "JSON array of strings",
    "markers_max_count": 8,     # MEASURED basis (research, round-8
                                # pre-seal): max distinct markers per
                                # record over the full cache = 2
                                # (2,349 records at 1, 64 at 2); 8 is
                                # measured-max x4 margin, not taste
    "marker_min_chars": 1,
    "marker_max_chars": 64,     # MEASURED basis: the longest shipped
                                # lexicon member is 'on the advice of'
                                # at 16 chars; 64 is x4 margin
    "markers_duplicates": "REFUSE",
    "direction_values": ("inbound", "outbound", "ambiguous"),  # CLOSED
    "lexicon_min_chars": 1,
    "lexicon_max_chars": 64,
    "lexicon_pattern": r"[0-9a-z][0-9a-z.\-]*",
}


def agreement_shape_problems(rec) -> list:
    """The EXECUTABLE closed-shape rule for an AgreementRecord under ANY
    lexicon version (0026-R8-2). Under the CURRENT version, grammar
    membership applies ON TOP of this; under a foreign version this is
    the WHOLE validation — markers are opaque within these bounds."""
    S = AGREEMENT_SHAPE
    out = []
    if type(rec) is not dict:
        return ["record is not an object"]
    unknown = sorted(set(rec) - set(S["keys"]))
    missing = sorted(set(S["keys"]) - set(rec))
    if unknown:
        out.append(f"unknown key(s) {unknown} — the record is CLOSED")
    if missing:
        out.append(f"missing key(s) {missing}")
    if out:
        return out
    m = rec["markers"]
    if type(m) is not list:
        out.append("markers is not a JSON array")
    else:
        if len(m) > S["markers_max_count"]:
            out.append(f"{len(m)} markers exceed the maximum "
                       f"{S['markers_max_count']}")
        seen = set()
        for i, tok in enumerate(m):
            if type(tok) is not str:
                out.append(f"markers[{i}] is not a string")
            elif not (S["marker_min_chars"] <= len(tok)
                      <= S["marker_max_chars"]):
                out.append(f"markers[{i}] length {len(tok)} outside "
                           f"[{S['marker_min_chars']}, "
                           f"{S['marker_max_chars']}]")
            elif tok in seen:
                out.append(f"markers[{i}] duplicates {tok!r} — REFUSE")
            else:
                seen.add(tok)
    if rec["direction"] not in S["direction_values"]:
        out.append(f"direction {rec['direction']!r} outside the closed "
                   f"set {S['direction_values']}")
    lx = rec["lexicon"]
    if type(lx) is not str or not (
            S["lexicon_min_chars"] <= len(lx) <= S["lexicon_max_chars"]):
        out.append("lexicon version is not a string within "
                   f"[{S['lexicon_min_chars']}, {S['lexicon_max_chars']}]"
                   " chars")
    elif not re.fullmatch(S["lexicon_pattern"], lx):
        out.append(f"lexicon version {lx!r} does not match the closed "
                   f"pattern")
    return out


def render_shape_block() -> str:
    """The §3d shape table, generated from AGREEMENT_SHAPE."""
    S = AGREEMENT_SHAPE
    return (
        "<!-- GENERATED:agreement-shape (import_matrix.py — the one "
        "carrier; do not hand-edit) -->\n"
        "| shape rule | value |\n|---|---|\n"
        f"| record keys (CLOSED; unknown keys REFUSE) | "
        f"`{', '.join(S['keys'])}` |\n"
        f"| markers collection | {S['markers_type']}, at most "
        f"{S['markers_max_count']} entries |\n"
        f"| marker string length | {S['marker_min_chars']}–"
        f"{S['marker_max_chars']} characters |\n"
        f"| duplicate markers | {S['markers_duplicates']} |\n"
        f"| direction (CLOSED) | `{', '.join(S['direction_values'])}` |\n"
        f"| lexicon version | {S['lexicon_min_chars']}–"
        f"{S['lexicon_max_chars']} chars matching "
        f"`{S['lexicon_pattern']}` |\n"
        "<!-- /GENERATED:agreement-shape -->")


_SHAPE_RE = re.compile(
    r"<!-- GENERATED:agreement-shape .*?/GENERATED:agreement-shape -->",
    re.S)


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
    shapes = _SHAPE_RE.findall(spec_text)
    if len(shapes) != 1 or shapes[0] != render_shape_block():
        out.append("the spec's agreement-shape block is absent or does "
                   "not byte-match import_matrix.render_shape_block() — "
                   "the executable bounds are the one carrier "
                   "(0026-R8-2)")
    return out


if __name__ == "__main__":
    import pathlib
    spec = (pathlib.Path(__file__).parents[2]
            / "0026-label-value-agreement.md")
    probs = spec_matrix_problems(spec.read_text())
    for p in probs:
        print(p)
    raise SystemExit(1 if probs else 0)
