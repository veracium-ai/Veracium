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
"""
from __future__ import annotations

import re

LEXICON_VERSION = "0026-lex-2"

# Attribution VERBS — §3a's named class and nothing wider.
_VERBS = (
    "said", "says", "told", "tells", "stated", "states",
    "mentioned", "mentions", "reported", "reports",
    "confirmed", "confirms", "informed", "informs",
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

# The user as the extractor names them in the THIRD person.
_USER_SUBJ = ("user", "they", "he", "she")

_FIRST_PERSON = _FIRST_PERSON_SUBJ + _FIRST_PERSON_OBJ + _FIRST_PERSON_SELF

_WORD = re.compile(r"[a-z']+")


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
    return _WORD.findall(text.lower())


def _direction(tokens: list, idx: int, lookback: int = 4) -> str:
    """'inbound' | 'outbound' | 'none' for the verb at `tokens[idx]`."""
    if idx == 0:
        # No subject at all: "recommended brand", "confirmed no allergies".
        # A participle opening the note attributes nothing to anyone.
        return "none"
    start = max(0, idx - lookback)
    for j in range(idx - 1, start - 1, -1):
        if tokens[j] in _FIRST_PERSON_SUBJ:
            return "outbound"
        if tokens[j] in _USER_SUBJ:
            return "outbound"            # the user, narrated in third person
        if tokens[j] in ("my", "our") and j + 1 < len(tokens) \
                and tokens[j + 1] in _FIRST_PERSON_SELF:
            return "outbound"            # "my own account said…"
    return "inbound"


def scan(note, object_text) -> dict:
    """The inbound markers, and the outbound ones SUPPRESSED.

    The suppressed set is what makes §6a measurable: it is exactly the
    population the directional rule saves, counted rather than asserted.
    """
    inbound, outbound = set(), set()
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
                first_person_source = bool(tail) and (
                    tail[0] in _FIRST_PERSON_OBJ
                    or tail[0] in _FIRST_PERSON_SUBJ
                    or tail[0] in _USER_SUBJ
                    or (tail[0] in ("my", "our") and len(tail) > 1
                        and tail[1] in _FIRST_PERSON_SELF))
                if first_person_source:
                    outbound.add(phrase)
                else:
                    inbound.add(phrase)  # "according to my doctor" — the
                                         # possessive attaches to a THIRD
                                         # PARTY, not to the speaker
    return {"inbound": frozenset(inbound), "outbound": frozenset(outbound)}


def relay_markers(note, object_text) -> frozenset:
    """§3a's named entry point: the INBOUND markers only."""
    return scan(note, object_text)["inbound"]
