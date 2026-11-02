"""specs/0051 §4b — the speaker-turn backstop, PRODUCT code (not the frozen predicate: research's 0051 v0.2 H4 read).
A triple restricted here has no value in any user text, so ATTEST-6 over the user text cannot attest it; this module's
only independent effect is the triple's disclosure. Turns come from the frozen grammar (`attest_turns.turns`).

A triple is restricted when EVERY non-`user` side of it occurs in some non-user turn and in no user text, each side
matched as a token sequence on word boundaries after these normalisations, and only these: case-fold; a `kind:`
prefix dropped from the side; `_` and `-` read as spaces; ATTEST-3's own object normalisation; tokens are runs of
letters and digits, so an apostrophe splits ("Daniel's" holds "daniel"); and each token compared by a plural stem
("seats" ~ "seat", "boxes" ~ "box", never "glass" ~ "glas").

One class is judged otherwise: the user's dated obligation (relation `deadline`, subject `user` or the obligation named
for itself, schema.is_obligation). Its one side is its DATE, judged by 0045's resolution (grounding.ungrounded) over
the user text and over the non-user text, because the extractor writes the date ISO whatever words were said: it is
restricted when the non-user text grounds the date and no user text does (the 0.29.0 release blocker B1)."""
from __future__ import annotations

import re

from . import attest_v3, grounding
from .attest_turns import turns
from .schema import OBLIGATION_RELATION, is_obligation

_KIND = re.compile(r"^[a-z][a-z_]*:")
_TOKEN = re.compile(r"[a-z0-9]+")


def _stem(tok: str) -> str:
    if len(tok) > 4 and tok.endswith("es") and tok[-3] in "sxz":
        return tok[:-2]
    if len(tok) > 5 and tok.endswith(("ches", "shes")):
        return tok[:-2]
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def _tokens(s: str) -> list:
    return [_stem(t) for t in _TOKEN.findall(attest_v3._norm_object(s.lower().replace("_", " ").replace("-", " ")))]


def _side(s: str) -> list:
    return _tokens(_KIND.sub("", s.strip().lower()))


def _occurs(value: list, toks: list) -> bool:
    n = len(value)
    return n > 0 and any(toks[i:i + n] == value for i in range(len(toks) - n + 1))


def _date_restricts(obj: str, raw_turns: list, session_date: str) -> bool:
    """The user's dated obligation (0003 §4c-v), judged on its DATE by 0045's own resolution, per side: restricted when
    the non-user text grounds the date and no user text does. The extractor writes the date ISO, so a token match
    would miss a date the assistant said in words ("It is on November 4.") and restrict one the user said in words and
    the assistant echoed ISO (research's stage-1 read, 8b0de7d2). A date neither side grounds is not restricted here:
    it is ungrounded, and the briefing never volunteers an ungrounded fact (0045 §4b)."""
    user_text = "\n".join(b for sp, b in raw_turns if sp == "user")
    other_text = "\n".join(b for sp, b in raw_turns if sp == "non-user")
    return (grounding.ungrounded(obj, user_text, session_date)
            and not grounding.ungrounded(obj, other_text, session_date))


def speaker_restricts(subject: str, obj: str, event_text: str, relation: str | None = None,
                      session_date: str | None = None) -> bool:
    raw = turns(event_text)
    if not any(sp == "non-user" for sp, _b in raw):
        return False
    # the user's dated obligation, in either form (subject `user`, or named for itself: schema.is_obligation), is
    # judged on its date alone, by grounding, so a name the user said never shields a date only the assistant said
    # (the 0.29.0 release blocker B1). Another party's deadline (`person:…`) keeps the every-side rule below.
    if (relation == OBLIGATION_RELATION and session_date is not None
            and (str(subject).strip().casefold() == "user" or is_obligation(subject, relation))):
        return _date_restricts(obj, raw, session_date)
    ts = [(sp, _tokens(b)) for sp, b in raw]
    sides = [obj] if subject == "user" else [subject] if obj == "user" else [subject, obj]
    values = [_side(s) for s in sides]
    if any(not v for v in values):
        return False
    return all(any(_occurs(v, t) for sp, t in ts if sp == "non-user")
               and not any(_occurs(v, t) for sp, t in ts if sp == "user") for v in values)
