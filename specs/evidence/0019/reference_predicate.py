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
        if w in MONTHS or w in MONTHS_ABBR:
            month = (MONTHS.index(w) if w in MONTHS
                     else MONTHS_ABBR.index(w)) + 1
            # a day ordinal or bare day number adjacent to the month name
            day = None
            for j in (i - 1, i + 1, i + 2):
                if 0 <= j < len(low):
                    m = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?", low[j])
                    if m and 1 <= int(m.group(1)) <= 31:
                        day = int(m.group(1))
                        break
            if day is not None:
                for year in (session.year - 1, session.year, session.year + 1):
                    try:
                        out.add(datetime.date(year, month, day))
                    except ValueError:
                        pass
            else:
                # bare month: month-granularity only — the month-START date;
                # a fabricated specific mid-month day is NOT a member
                for year in (session.year - 1, session.year, session.year + 1):
                    out.add(datetime.date(year, month, 1))

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

    for m in NUMERIC_DATE.finditer(event_text):
        for cand in _numeric_completions(m.group(0), session):
            out.add(cand)

    return {d for d in out
            if abs((d - session).days) <= WINDOW_DAYS}


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
    grounded in the event text (verbatim, or by resolution-set membership
    for ISO dates)."""
    text_tokens = set(toks(event_text))
    resolutions = None                        # computed lazily, once
    iso_in_obj = {m.group(0) for m in ISO_DATE.finditer(obj_raw)}

    for token in specifics_tokens(obj_raw):
        if token in text_tokens:
            continue
        parent_iso = next((d for d in iso_in_obj if token in toks(d)), None)
        if parent_iso is not None:
            if resolutions is None:
                resolutions = resolution_set(event_text, session_date)
            try:
                if datetime.date.fromisoformat(parent_iso) in resolutions:
                    continue
            except ValueError:
                pass
        return True
    return False
