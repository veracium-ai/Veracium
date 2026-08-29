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
    # --- 0026-R1-1: the reviewer's five executed counterexamples, verbatim,
    # plus the grammar cells they generalize to (lex-3's load-bearing rules:
    # post-verbal agent governs; passive recipient is inert; embedded
    # clauses classify independently; ambiguous pronouns restrict) --------
    ("passive_recipient_first_person",
     "I was told by my doctor to rest", None, True),
    ("passive_recipient_user",
     "user was told by the vet to fast the cat", None, True),
    ("reduced_passive_user_agent", "price stated by user", None, False),
    ("reduced_passive_third_agent", "price stated by the vendor", None, True),
    ("embedded_clause_inner_inbound",
     "user said their doctor confirmed the dosage", None, True),
    ("ambiguous_pronoun_restricts",
     "she said the user needs medication", None, True, "ambiguous"),
    ("ambiguous_object_pronoun",
     "I was told by her to rest", None, True, "ambiguous"),
    ("passive_unnamed_source", "I was told to rest", None, True),
    ("agent_governs_over_recipient",
     "the client was told by user to pay", None, False),
    ("adverb_between_subject_and_verb",
     "user also said no allergies", None, False),
    # --- lex-4 (pre-emptive, research's named shapes): coordination and
    # nesting — both error directions of the new rules are over-restriction
    ("coordinated_user_subject",
     "the vet and I said the diet works", None, True),
    ("coordinated_user_subject_2",
     "my wife and I said it was fine", None, True),
    ("vp_coordination_elided_third",
     "the vet examined the cat and said no allergies", None, True),
    ("vp_coordination_elided_user",
     "user visited the clinic and said no allergies", None, False),
    ("nested_relay", "my sister said the vet said it is fine", None, True),
    ("nested_user_outer", "I said the vet said it is fine", None, True),
    ("dropped_subject_fragment", "said it was fine", None, False),
)


def problems() -> list:
    out = []
    for cell in CELLS:
        name, note, obj, want = cell[:4]
        # optional 5th element: the CLASS the restriction must come from.
        # 0026-R1-1: ambiguous-vs-inbound is invisible at the match-bool
        # surface (both restrict), so the ambiguity cells assert the
        # counted split — otherwise dropping the ambiguous class entirely
        # is a behaviour-preserving mutation at this surface while §6a's
        # measurement silently loses its ambiguity count.
        want_class = cell[4] if len(cell) > 4 else None
        try:
            r = L.scan(note, obj)
            got = bool(r["inbound"] | r["ambiguous"])
        except Exception as exc:                       # totality is a claim
            out.append(f"{name}: RAISED {type(exc).__name__}: {exc}")
            continue
        if got != want:
            out.append(f"{name}: matched={got}, expected {want} "
                       f"(in={sorted(r['inbound'] | r['ambiguous'])})")
        if want_class and not r[want_class]:
            out.append(f"{name}: the restriction must come from the "
                       f"{want_class!r} class and that set is empty "
                       f"(scan={ {k: sorted(v) for k, v in r.items()} })")
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
