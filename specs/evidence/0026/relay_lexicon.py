"""0026 §3a — the closed marker lexicon and `relay_markers`, as EVIDENCE.

WHY THIS LIVES UNDER specs/evidence/ AND NOT IN src/. 0026 is a draft. Only
an accepted spec authorises implementation, and §6a's false-positive
measurement is an ACCEPTANCE PRECONDITION — it has to run before the thing
it gates can ship. So the detector exists here first, exactly as 0025's
census script does, and graduates to `src/` at acceptance.

AT ACCEPTANCE, DELETE OR REDIRECT THIS FILE. V4 requires the lexicon to have
exactly ONE definition site; the moment a product copy exists this becomes a
second copy of a trust-bearing table, which is the drift 0026 is about.

The design §3a fixes:

* PURE and TOTAL over (None | "" | any str)². Consumes the same canonical
  strings the write path stores, and makes no LLM call — the checker must not
  ask the component under suspicion to audit itself.
* CLOSED and VERSIONED; an empty or malformed lexicon REFUSES AT LOAD, since
  a vacuous checker that passes everything is the presumed-faking target.
* DIRECTIONAL. Inbound attribution matches; the user's own speech never does.

MEASURED HISTORY OF THIS FILE (§6a's pre-commitment, honoured):

  lex-1  fired on 8.20% of grounded first-person triples against a 2% bar.
         Two causes, both found by looking at the fires rather than at the
         rate. (a) It carried the ADVICE class — recommended / suggested /
         advised — which produced 4,445 of 5,618 fires (79%) on phrases like
         "recommended brand": recommending attributes nothing to a source.
         (b) Its directional rule was written in §3a's first-person grammar
         ("I told my doctor"), and THIS EXTRACTOR NARRATES THE USER IN THE
         THIRD PERSON ("user confirmed no dietary restrictions"). The
         first-person form suppressed exactly 0 of 68,479 triples while the
         third-person form was read as INBOUND — the user's own word treated
         as a relay, which is the precise failure the bar exists to prevent.
  lex-2  narrowed to §3a's named attribution class; a bare participle with no
         subject attributes nothing; the user as third-person subject is
         OUTBOUND; `per` requires an entity rather than a unit.
  lex-3  (external round 1, 0026-R1-1) the directional rule was a 4-token
         PROXIMITY scan and proximity is not authorship: "I was told by my
         doctor" read outbound (the passive recipient mistaken for the
         speaker), "price stated by user" read inbound (the post-verbal
         agent never consulted), "user said their doctor confirmed…" read
         both verbs outbound (no clause boundary), and she/he/they were
         silently assumed to be the user. lex-3 is a directional GRAMMAR:
         a post-verbal `by <agent>` phrase governs when present (passive
         and reduced-passive), the active subject is resolved inside its
         own clause (attribution verbs and complementizers bound the
         scan), ambiguous pronouns are their own class with an explicit
         conservative outcome (restrict — over-restriction is the safe
         direction in a restrict-only design, and it is COUNTED), and an
         unnamed passive source is conservatively inbound.
  lex-4  (pre-emptive hardening for research's red-team pass, same day)
         two coordination shapes still misclassified in the UNSAFE
         direction: "the vet and I said…" resolved the nearest subject
         (I) and suppressed the third-party co-source, and "the vet
         examined the cat and said…" hit the `and` clause-breaker and
         attributed nothing — an elided third-party subject across a
         VP coordination. Coordinators (and/but/so/then) are now
         TRANSPARENT to the subject scan (VP coordination shares its
         subject; the nearest noun across the coordinator is the safe
         inbound direction), and a user-class subject immediately
         preceded by a coordinator keeps scanning for the co-source
         ("my wife and I said" restricts; "user visited the clinic and
         said" does not — the user-class subject there is not
         coordinator-adjacent). Both error directions of the new rules
         are over-restriction, the safe side, priced by re-measurement.
  lex-5/6 (research red-team, FN direction) the verb classes joined and
         the nominal homographs were narrowed by reading the fires; see
         §3a and FP-MEASUREMENT.md.
  lex-7  (external round 2, 0026-R2-1) the subject is resolved by HEAD
         CONSTRUCTION, not nearest token: the clause is read FORWARD,
         the first noun after determiners/possessives is the head,
         post-head material is inert modifier whatever it names ("the
         doctor treating the user said" no longer reads `user`),
         coordinators introduce co-heads determiners and all ("the
         doctor and the user said" restricts), Unicode apostrophes are
         normalized before tokenization (the curly-possessive "user's
         doctor" is a possessed third-party head), and relative
         pronouns are modifier-openers rather than clause breakers
         (found by the generated grammar oracle). Resolution over the
         head SET: any third-party head restricts; else ambiguous;
         else outbound.
  lex-8  (research round-2 pre-seal) COMITATIVE quasi-coordinators join
         the co-source scan ("the user, along with her vet, said…" —
         three genuine relays were silently unrestricted; the round-1
         co-source class one syntactic layer up, and exactly the
         generator-axis gap: the oracle could not catch what it did not
         generate — the axis is generated now); and the self-possessive
         rule covers third-person narration ("the user's own note" is
         the user's own, like "my own"). Measured identical to lex-7 on
         this corpus (439 = 0.64%): comitatives do not occur in the
         own-use population.
  lex-9  (external round 3, R3-1) `or` joins the coordinators (a
         POSSIBLE third-party speaker restricts), and the
         self-possessive rule is split ARTIFACT-vs-ENTITY: a closed
         artifact set (note, account, words, message…) keeps "my own
         note said…" outbound, while "my own doctor said…" — a
         possessed third-party PERSON — restricts, in both the subject
         scan and the agent/frame path. Measured identical again: the
         shapes are absent from the own-use population.
  lex-10 (external round 4, R4-1) the ARTIFACT carve-out is REMOVED —
         OWNERSHIP IS NOT AUTHORSHIP. lex-9 read every noun in a closed
         artifact set as user-authored, but a record, account or entry
         the user OWNS can be produced by a doctor, bank or other third
         party ("my own record reported a diagnosis of cancer" was
         outbound: laundering, the FN direction the spec exists to
         close). No noun class carries an authorship inference now: a
         possessed head restricts whoever possesses it, artifacts
         included. "My own notes say…" over-restricts — priced,
         counted, reversible; the laundering direction is not.
"""
from __future__ import annotations

import re

LEXICON_VERSION = "0026-lex-10"

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
