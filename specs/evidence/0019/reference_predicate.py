"""specs/0019 §4b — the NORMATIVE reference predicate (v4, resolution-set form).

PORTABLE AND PURE: no I/O, no external paths, no corpus dependency. Two
conforming implementations must agree with this module on every input; the
pinned vectors live beside it in `vectors.json` and
`test_predicate_matches_the_pinned_vectors` (U3) binds the shipped
implementation to both.

The predicate: an extracted object's SPECIFICS tokens (pure digits,
alphanumeric identifiers, proper-noun runs minus the position-0
sentence-leading single word) must each be grounded in the event text —
verbatim, or for ISO dates, by membership in the RESOLUTION SET of the
event text's date expressions against the session date (R2-1: proximity
grounds nothing; the date must equal a specific expression's deterministic
resolution).

Historical provenance: `phase1f_*.py` beside this file is the SUPERSEDED
window-form predicate whose measurement motivated the option-A class choice;
it is not the candidate.
"""

from __future__ import annotations

import calendar
import datetime
import re

WORD = re.compile(r"\w+")
ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
IDENTIFIER = re.compile(r"^(?=.*[a-z])(?=.*\d)[a-z0-9]+$")   # s21, 10k, v6
CAPRUN = re.compile(r"\b[A-Z][a-zA-Z0-9]+")

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday")
MONTHS = ("january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december")
MONTHS_ABBR = tuple(m[:3] for m in MONTHS)
RELATIVE_DAYS = {"today": 0, "tonight": 0, "tomorrow": 1, "yesterday": -1}
ORDINAL = re.compile(r"\b(\d{1,2})(st|nd|rd|th)\b")
NUMERIC_DATE = re.compile(r"\b\d{1,4}[-/.]\d{1,2}(?:[-/.]\d{1,4})?\b")
NEXT_LAST = re.compile(
    r"\b(next|last|this)\s+(week|month|year|" + "|".join(WEEKDAYS) + r")\b")

WINDOW_DAYS = 366


def toks(s: str) -> list[str]:
    return WORD.findall(s.lower())


def specifics_tokens(obj_raw: str) -> list[str]:
    """The §4b specifics classes, with the pinned position-0 rule."""
    out = []
    for t in toks(obj_raw):
        if t.isdigit() or IDENTIFIER.match(t):
            out.append(t)
    for m in CAPRUN.finditer(obj_raw):
        if m.start() == 0 and " " not in obj_raw[: m.end()]:
            continue                       # sentence-leading single cap word
        out.extend(toks(m.group(0)))
    return list(dict.fromkeys(out))


def _nearest_weekday(session: datetime.date, weekday_index: int
                     ) -> list[datetime.date]:
    """The nearest PAST and nearest FUTURE occurrence (both readings legal);
    when the session date IS the named weekday, the session date itself is
    also a legal resolution ("we met Friday", said on a Friday)."""
    delta = (weekday_index - session.weekday()) % 7
    future = session + datetime.timedelta(days=delta or 7)
    past = session - datetime.timedelta(days=(7 - delta) % 7 or 7)
    out = [past, future]
    if delta == 0:
        out.append(session)
    return out


def resolution_set(event_text: str, session_date: str) -> set[datetime.date]:
    """Every deterministic resolution of every §4b date expression found in
    the event text, window-filtered to ±366 days of the session date."""
    session = datetime.date.fromisoformat(session_date)
    low = toks(event_text)
    out: set[datetime.date] = set()

    for i, w in enumerate(low):
        if w in WEEKDAYS:
            out.update(_nearest_weekday(session, WEEKDAYS.index(w)))
        if w in RELATIVE_DAYS:
            out.add(session + datetime.timedelta(days=RELATIVE_DAYS[w]))
        # (month-day pairing moved to the ANCHORED patterns below — R3-2:
        # token-index proximity recreated the unrelated-number defect; a bare
        # month name yields NO date resolutions at all, month granularity
        # cannot deterministically resolve to any specific day)

    for m in NEXT_LAST.finditer(event_text.lower()):
        kind, unit = m.group(1), m.group(2)
        sign = {"next": 1, "last": -1, "this": 0}[kind]
        if unit in WEEKDAYS:
            wd = WEEKDAYS.index(unit)
            delta = (wd - session.weekday()) % 7
            if sign == 1:
                out.add(session + datetime.timedelta(days=delta or 7))
            elif sign == -1:
                out.add(session - datetime.timedelta(days=(7 - delta) % 7 or 7))
            else:
                out.add(session + datetime.timedelta(days=delta))
        elif unit == "week":
            out.add(session + datetime.timedelta(weeks=sign))
        elif unit == "month":
            month = session.month - 1 + sign
            year = session.year + month // 12
            month = month % 12 + 1
            day = min(session.day, calendar.monthrange(year, month)[1])
            out.add(datetime.date(year, month, day))
        elif unit == "year":
            try:
                out.add(session.replace(year=session.year + sign))
            except ValueError:
                out.add(session.replace(year=session.year + sign, day=28))

    # ANCHORED month-day expressions (R3-2): the day number must sit in a
    # date-syntactic position bound to the month name — "July 12",
    # "July 12th", "12 July", "the 12th of July". "July had 12 projects"
    # matches none of these.
    months_alt = "|".join(MONTHS) + "|" + "|".join(MONTHS_ABBR)
    low_text = event_text.lower()
    for m in re.finditer(
            rf"\b({months_alt})\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", low_text):
        _add_month_day(out, m.group(1), int(m.group(2)), session)
    for m in re.finditer(
            rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({months_alt})\b",
            low_text):
        _add_month_day(out, m.group(2), int(m.group(1)), session)

    for m in NUMERIC_DATE.finditer(event_text):
        for cand in _numeric_completions(m.group(0), session):
            out.add(cand)

    return {d for d in out
            if abs((d - session).days) <= WINDOW_DAYS}


def _add_month_day(out: set, month_word: str, day: int,
                   session: datetime.date) -> None:
    if not 1 <= day <= 31:
        return
    month = (MONTHS.index(month_word) + 1 if month_word in MONTHS
             else MONTHS_ABBR.index(month_word) + 1)
    for year in (session.year - 1, session.year, session.year + 1):
        try:
            out.add(datetime.date(year, month, day))
        except ValueError:
            pass


def _numeric_completions(s: str, session: datetime.date) -> list[datetime.date]:
    parts = re.split(r"[-/.]", s)
    out = []
    try:
        if len(parts) == 3:
            a, b, c = (int(x) for x in parts)
            for y, mth, d in ((a, b, c), (c, b, a), (c, a, b)):
                if y < 100:
                    y += 2000
                try:
                    out.append(datetime.date(y, mth, d))
                except ValueError:
                    pass
        elif len(parts) == 2:
            a, b = (int(x) for x in parts)
            for mth, d in ((a, b), (b, a)):
                for year in (session.year - 1, session.year, session.year + 1):
                    try:
                        out.append(datetime.date(year, mth, d))
                    except ValueError:
                        pass
    except ValueError:
        pass
    return out


def ungrounded(obj_raw: str, event_text: str, session_date: str) -> bool:
    """The §4b predicate: True iff any specifics token of the object is not
    grounded in the event text — verbatim, or (for tokens INSIDE an ISO date
    span) by that SPAN's atomic resolution-set membership.

    R3-1 determinism: every ISO span in the object is parsed and judged
    ATOMICALLY, by character position — a token is attributed to a span iff
    it lies within that span's character range, never by shared-token
    membership over a set (the round-3 nondeterminism). No iteration
    touches an unordered collection whose order matters; results are
    PYTHONHASHSEED-independent by construction."""
    text_tokens = set(toks(event_text))
    resolutions = None                        # computed lazily, once

    # 1. judge each ISO span atomically, recording its grounded character range
    grounded_spans: list[tuple[int, int]] = []
    for m in ISO_DATE.finditer(obj_raw):
        span_text = m.group(0)
        if all(tok in text_tokens for tok in toks(span_text)):
            grounded_spans.append(m.span())
            continue                          # verbatim-grounded span
        try:
            d = datetime.date.fromisoformat(span_text)
        except ValueError:
            continue                          # malformed span: tokens judged plainly
        if resolutions is None:
            resolutions = resolution_set(event_text, session_date)
        if d in resolutions:
            grounded_spans.append(m.span())

    def _in_grounded_span(pos: int) -> bool:
        return any(a <= pos < b for a, b in grounded_spans)

    # 2. every specifics token outside a grounded span must ground verbatim
    for m in WORD.finditer(obj_raw):
        token = m.group(0).lower()
        if token not in specifics_tokens(obj_raw):
            continue
        if _in_grounded_span(m.start()):
            continue
        if token not in text_tokens:
            return True
    return False
