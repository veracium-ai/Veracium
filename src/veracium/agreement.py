"""specs/0026 — the relay-marker detector (ACCEPTED 2026-08-30).

THE one code-owned lexicon surface (V4: not host-configurable; exactly
one definition site in the product). The grammar, tables and history
live in the accepted reference artifact
`specs/evidence/0026/relay_lexicon.py` (lex-1 through lex-10, twelve
external review rounds); this module is that artifact graduated into
`src/`, and a standing test binds the two — tables, version and
observed behavior — so they cannot drift.

The detector is PURE and total over (None/empty/any-str)^2: no LLM
call, no network, no host input (V1). `scan(note, object_text)`
returns the inbound/outbound/ambiguous marker sets;
`relay_markers(note, object_text)` is the restricting union
(inbound | ambiguous) — the §3b floor evidence. Direction is a
GRAMMAR: the agent governs, passive recipients are inert, clauses
classify independently, ambiguous pronouns restrict with a counted
conservative outcome, and outbound (the user as source) never
matches. Grammar membership is VERSION-SCOPED (0026-R7-1): this
module defines the CURRENT lexicon; foreign-version stored records
validate as opaque closed shapes only.
"""
from __future__ import annotations

import re

LEXICON_VERSION = "0026-lex-10"

# The READING domain — every value _direction can return (0026-I12,
# research's round-9 pre-seal: this domain and the STORED direction
# enum were two independent definitions bridged only by a prose
# comment, which is exactly how R9-1 split; import_matrix binds the
# two through an executable mapping whose keys must equal this tuple).
LEXICON_DIRECTIONS = ("inbound", "outbound", "ambiguous", "none")

# Attribution VERBS — §3a's named class. lex-5 (research red-team,
# FN direction): the list omitted high-frequency attribution verbs —
# `claimed` above all, the name of the very relation 0024 quarantines —
# and §6a measured only false positives, so list completeness WAS the
# check's recall and it was unmeasured. The additions are membership,
# not logic: the direction grammar already discriminates their
# first-person/user uses ("I claimed the deduction" is outbound by the
# same scan). Professional-judgment ruling (stated, not implied):
# diagnosed/prescribed ARE attribution — they attribute a professional's
# factual claim, which is exactly the B02/B07 laundering class — and are
# IN. The advice class (advised/recommended/suggested) stays OUT: it
# attributes a recommendation, not a fact ("doctor advised rest"
# asserted as fact is first-order true as an event), and it was 79% of
# lex-1's measured false fires. Every addition is priced by the §6a
# re-measurement and covered by the recall cells in the matrix.
_VERBS = (
    "said", "says", "told", "tells", "stated", "states",
    "mentioned", "mentions", "reported", "reports",
    "confirmed", "confirms", "informed", "informs",
    "claimed", "claims", "warned", "warns", "wrote", "writes",
    "texted", "texts", "emailed", "noted",
    "replied", "replies", "explained", "explains",
    "insisted", "insists", "acknowledged", "acknowledges",
    "argued", "argues", "testified", "testifies",
    "alleged", "alleges", "diagnosed", "diagnoses",
    "prescribed", "prescribes",
    # DROPPED after reading the lex-5 fires (the §6a discipline, again at
    # the homograph rung): "notes" (207 fires, every sampled one the
    # NOUN — "taking notes"), "added"/"adds" (81+37, "adds flavor",
    # "added to cart" — the non-attributive verb sense dominates), and
    # "emails" (48, "checking emails"). Their unambiguous past/inflected
    # attribution forms (noted, emailed) STAY, so the relays research
    # named still fire; the nominal homographs do not.
)

# Source-naming PHRASES: an attribution frame whose object is the source.
_PHRASES = (
    "according to", "confirmed by", "as stated by",
    "as reported by", "as told by", "on the advice of",
    "in the words of", "quoting",
)

# "per" is in §3a's list as "per <entity>", but bare `per` is overwhelmingly a
# RATE here ("per week", "$5 per month"), so it is a frame with a unit
# exclusion rather than a plain phrase.
_PER_UNITS = frozenset((
    "week", "weeks", "day", "days", "month", "months", "year", "years",
    "hour", "hours", "minute", "minutes", "second", "seconds",
    "night", "nights", "session", "sessions", "serving", "servings",
    "person", "people", "unit", "units", "item", "items", "mile", "miles",
    "km", "kg", "lb", "lbs", "gram", "grams", "litre", "liter", "cup",
    "cups", "time", "times", "use", "visit", "visits", "class", "classes",
    "meal", "meals", "load", "loads", "page", "pages", "episode", "episodes",
    "capita", "diem", "annum", "cent", "share", "gallon", "gallons",
))

# FIRST-PERSON reference, split by GRAMMATICAL ROLE — the roles behave
# oppositely and conflating them was this file's first defect. "my doctor
# said…" is INBOUND: `my` is a possessive on a third party and the subject of
# `said` is the doctor.
_FIRST_PERSON_SUBJ = ("i", "we")
_FIRST_PERSON_OBJ = ("me", "us", "myself", "ourselves")
_FIRST_PERSON_SELF = ("own",)

# The user as the extractor names them in the THIRD person. he/she/they
# are NOT here: a pronoun's referent is not resolvable from a single
# note, and silently assuming it is the user was 0026-R1-1's fifth
# counterexample. They are their own class with a conservative outcome.
_USER_SUBJ = ("user",)
_AMBIG_PRON = ("he", "she", "they")

# Passive auxiliaries — "was told", "got told", "is stated".
_BE_FORMS = ("is", "are", "was", "were", "be", "been", "being", "am",
             "get", "gets", "got", "getting")

# Tokens that END a clause for the backward subject scan: another
# attribution verb ("user said their doctor confirmed" — `confirmed`'s
# subject scan must not cross `said`), or a complementizer/conjunction.
# who/whom/which are NOT here (lex-7, found by the grammar oracle):
# they are post-nominal relative pronouns — MODIFIER-openers, not clause
# breakers — and breaking on them orphaned the subject head before them
# ("my own account who examined the cat said…" lost `account`). The
# forward head parse ignores post-head material, so the relative clause
# is inert by construction. `that` stays: after an attribution verb it
# is a complementizer, and the verb itself already breaks.
_CLAUSE_BREAK = frozenset((
    "that", "because",
    "when", "while", "after", "before", "since", "if",
    "although", "though", "unless", "until",
))

# Coordinators are TRANSPARENT to the subject scan (lex-4): a VP
# coordination shares its subject ("the vet examined the cat and said…"),
# so breaking at `and` attributed an elided third-party subject to
# nobody — the unsafe direction.
# "or" is a coordinator too (external round 3, R3-1): "the user or the
# doctor said…" names a POSSIBLE third-party speaker, and possibility
# restricts in a restrict-only design.
_COORD = frozenset(("and", "but", "so", "then", "plus", "or"))

# The self-possessive covers user-authored ARTIFACTS, not possessed
# third-party ENTITIES (external round 3, R3-1): "my own note said…" is
# the user's own word; "my own doctor said…" is the doctor's. A closed
# artifact set makes the distinction decidable; anything outside it is
# a possessed head and classifies third.
# COMITATIVE quasi-coordinators (lex-8, research round-2 pre-seal): a
# prepositional co-speaker phrase — "the user, along with her vet,
# said…" — introduces a third-party CO-SOURCE exactly like "and", but
# lexical coordinators cannot see it, so three genuine relays were
# silently unrestricted (the round-1 co-source class, one syntactic
# layer up). Matched as token sequences inside the clause; each match
# reopens head-expectation like a coordinator.
_COMITATIVE = (
    ("along", "with"), ("together", "with"), ("as", "well", "as"),
    ("in", "addition", "to"), ("accompanied", "by"),
)

# Skipped while scanning for a subject head (never a subject themselves).
_SKIP_TOKENS = frozenset((
    "the", "a", "an", "not", "never", "also", "just", "only", "already",
    "recently", "always", "again", "as",
))

# Words that cannot be the HEAD a possessive points at — a bare "her"/
# "his"/"their" followed by one of these (or by nothing) is an OBJECT
# pronoun, not a possessive: "told by her to rest" (0026 round-1's
# ambiguous-object cell, re-broken by the lex-7 possessive branch and
# restored here).
_NON_HEADS = frozenset((
    "to", "of", "that", "for", "on", "in", "at", "with", "about",
    "and", "or", "but",
))

_FIRST_PERSON = _FIRST_PERSON_SUBJ + _FIRST_PERSON_OBJ + _FIRST_PERSON_SELF

_WORD = re.compile(r"[a-z']+")

# 0026-R2-1: the curly apostrophe (U+2019, and the modifier letter
# U+02BC) tokenized "user's" as user/s/doctor-adjacent fragments, so a
# Unicode possessive defeated every possessive rule. Normalized BEFORE
# tokenization; the ASCII possessive stays one token.
_APOSTROPHES = str.maketrans({"\u2019": "'", "\u02bc": "'", "\u2018": "'"})


class LexiconError(RuntimeError):
    """The lexicon is empty or malformed — refuse at LOAD, never at use."""


def _validate_lexicon() -> None:
    """V4: refuse a vacuous or malformed lexicon at import time."""
    for name, table in (("verbs", _VERBS), ("phrases", _PHRASES),
                        ("first_person", _FIRST_PERSON),
                        ("user_subj", _USER_SUBJ), ("per_units", _PER_UNITS)):
        if not table:
            raise LexiconError(f"the {name} table is EMPTY — a lexicon that "
                               f"matches nothing passes everything")
        for entry in table:
            if not isinstance(entry, str) or not entry.strip():
                raise LexiconError(f"malformed {name} entry {entry!r}")
            if entry != entry.lower():
                raise LexiconError(f"{name} entry {entry!r} is not lowercased "
                                   f"— the scan lowercases its input, so this "
                                   f"entry could never match")


_validate_lexicon()


def _tokens(text: str) -> list:
    return _WORD.findall(text.lower().translate(_APOSTROPHES))


_DETERMINERS = frozenset(("the", "a", "an", "this", "that", "these",
                          "those"))
_POSSESSIVES = frozenset(("my", "our", "their", "his", "her", "its"))


def _is_possessive(tok: str) -> bool:
    """A possessive marker: the closed pronoun set, or any token carrying
    an apostrophe-s / trailing-apostrophe possessive ("user's",
    "doctors'"). The HEAD follows a possessive, and a possessed head is a
    THIRD PARTY whoever the possessor is ("the user's doctor" is the
    doctor)."""
    return (tok in _POSSESSIVES or tok.endswith("'s")
            or (tok.endswith("'") and len(tok) > 1))


def _classify_source(head_tokens: list) -> str:
    """Who a resolved source phrase names: 'user' | 'ambiguous' | 'third'.
    `head_tokens` starts at the source phrase (determiners not yet
    skipped). Possessives are attachment markers: the HEAD follows them,
    and a possessed head is a third party whoever possesses it —
    "the user's doctor" names the doctor (0026-R2-1's Unicode-possessive
    counterexample, normalized upstream)."""
    toks = [t for t in head_tokens if t not in _DETERMINERS
            and t not in _SKIP_TOKENS]
    if not toks:
        return "third"                   # unnamed — conservative
    h = toks[0]
    if _is_possessive(h):
        # R4-1: no artifact carve-out — "by my own record" restricts,
        # because ownership is not authorship (the record's producer may
        # be a doctor or a bank); "by my own doctor" restricts (R3-1).
        # Every possessed head is a third-party source.
        if h in ("her", "his", "their", "its") \
                and (len(toks) == 1 or toks[1] in _NON_HEADS):
            return "ambiguous"           # bare object pronoun: "by her"
        return "third"                   # possessed head: user's doctor,
                                         # my doctor, their vet
    if h in _FIRST_PERSON_SUBJ or h in _FIRST_PERSON_OBJ \
            or h in _USER_SUBJ:
        return "user"
    if h in _AMBIG_PRON or h in ("him", "her", "them"):
        return "ambiguous"
    return "third"


def _agent_after(tokens: list, idx: int):
    """The `by <agent>` phrase following the verb, or None.

    0026-R1-1: the post-verbal agent GOVERNS direction when present —
    "told by my doctor" (passive) and "price stated by user" (reduced
    passive) are both classified by their agent, whatever precedes the
    verb."""
    j = idx + 1
    while j < len(tokens) and tokens[j] in _SKIP_TOKENS:
        j += 1
    if j < len(tokens) and tokens[j] == "by":
        head = [t for t in tokens[j + 1:j + 4]
                if t not in ("the", "a", "an")]
        return _classify_source(head)
    return None


def _direction(tokens: list, idx: int, max_scan: int = 24) -> str:
    """'inbound' | 'outbound' | 'ambiguous' | 'none' for tokens[idx].

    The directional GRAMMAR (lex-3, 0026-R1-1) — proximity is not
    authorship:

    1. A post-verbal `by <agent>` phrase governs: agent user/first-person
       -> outbound; agent third-party -> inbound; agent pronoun ->
       ambiguous. Covers passive ("I was told by my doctor") and reduced
       passive ("price stated by user") alike.
    2. Otherwise, a passive auxiliary before the verb means the preceding
       noun is the RECIPIENT, not the speaker: the source is unnamed ->
       conservatively inbound ("I was told..." is a relay from an
       unstated source).
    3. Otherwise the ACTIVE subject is resolved by scanning backward
       INSIDE the clause -- the scan stops at another attribution verb or
       a complementizer, so an embedded clause's verb never inherits the
       outer subject ("user said their doctor confirmed..." classifies
       `said` outbound and `confirmed` inbound).
    4. he/she/they are AMBIGUOUS -- never silently the user. The caller
       treats ambiguous as restrict (the conservative outcome in a
       restrict-only design) and counts it separately.
    5. No subject at all is 'none': a bare participle attributes nothing.
    """
    agent = _agent_after(tokens, idx)
    if agent is not None:
        return {"user": "outbound", "ambiguous": "ambiguous",
                "third": "inbound"}[agent]
    if idx == 0:
        return "none"
    # passive with no agent: recipient precedes, source unnamed
    j = idx - 1
    while j >= 0 and tokens[j] in _SKIP_TOKENS:
        j -= 1
    if j >= 0 and tokens[j] in _BE_FORMS:
        return "inbound"
    # ACTIVE: the subject by HEAD CONSTRUCTION (lex-7, 0026-R2-1 — the
    # backward nearest-token scan read a modifier's object as the
    # subject: "the doctor treating the user said" resolved `user`).
    # The clause is bounded backward by a breaker (another attribution
    # verb, an auxiliary, a complementizer); then it is read FORWARD:
    # the first noun after any determiners/possessives is the subject
    # HEAD (post-head material up to the verb is modifier and is
    # IGNORED, whatever identities it contains), and each coordinator
    # introduces one more co-head, determiners and all ("the doctor and
    # the user said" — R2-1's second counterexample). Resolution over
    # the head SET: any third-party head restricts (co-source governs);
    # else any ambiguous head is ambiguous; else all-user is outbound.
    start = max(0, idx - max_scan)
    cstart = start
    for j in range(idx - 1, start - 1, -1):
        tok = tokens[j]
        if tok in _CLAUSE_BREAK or tok in _VERBS or tok in _BE_FORMS:
            cstart = j + 1
            break
    clause = tokens[cstart:idx]
    heads = []
    expecting_head = True
    saw_self_poss = False
    k = 0
    while k < len(clause):
        tok = clause[k]
        matched_com = None
        for pat in _COMITATIVE:
            if tuple(clause[k:k + len(pat)]) == pat:
                matched_com = pat
                break
        if matched_com:
            expecting_head = True        # a comitative phrase introduces
            saw_self_poss = False        # a CO-SPEAKER (lex-8)
            k += len(matched_com)
            continue
        k += 1
        if tok in _DETERMINERS or tok in _SKIP_TOKENS:
            continue
        if tok in _COORD:
            expecting_head = True        # a coordinator opens a new
            saw_self_poss = False        # conjunct, determiners and all
            continue
        if not expecting_head:
            continue                     # post-head modifier material —
                                         # ignored, whoever it names
        if _is_possessive(tok):
            nxt = clause[k] if k < len(clause) else ""
            if tok in ("my", "our", "user's", "users'") \
                    and nxt in _FIRST_PERSON_SELF:
                # "my own X" AND "the user's own X" are the user's own —
                # the extractor narrates the user in the third person
                # (lex-8, research: the self rule covered first person
                # only, so "the user's own note" over-restricted)
                saw_self_poss = True
                continue
            heads.append("third")        # possessed head: my/their/
            expecting_head = False       # user's <noun>
            continue
        if tok in _FIRST_PERSON_SELF and saw_self_poss:
            continue                     # the "own" of "my own"
        if tok in _FIRST_PERSON_SUBJ or tok in _USER_SUBJ:
            heads.append("user")
            expecting_head = False
            continue
        if tok in _AMBIG_PRON or tok in ("him", "her", "them"):
            heads.append("ambiguous")
            expecting_head = False
            continue
        heads.append("third")            # a possessed head restricts,
        expecting_head = False           # artifacts included: "my own
        saw_self_poss = False            # record" may be doctor-authored
                                         # (R4-1 — ownership != authorship)
    if not heads:
        return "none"                    # clause opens with no subject
    if "third" in heads:
        return "inbound"                 # a third-party (co-)source
    if "ambiguous" in heads:
        return "ambiguous"
    return "outbound"


def scan(note, object_text) -> dict:
    """The inbound markers, and the outbound ones SUPPRESSED.

    The suppressed set is what makes §6a measurable: it is exactly the
    population the directional rule saves, counted rather than asserted.
    """
    inbound, outbound, ambiguous = set(), set(), set()
    for field in (note, object_text):
        if not isinstance(field, str) or not field.strip():
            continue                     # total over None/empty by contract
        low = field.lower()
        toks = _tokens(field)

        for i, tok in enumerate(toks):
            if tok in _VERBS:
                d = _direction(toks, i)
                if d == "inbound":
                    inbound.add(tok)
                elif d == "outbound":
                    outbound.add(tok)
                elif d == "ambiguous":
                    ambiguous.add(tok)
            elif tok == "per" and i + 1 < len(toks):
                if toks[i + 1] not in _PER_UNITS:
                    inbound.add("per")   # "per the vet", "per Dr Adeyemi"

        for phrase in _PHRASES:
            for m in re.finditer(r"\b" + re.escape(phrase) + r"\b", low):
                tail = _tokens(low[m.end():m.end() + 40])
                # skip a leading determiner: "according to THE user" names
                # the same source as "according to me", and the article was
                # hiding it from this check
                while tail and tail[0] in ("the", "a", "an"):
                    tail = tail[1:]
                src = _classify_source(tail)
                if src == "user":
                    outbound.add(phrase)
                elif src == "ambiguous":
                    ambiguous.add(phrase)   # "according to her" — the
                                            # referent is not resolvable
                else:
                    inbound.add(phrase)  # "according to my doctor" — the
                                         # possessive attaches to a THIRD
                                         # PARTY, not to the speaker
    return {"inbound": frozenset(inbound), "outbound": frozenset(outbound),
            "ambiguous": frozenset(ambiguous)}


def relay_markers(note, object_text) -> frozenset:
    """§3a's named entry point: the markers that RESTRICT.

    Inbound markers restrict by design; AMBIGUOUS markers restrict as the
    explicit conservative outcome (0026-R1-1: an unresolvable referent
    must not be silently assumed to be the user, and in a restrict-only
    design over-restriction is the safe failure — bounded by §6a's
    false-positive bar and counted separately in the measurement)."""
    r = scan(note, object_text)
    return r["inbound"] | r["ambiguous"]


def derive_record(note, object_text, disclosure):
    """specs/0026 §3b/§3c — THE one derivation of an AgreementRecord
    from a record's note/object and its (final) disclosure. Used by
    ingest at establishment AND by default-mode import recomputation,
    so the two boundaries cannot drift (the R4-2/R9-1 one-carrier
    lesson). Returns an AgreementRecord or None; NEVER touches
    disclosure itself — the caller owns the restrict-only floor.

    - a RESTRICTING match (inbound or ambiguous) -> a record with
      direction "inbound" (or "ambiguous" when only that class fired);
    - an OUTBOUND (user-as-source) reading on a record whose final
      disclosure is QUARANTINED -> §3c's demotion-direction
      DISAGREEMENT, direction "user_source", no disposition change;
    - no markers -> None (V2: absence of a marker is absence of
      evidence).

    Markers are sorted and capped at the closed shape's bound of 8
    (measured max over the corpus is 2; the cap is deterministic
    overflow protection, never expected to bite)."""
    from .schema import AgreementRecord, Disclosure
    res = scan(note, object_text)
    restrict = res["inbound"] | res["ambiguous"]
    if restrict:
        return AgreementRecord(
            markers=sorted(restrict)[:8],
            direction=("inbound" if res["inbound"] else "ambiguous"),
            lexicon=LEXICON_VERSION)
    if res["outbound"] and disclosure == Disclosure.QUARANTINED:
        return AgreementRecord(
            markers=sorted(res["outbound"])[:8],
            direction="user_source",
            lexicon=LEXICON_VERSION)
    return None

