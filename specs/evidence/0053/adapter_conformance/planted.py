"""specs/0053 §3a/§6: the canonicaliser's planted pairs, each a pair of small stores written here, so the canonicaliser is
judged on stores whose answer is known. Four it must report DIFFERENT, two EQUAL, and one it must REFUSE by name (v0.3,
Q6: a NULL against a value differs; the same instants as other text are equal; an unparseable clock is refused)."""
from __future__ import annotations

import os
import sqlite3

T1, T2 = "2026-07-01T10:00:00.000001+00:00", "2026-07-01T10:00:00.000002+00:00"
IDS = {("a", "id", ()), ("b", "id", ()), ("b", "a_ref", ()), ("p", "id", ()), ("e", "id", ())}
CLOCKS = {("e", "at", ())}


def _store(path, a_rows=(), b_rows=(), p_rows=(), e_rows=()):
    con = sqlite3.connect(path)
    con.executescript("CREATE TABLE a (id TEXT); CREATE TABLE b (id TEXT, a_ref TEXT);"
                      "CREATE TABLE p (id TEXT, author TEXT); CREATE TABLE e (id TEXT, at TEXT);")
    con.executemany("INSERT INTO a VALUES (?)", [(r,) for r in a_rows])
    con.executemany("INSERT INTO b VALUES (?, ?)", b_rows)
    con.executemany("INSERT INTO p VALUES (?, ?)", p_rows)
    con.executemany("INSERT INTO e VALUES (?, ?)", e_rows)
    con.commit()
    con.close()
    return path


#: (name, store A, store B, the verdict it must give: "equal", "different" or "refused")
def pairs(d):
    os.makedirs(d, exist_ok=True)
    s = lambda n, **kw: _store(os.path.join(d, n + ".db"), **kw)
    return [
        ("cross-row-reference", s("ref-a", a_rows=("a-x1aaaaaa", "a-x2aaaaaa"), b_rows=[("b-z1aaaaaa", "a-x1aaaaaa")]),
         s("ref-b", a_rows=("a-y1bbbbbb", "a-y2bbbbbb"), b_rows=[("b-w1bbbbbb", "a-y2bbbbbb")]), "different"),
        ("clock-reversal", s("rev-a", e_rows=[("e-1aaaaaaa", T1), ("e-2aaaaaaa", T2)]),
         s("rev-b", e_rows=[("e-1bbbbbbb", T2), ("e-2bbbbbbb", T1)]), "different"),
        ("provenance-field", s("prov-a", p_rows=[("p-1aaaaaaa", "user")]),
         s("prov-b", p_rows=[("p-1bbbbbbb", "third_party")]), "different"),
        ("tie-only", s("tie-a", e_rows=[("e-1aaaaaaa", T1), ("e-2aaaaaaa", T1)]),
         s("tie-b", e_rows=[("e-1bbbbbbb", T1), ("e-2bbbbbbb", T2)]), "equal"),
        # v0.3 (Q6): a NULL at a clock place against a value is a difference, compared as stored
        ("clock-null-against-a-value", s("null-a", e_rows=[("e-1aaaaaaa", None), ("e-2aaaaaaa", T2)]),
         s("null-b", e_rows=[("e-1bbbbbbb", T1), ("e-2bbbbbbb", T2)]), "different"),
        # ...the same instants written as other text (Z against +00:00, a whole second with and without its fraction) are
        # equal: clocks are ordered as aware instants, never as text. As raw strings the two places sort the other way
        ("same-instants-other-text", s("text-a", e_rows=[("e-1aaaaaaa", "2026-07-01T10:00:00Z"),
                                                         ("e-2aaaaaaa", "2026-07-01T10:00:00.5+00:00")]),
         s("text-b", e_rows=[("e-1bbbbbbb", "2026-07-01T10:00:00+00:00"),
                             ("e-2bbbbbbb", "2026-07-01T10:00:00.500000Z")]), "equal"),
        # ...and a clock that does not parse is refused by name, never ordered as text
        ("unparseable-clock", s("bad-a", e_rows=[("e-1aaaaaaa", "yesterday")]),
         s("bad-b", e_rows=[("e-1bbbbbbb", T1)]), "refused"),
    ]


def misjudged(canon_mod, d) -> list[str]:
    c = canon_mod.Canon(IDS, CLOCKS)
    bad = []
    for name, a, b, want in pairs(d):
        try:
            diff = c.differences(a, b)
        except AssertionError as exc:
            if want != "refused" or "not a timestamp" not in str(exc):
                bad.append(f"{name}: refused ({exc}) and must be {want}")
            continue
        if want == "refused":
            bad.append(f"{name}: judged ({'different' if diff else 'equal'}) and must be refused by name")
        elif want == "equal" and diff:
            bad.append(f"{name}: reported different ({diff[0]}) and must be equal")
        elif want == "different" and not diff:
            bad.append(f"{name}: reported equal and must be different")
    return bad
