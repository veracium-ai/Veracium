#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0026_relay_lexicon.py::test_relay_lexicon_mutation_matrix
"""0026 §3a — the lexicon's adversarial cell matrix, runnable and offline.

WHY THIS EXISTS BEFORE THE LEXICON SHIPS. Seven consecutive external rounds
on another line were one evidence script being mutation-tested at one mutant
per round — comment-shadow, anchored-comment, table-membership, delimiter,
fence-grammar — a standard parser-hardening ladder climbed at a full seal
cycle per rung. A marker lexicon is the same shape of artifact. So the
matrix is written now, with the mutants the reviewer would reach for.

TWO OF THESE CELLS ARE NOT HYPOTHETICAL. `possessive_third_party` and
`user_third_person` both FAILED in lex-1 and were found by running the
matrix and by reading real fires — the first would have suppressed the most
common relay shape in the corpus, the second read the user's own word as a
relay. Both are the FAVOURABLE-looking direction of error, which is the
direction that survives review.

Run:  $PY specs/evidence/0026/validate_lexicon.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import relay_lexicon as L                                   # noqa: E402

# (cell name, note, object, expect_match)
CELLS = (
    # --- inbound: a third party is the source -----------------------------
    ("possessive_third_party", "my doctor said the levels were fine", None, True),
    ("inbound_phrase", "according to the vet, she needs a diet", None, True),
    ("inbound_frame", "as stated by the vet", None, True),
    ("inbound_first_person_object", "the vet told me to switch food", None, True),
    ("per_entity", "per Dr Adeyemi, the dose is fine", None, True),
    ("inbound_in_object_field", None, "as reported by the clinic", True),
    ("mixed_inbound_survives",
     "I told my doctor that the vet said she is fine", None, True),
    # --- outbound: the USER is the source ---------------------------------
    ("outbound_first_person", "I told my doctor about the pain", None, False),
    ("outbound_frame", "as I said to the vet last week", None, False),
    ("user_third_person", "user confirmed no dietary restrictions", None, False),
    ("user_named_in_frame", "according to the user, it is fine", None, False),
    ("outbound_phrase_me", "according to me, it is fine", None, False),
    ("own_words", "in my own words, I run daily", None, False),
    # --- no attribution at all --------------------------------------------
    ("participle_no_subject", "recommended brand", None, False),
    ("participle_no_subject_2", "confirmed no allergies", None, False),
    ("per_unit_rate", "3 sessions per week", None, False),
    ("per_unit_currency", "billed $5 per month", None, False),
    ("no_marker", "I run every morning", None, False),
    # --- totality over the field domain -----------------------------------
    ("both_none", None, None, False),
    ("both_empty", "", "", False),
    ("whitespace_only", "   ", "\t\n", False),
    ("uppercase_input", "MY DOCTOR SAID THE LEVELS WERE FINE", None, True),
)


def problems() -> list:
    out = []
    for name, note, obj, want in CELLS:
        try:
            got = bool(L.relay_markers(note, obj))
        except Exception as exc:                       # totality is a claim
            out.append(f"{name}: RAISED {type(exc).__name__}: {exc}")
            continue
        if got != want:
            out.append(f"{name}: matched={got}, expected {want} "
                       f"(in={sorted(L.relay_markers(note, obj))})")
    # V4: a vacuous lexicon must refuse at LOAD, not pass everything
    if not (L._VERBS and L._PHRASES and L._USER_SUBJ):
        out.append("a lexicon table is empty and load did not refuse")
    return out


def main() -> int:
    bad = problems()
    if bad:
        print("relay lexicon matrix FAILED:\n  " + "\n  ".join(bad),
              file=sys.stderr)
        return 1
    print(f"relay lexicon {L.LEXICON_VERSION}: {len(CELLS)} cells, all agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
