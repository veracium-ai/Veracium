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
    # --- lex-8 (research round-2 pre-seal): comitative co-speakers and
    # the third-person self-possessive
    ("comitative_along_with",
     "the user, along with her vet, said the cat is sick", None, True),
    ("comitative_together_with",
     "the user together with the landlord said rent is due", None, True),
    ("comitative_as_well_as",
     "the user as well as the accountant said the deduction is valid",
     None, True),
    ("users_own_is_self", "the user's own note said fine", None, False),
    # --- lex-9 (external round 3, R3-1): disjunction + artifact/entity
    ("or_disjunction_restricts",
     "the user or the doctor said to rest", None, True),
    ("users_own_entity_is_third",
     "the user's own doctor said to rest", None, True),
    ("my_own_entity_is_third", "my own doctor said to rest", None, True),
    # --- lex-5 RECALL cells (research red-team, the FN direction): §6a
    # measures false positives only, so verb-list completeness IS the
    # check's recall — these held relays MUST FIRE, so completeness is
    # measured, not enumerated. The first two are research's headline.
    ("recall_claimed", "my landlord claimed I owe 500 dollars", None, True),
    ("recall_claimed_third", "the tenant claimed the deposit was returned",
     None, True),
    ("recall_warned", "the doctor warned about the interaction", None, True),
    ("recall_wrote", "my lawyer wrote that the lease is void", None, True),
    ("recall_texted", "the landlord texted that rent is due", None, True),
    ("recall_noted", "the nurse noted an allergy to penicillin", None, True),
    ("recall_explained", "the mechanic explained the brakes were worn",
     None, True),
    ("recall_insisted", "her accountant insisted the filing was correct",
     None, True),
    ("recall_alleged", "the neighbor alleged the fence is misplaced",
     None, True),
    ("recall_diagnosed", "the vet diagnosed a thyroid condition",
     None, True),
    ("recall_prescribed", "the doctor prescribed 10mg daily", None, True),
    # own-use controls: the grammar discriminates the new verbs too
    ("recall_own_claimed", "I claimed the deduction on my return",
     None, False),
    ("recall_own_noted", "user noted a preference for mornings",
     None, False),
    ("recall_own_wrote", "I wrote to the landlord about the leak",
     None, False),
)


# ---------------------------------------------------------------------------
# 0026-R2-1: the GRAMMAR-ORACLE CORPUS — generated, not hand-picked. The
# 53 hand cells stayed green while modifiers, determiner-separated
# conjuncts and Unicode possessives all misclassified, because hand cells
# cover what their author enumerated. Here the corpus is the CROSS-PRODUCT
# of construction parameters and the expected label is DERIVED from the
# constructions (any third-party head restricts; else ambiguous; else
# user), so a new attachment shape is a new generator axis, not a new
# hand cell.

_SUBJECT_HEADS = {
    # surface, head identity
    "the doctor": "third",
    "user": "user",
    "i": "user",
    "she": "ambiguous",
    "my doctor": "third",
    "the user's doctor": "third",          # ASCII possessive
    "the user\u2019s doctor": "third",     # curly possessive (normalized)
    "my own account": "user",
    "the user's own note": "user",         # third-person self-possessive
    "the user\u2019s own note": "user",    # …and its curly form
    # R3-1: artifact-vs-entity — a possessed PERSON is a third party
    # whatever the possessive; only user-authored artifacts are self
    "my own doctor": "third",
    "the user's own doctor": "third",
}
_MODIFIERS = (
    "",                                    # bare
    " treating the user",                  # participial, user inside
    " of the user",                        # prepositional, user inside
    " who examined the cat",               # relative-ish
)
_CONJUNCTS = {
    "": None,
    " and the user": "user",               # determiner-separated conjunct
    " and i": "user",
    " and the nurse": "third",
    " and she": "ambiguous",
    # COMITATIVE axis (lex-8, research round-2: quasi-coordinators were
    # the generator's gap — the oracle could not catch what it did not
    # generate)
    " along with her vet": "third",
    " together with the landlord": "third",
    " as well as the accountant": "third",
    " in addition to the nurse": "third",
    # R3-1: disjunction — a POSSIBLE third-party speaker restricts
    " or the doctor": "third",
    " or she": "ambiguous",
}
_IDENT_RANK = {"third": 0, "ambiguous": 1, "user": 2}


def _expected(heads) -> str:
    """The design rule, applied to the head set: any third-party co-source
    restricts; else any ambiguous head is ambiguous; else outbound."""
    if "third" in heads:
        return "inbound"
    if "ambiguous" in heads:
        return "ambiguous"
    return "outbound"


def grammar_oracle_cells():
    """(name, text, expected direction) for every generated construction.
    Modifiers attach to the FIRST head only (post-head material must be
    inert whatever it names); conjuncts add a second head, determiners
    and all."""
    for subj, ident in _SUBJECT_HEADS.items():
        for mi, mod in enumerate(_MODIFIERS):
            # a relative-clause modifier contains verbs in some grammars;
            # keep modifiers verb-free here so the clause bound is the
            # attribution verb itself
            for cname, cident in _CONJUNCTS.items():
                heads = [ident] + ([cident] if cident else [])
                text = f"{subj}{mod}{cname} said the diet works"
                name = (f"gen_{ident}_m{mi}_" 
                        f"{cident or 'solo'}")
                yield name, text, _expected(heads)


def grammar_oracle_problems() -> list:
    out = []
    for name, text, want in grammar_oracle_cells():
        toks = L._tokens(text)
        got = None
        for i, tok in enumerate(toks):
            if tok == "said":
                got = L._direction(toks, i)
                break
        if got != want:
            out.append(f"grammar-oracle {name}: {text!r} -> {got}, "
                       f"expected {want}")
    return out


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
    out.extend(grammar_oracle_problems())
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
