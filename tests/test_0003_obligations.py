"""specs/0003/obligations (amendment v0.2, research 824309d4, adopted 2026-11-01; the owner, 2026-10-29: "(A) in the held
release", 2026-11-01: "Ship, then review"): an obligation's subject is the named thing, and the briefing renders a
contested commitment ONCE.

The defect (research's free-roam, 00e3ae17): `deadline` is functional and the extractor wrote every commitment under
subject `user`, so each new one superseded the last. §4a moves the name to the subject; §4b renders a refused
reschedule once, marked contested, in DATED COMMITMENTS; §4c is the doctor's report-only count. Driven through
`Memory.remember` with a scripted extractor, so every cell runs the shipped ingest and briefing; the briefing's window
is the config default (7 days), so every date is relative to today.
"""

import json
import re
import pathlib
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from veracium import EvidenceAuthor, EvidenceContext, Memory, MemoryConfig, doctor, proactive
from veracium.prompts import EXTRACT_PROMPT
from veracium.schema import Disclosure, Edge, Provenance

U = "u"
DAY = lambda n: (datetime.now(timezone.utc).date() + timedelta(days=n)).isoformat()  # noqa: E731 (the briefing's UTC today)
D1, D2, FAR = DAY(2), DAY(4), DAY(30)
RULE = ("- A dated obligation the user states (an appointment, a deadline, a due date,\n"
        "  a renewal, a scheduled event) is ONE triple whose SUBJECT is the obligation\n"
        "  itself")


class Scripted:
    """Each distill call emits the next scripted list of (subject, relation, object); captures every prompt sent."""

    def __init__(self, *scripts):
        self.scripts, self.prompts = list(scripts), []

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            self.prompts.append(prompt)
            return json.dumps({"triples": [{"subject": s, "relation": r, "object": o, "volatility": "durable"}
                                           for s, r, o in self.scripts.pop(0)],
                               "episode": "The user mentioned a commitment.", "instructions": []})
        return ""


def _say(triples):
    """Event text that STATES each triple, so 0045's grounding admits it (an ungrounded fact never reaches the
    briefing, and a cell over ungrounded facts would pass vacuously)."""
    return "USER: " + " ".join(f"I have a {o}." if s == "user" else f"I have a {s} on {o}." for s, _r, o in triples)


def _mem(d, *scripts, author=None):
    llm = Scripted(*scripts)
    m = Memory(llm=llm, config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
    for i, triples in enumerate(scripts):
        who = (author or {}).get(i)
        if who is None:
            m.remember(U, _say(triples), date=DAY(-10 + i), context=EvidenceContext.direct())
        else:
            m.remember(U, f"The clinic says your {triples[0][0]} moved to {triples[0][2]}.", date=DAY(-10 + i),
                       author=who, source_id="clinic")
    return m, llm


def _deadlines(m):
    return [e for e in m.store.edges(U, active_only=False, include_quarantined=True) if e.relation == "deadline"]


def _rows(m):
    return m.store._conn.execute("SELECT rule_version FROM supersession_refusals WHERE user_id=?", (U,)).fetchall()


def _commitments(m):
    """The DATED COMMITMENTS lines of the briefing, asserted present (an empty briefing is the property failing)."""
    ctx = m.recall(U).context
    assert "## DATED COMMITMENTS" in ctx, ctx
    return [ln for ln in ctx.split("## DATED COMMITMENTS\n", 1)[1].split("\n\n", 1)[0].splitlines()
            if ln.strip() and not ln.startswith("[")]      # a status line ("[withheld: …]") is not a commitment


def _plain(subject, d):
    return f"deadline: {subject} — {d} (due {d})"


def _contested(subject, *ds):
    when = ds[0] if len(ds) == 1 else ", ".join(ds[:-1]) + " or " + ds[-1]
    return f"deadline: {subject} — CONTESTED: {when} (unconfirmed which is current)"


TWO = ([("dentist appointment", "deadline", D1)], [("haircut appointment", "deadline", D2)])
RESCHEDULE = ([("dentist appointment", "deadline", D1)], [("dentist appointment", "deadline", D2)])


# ---- §4a, INV-OB1: two obligations in the user's words coexist ---------------------------------------------------
def test_ob1_two_obligations_coexist():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *TWO)
        es = _deadlines(m)
        assert sorted((e.subject, e.object) for e in es if e.active) == [("dentist appointment", D1),
                                                                        ("haircut appointment", D2)], es
        assert [e for e in es if not e.active] == [] and _rows(m) == []


def test_ob1_the_subject_user_form_is_the_defect_it_answers():
    """The defect's own cell, kept beside its inversion: under subject `user` the second commitment retires the first."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("user", "deadline", f"dentist appointment on {D1}")],
                    [("user", "deadline", f"haircut appointment on {D2}")])
        assert [(e.object, e.invalidation_reason) for e in _deadlines(m) if not e.active] == [
            (f"dentist appointment on {D1}", "superseded")]


# ---- §4a, INV-OB2: a reschedule is contested, never silently applied or lost ----------------------------------------
def test_ob2_a_reschedule_is_contested_with_one_refusal_row():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *RESCHEDULE)
        assert sorted(e.object for e in _deadlines(m) if e.active) == [D1, D2]
        assert [e for e in _deadlines(m) if not e.active] == []
        assert _rows(m) == [("supersession-authority-v2",)]
        groups = m.recall(U, "dentist appointment").contested
        assert [(g.subject, g.relation, sorted(x.object for x in g.exposed)) for g in groups] == [
            ("dentist appointment", "deadline", [D1, D2])], groups


# ---- §4b, INV-OB3: the briefing renders a contested group ONCE, marked, with both dates -----------------------------
def test_ob3_the_briefing_renders_a_contested_commitment_once():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *RESCHEDULE)
        lines = _commitments(m)
        assert lines == [_contested("dentist appointment", D1, D2)], lines
        assert sorted(e.object for e in m.recall(U).edges) == [D1, D2]     # every member is returned (D3)
        assert m.recall(U).contested == []                                 # no new public carrier (D3)


def test_ob10_one_episode_naming_two_dates_renders_once_contested():
    """Research's addition: one message, two dates for one obligation. The subject axis refuses first (subject OTHER),
    so the row is supersession-authority-v2, and the briefing renders the pair once."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", D1), ("dentist appointment", "deadline", D2)])
        assert sorted(e.object for e in _deadlines(m) if e.active) == [D1, D2] and len(_rows(m)) == 1
        assert _commitments(m) == [_contested("dentist appointment", D1, D2)]


def test_a_member_outside_the_window_never_appears_and_marks_its_partner():
    """0012 I10d: contested material gets NO NEW REACH. A reschedule past the window leaves one member in the
    commitment tier: it renders plain, MARKED contested, and the out-of-window date appears nowhere."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", D1)], [("dentist appointment", "deadline", FAR)])
        ctx = m.recall(U).context
        assert _commitments(m) == [_plain("dentist appointment", D1) + " (contested — unconfirmed which date is current)"]
        assert FAR not in ctx, ctx


def test_an_uncontested_commitment_carries_no_mark():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", D1)])
        assert _commitments(m) == [_plain("dentist appointment", D1)]


def test_a_group_with_no_member_in_the_window_renders_nothing():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", FAR)], [("dentist appointment", "deadline", DAY(40))])
        assert "## DATED COMMITMENTS" not in m.recall(U).context


# ---- §4b, research's stage-2 B1: a contested line names each member's OBJECT, not only a date ---------------------
def test_b1_a_contested_line_keeps_each_members_object():
    """A contested group of any functional relation renders each member's object (clamped), not the date the object
    or note happens to carry: "Berlin until D1" vs "Paris from D2" must not read as two dates for Alice."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("person:alice", "located_at", f"Berlin until {D1}")], [("person:alice", "located_at", f"Paris from {D2}")])
        assert len(_rows(m)) == 1, _rows(m)
        ctx = m.recall(U).context
        assert "Berlin" in ctx and "Paris" in ctx, ctx
        line = next(ln for ln in ctx.splitlines() if "CONTESTED" in ln)
        assert line == f"located_at: person:alice — CONTESTED: Berlin until {D1} or Paris from {D2} (unconfirmed which is current)", line


def test_b1_a_contested_deadline_keeps_its_time_and_place():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", f"{D1} at 3pm with Dr. Lee")],
                    [("dentist appointment", "deadline", f"{D2} at 9am with Dr. Patel")])
        assert _commitments(m) == [_contested("dentist appointment", f"{D1} at 3pm with Dr. Lee", f"{D2} at 9am with Dr. Patel")]


# ---- §4b, the plain line names its subject (research S1-4) -----------------------------------------------------------
def test_a_plain_commitment_names_a_subject_other_than_user():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *TWO)
        assert _commitments(m) == [_plain("dentist appointment", D1), _plain("haircut appointment", D2)]


def test_a_subject_user_commitment_renders_byte_identical_to_before():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("user", "deadline", f"dentist appointment on {D1}")])
        assert _commitments(m) == [f"deadline: dentist appointment on {D1} (due {D1})"]


def test_an_oversized_subject_is_clamped_and_counted():
    """Research S1-4(a): the subject is extracted text, clamped as the object is, and its clamp signals (I10a)."""
    big = "dentist appointment " + "x" * 4000
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [(big, "deadline", D1)])
        r = m.recall(U)
        line = _commitments(m)[0]
        assert len(line) < 1000 and big not in line and line.endswith(f"(due {D1})"), line
        assert r.truncated, r.context


# ---- the N1–N4 batch (research's stage 2 on 6d10dc6, 4910a8b9; stage 1 on ea88c72, d3d22dd5) -----------------------
TAIL = " (unconfirmed which is current)"
MARK = " (contested — unconfirmed which date is current)"


def _clamped(ctx):
    """The I10a figure the report line states (0 when no report line: nothing was dropped or clamped)."""
    found = re.findall(r"/ (\d+) clamped\]", ctx)
    assert len(found) <= 1, ctx
    return int(found[0]) if found else 0


def _cap(m, line):
    return m._est_tokens(line) <= m.config.item_cap_tokens


def _many(d, n, subject="dentist appointment"):
    """n refused reschedules of one obligation, each overdue (dated before today): one contested group of n."""
    llm = Scripted(*[[(subject, "deadline", DAY(-n - 1 + i))] for i in range(n)])
    m = Memory(llm=llm, config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
    for i in range(n):
        m.remember(U, f"USER: I have a {subject} on {DAY(-n - 1 + i)}.", date=DAY(-n - 1 + i),
                   context=EvidenceContext.direct())
    return m


def test_n1_a_long_group_at_the_floor_budget_keeps_its_nearest_dates_and_its_framing():
    """0012 §4c-v.3 (N1): at the floor budget a 70-member group line is RECOMPOSED, never tail-clamped. The framing
    ends the line, the nearest dates are kept whole and in order, the rest are named "or K more" (K the distinct
    values not shown), every member is still returned, and the line is ONE clamped item."""
    with tempfile.TemporaryDirectory() as d:
        m = _many(d, 70)
        r = m.recall(U, token_budget=256)
        line = next(ln for ln in r.context.splitlines() if "CONTESTED" in ln)
        assert line.endswith(TAIL) and "content truncated" not in line, line
        body = line.split(" — CONTESTED: ", 1)[1][:-len(TAIL)]
        shown, k = body.rsplit(" or ", 1)
        k = int(k.removesuffix(" more"))
        shown = shown.split(", ")
        assert shown == [DAY(-71 + i) for i in range(len(shown))] and len(shown) + k == 70, line
        assert len([e for e in r.edges if e.relation == "deadline"]) == 70
        assert _clamped(r.context) == 1, r.context


def test_n1_a_group_of_oversized_objects_is_held_to_the_item_cap():
    """N1 (research's B1 re-check at e4bbdc4): two 2,400-char objects made a ~3,790-char line, never item-capped."""
    o1, o2 = f"{D1} " + "a" * 2400, f"{D2} " + "b" * 2400
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("lease renewal", "deadline", o1)], [("lease renewal", "deadline", o2)])
        r = m.recall(U)
        line = next(ln for ln in r.context.splitlines() if "CONTESTED" in ln)
        assert _cap(m, line) and line.startswith(f"deadline: lease renewal — CONTESTED: {D1} a") and \
            line.endswith(" or 1 more" + TAIL), line
        assert _clamped(r.context) == 1, r.context


def test_n1_k_counts_the_distinct_values_not_shown_not_the_members():
    """K counts the distinct VALUES the line does not show. Two members whose different objects clamp to one display
    string are TWO values (SR1-01, shipped-changes round 1: this cell used to call them one, which is the defect the
    reviewer reproduced), so one shown slot leaves two more."""
    o1, o2, o3 = f"{D1} " + "a" * 3000 + "1", f"{D1} " + "a" * 3000 + "2", f"{D2} " + "c" * 400
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *[[("lease renewal", "deadline", o)] for o in (o1, o2, o3)])
        line = next(ln for ln in m.recall(U).context.splitlines() if "CONTESTED" in ln)
        assert _cap(m, line) and line.endswith(" or 2 more" + TAIL), line


def test_n1_k_counts_values_when_one_episode_repeats_a_value():
    """K counts distinct VALUES, not members, and a group CAN hold one value twice: a prior A and one episode naming
    [B, A] keep both A edges current (0003 §4c-iv), so the group is three members over two values. One shown slot
    leaves ONE more, not two. Here the commitment tier collapses the repeated value before the line is composed (two
    members over two values), so this cell does NOT reach N1-K-counts-members; a repeated value whose two edges carry
    DISTINCT NOTES does (SR2-03, shipped-changes round 2: the cells below), and that mutant is a row again."""
    # ~300 tokens each: ONE value fits the 512-token line, two do not, so the elided form is composed (the one-slot
    # fallback, taken when not even one fits, counts K on its own)
    a, b = f"{D1} " + "a" * 1200, f"{D2} " + "b" * 1200
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("lease renewal", "deadline", a)], [("lease renewal", "deadline", b), ("lease renewal", "deadline", a)])
        gs, _ = m._build_contested(U, [], None)
        assert len(gs) == 1 and len(gs[0].exposed) == 3 and len({e.object for e in gs[0].exposed}) == 2, gs
        line = next(ln for ln in m.recall(U).context.splitlines() if "CONTESTED" in ln)
        assert _cap(m, line) and line.endswith(" or 1 more" + TAIL), line


class _NoteScripted:
    """SR2-03 (shipped-changes round 2): the reviewer's scripted extractor (repro/probe_round2.py), carrying each
    triple's NOTE. A repeated value with a different note is a different carrier: `collapse_for_render` keeps both,
    and the commitment tier admits every dated member."""
    def __init__(self, script):
        self.s = list(script)

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role != "distill":
            return ""
        return json.dumps({"triples": [{"subject": "dentist appointment", "relation": "deadline", "object": o,
                                        "note": n, "volatility": "durable"} for o, n in self.s.pop(0)],
                           "episode": "The user stated a dated commitment.", "instructions": []})


def _distinct_note_line(tmp_path, a, b):
    """The reviewer's case: A (note 'initial appointment'); then B (note 'new appointment') and A again (note 'restated
    appointment'). All three edges stay active and grounded and ALL THREE reach the contested tier: three members, two
    distinct values. Returns the contested line at the reviewer's fixed clock."""
    from veracium.budgets import est_tokens
    m = Memory(llm=_NoteScripted([[(a, "initial appointment")], [(b, "new appointment"), (a, "restated appointment")]]),
               config=MemoryConfig(db_path=str(tmp_path / "k.db"), require_source_id=False,
                                   wiki_recompile_after_writes=0))
    m.remember(U, f"My dentist appointment is {a}.", date="2026-11-01", context=EvidenceContext.direct())
    m.remember(U, f"My dentist appointment is {b} or {a}.", date="2026-11-02", context=EvidenceContext.direct())
    gs, _ = m._build_contested(U, [], None)
    ctx, edges, _, _ = proactive.assemble(m.store, U, m.config, now=datetime(2026, 11, 11, tzinfo=timezone.utc),
                                          token_budget=1200, est=est_tokens,
                                          contested=[(g.subject, g.relation, [e.id for e in g.exposed]) for g in gs])
    m.close()
    assert len(edges) == 3 and len({e.object for e in edges}) == 2, \
        f"the case must put three members over two values in the tier, or it does not reach the member count: {edges}"
    return next(ln for ln in ctx.splitlines() if "CONTESTED" in ln)


def test_sr2_03_a_repeated_value_with_a_distinct_note_is_one_value_on_the_one_slot_path(tmp_path):
    """SR2-03 (shipped-changes round 2), the reviewer's distinct-note case verbatim: values of ~300 tokens, so the
    one-slot fallback composes the line. K counts DISTINCT VALUES (two), not members (three): one more, not two.
    Kills N1-K-counts-members, which the round-2 package had declared equivalent."""
    line = _distinct_note_line(tmp_path, "2026-11-12 " + "a" * 1200, "2026-11-14 " + "b" * 1200)
    assert line.endswith(" or 1 more" + TAIL), line[-120:]


def test_sr2_03_a_repeated_value_with_a_distinct_note_is_one_value_on_the_ordinary_path(tmp_path):
    """SR2-03 on the ordinary path (research's stage-1 measurement on 0d06c4b3): short values, both shown. Two distinct
    values with nothing left over name no "or K more"; K over the three members would read "…, … or 1 more"."""
    line = _distinct_note_line(tmp_path, "2026-11-12", "2026-11-14")
    assert line.endswith("CONTESTED: 2026-11-12 or 2026-11-14" + TAIL), line



def test_sr2_03_a_one_value_unit_clamped_on_the_one_slot_path_is_reported_clamped(tmp_path):
    """Research's stage-1 measurement for round 3 (A5, a neighbour SR2-03's declaration had called equivalent): the
    distinct-note pattern with B's date BEYOND the briefing window puts A twice in the tier, two members over ONE value,
    so K is 0. At a 256-token budget the one-slot fallback clamps that value to what the framing leaves (a cut the
    member check `_obj(m) != m.object` cannot see, the value being under the object width). Only `first != values[0]`
    signals it, so the budget report must count one clamped item."""
    from veracium.budgets import est_tokens
    a, b = "2026-11-12 " + "a" * 900, "2027-06-01 " + "b" * 900
    m = Memory(llm=_NoteScripted([[(a, "initial")], [(b, "new"), (a, "restated")]]),
               config=MemoryConfig(db_path=str(tmp_path / "a5.db"), require_source_id=False,
                                   wiki_recompile_after_writes=0))
    m.remember(U, f"My dentist appointment is {a}.", date="2026-11-01", context=EvidenceContext.direct())
    m.remember(U, f"My dentist appointment is {b} or {a}.", date="2026-11-02", context=EvidenceContext.direct())
    gs, _ = m._build_contested(U, [], None)
    ctx, edges, _, _ = proactive.assemble(m.store, U, m.config, now=datetime(2026, 11, 11, tzinfo=timezone.utc),
                                          token_budget=256, est=est_tokens,
                                          contested=[(g.subject, g.relation, [e.id for e in g.exposed]) for g in gs])
    m.close()
    line = next(ln for ln in ctx.splitlines() if "CONTESTED" in ln)
    # reach: one value over two members, nothing left to count, and the shown value is cut on the one-slot path
    assert len(edges) == 2 and {e.object for e in edges} == {a}, edges
    assert " more" not in line and a not in line and line.endswith(TAIL), line[-120:]
    assert ctx.splitlines()[-1].endswith(" / 1 clamped]"), ctx.splitlines()[-1]

def _mem_cap(d, cap, *objects):
    """A contested lease renewal over `objects`, with item_cap_tokens=`cap` (64, the floor, lets two clamped
    displays share one line, so a display collision is visible)."""
    llm = Scripted(*[[("lease renewal", "deadline", o)] for o in objects])
    m = Memory(llm=llm, config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db", wiki_recompile_after_writes=0,
                                            item_cap_tokens=cap))
    for i, o in enumerate(objects):
        m.remember(U, _say([("lease renewal", "deadline", o)]), date=DAY(-10 + i), context=EvidenceContext.direct())
    return m


def test_sr1_01_two_distinct_values_that_clamp_alike_are_one_shown_and_one_more():
    """SR1-01 (shipped-changes round 1): distinctness is decided on the original objects, before the clamp. Two
    different values whose clamped displays are identical are two values; the second display, repeating the first,
    is not shown again and is counted in K (research's stage 1, Q1). Before the fix the line showed one slot and no
    "or 1 more"; without the fold it would read "X or X"."""
    from veracium.budgets import clamp_item
    a, b = f"{D1} " + "a" * 300 + "1", f"{D1} " + "a" * 300 + "2"
    with tempfile.TemporaryDirectory() as d:
        m = _mem_cap(d, 64, a, b)
        r = m.recall(U)
        line = next(ln for ln in r.context.splitlines() if "CONTESTED" in ln)
        assert line == f"deadline: lease renewal — CONTESTED: {clamp_item(a, 16)} or 1 more" + TAIL, line
        assert clamp_item(a, 16) == clamp_item(b, 16) and _clamped(r.context) == 1, r.context
        assert {e.object for e in r.edges if e.relation == "deadline"} == {a, b}


def test_sr1_01_a_collision_beside_a_plain_value_keeps_the_plain_value_and_counts_the_collision():
    """The matrix's third cell: two values collide in display, a third does not. The plain value is shown, in
    nearest-due order after the first, and the colliding one is the one more."""
    from veracium.budgets import clamp_item
    a, b, c = f"{D1} " + "a" * 300 + "1", f"{D1} " + "a" * 300 + "2", f"{D2} plain"
    with tempfile.TemporaryDirectory() as d:
        m = _mem_cap(d, 64, a, b, c)
        r = m.recall(U)
        line = next(ln for ln in r.context.splitlines() if "CONTESTED" in ln)
        assert line == f"deadline: lease renewal — CONTESTED: {clamp_item(a, 16)}, {c} or 1 more" + TAIL, line
        assert _clamped(r.context) == 1, r.context


_LONG_SUBJECT = "lease renewal " + "x" * 400     # its label is clamped at item_cap//8, so no n-slot line fits


def _one_slot_line(d, *objects):
    llm = Scripted(*[[(_LONG_SUBJECT, "deadline", o)] for o in objects])
    m = Memory(llm=llm, config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
    for i, o in enumerate(objects):
        m.remember(U, _say([(_LONG_SUBJECT, "deadline", o)]), date=DAY(-10 + i), context=EvidenceContext.direct())
    r = m.recall(U)
    return m, r, next(ln for ln in r.context.splitlines() if "CONTESTED" in ln)


def test_r2s_2_the_one_slot_path_shows_the_nearest_value_and_counts_the_other():
    """R2S-2 (research's stage 2 on 974a6122, P1): the one-slot fallback, taken when no n-slot line fits, shows the
    NEAREST value clamped to what the framing leaves and counts the other in K."""
    from veracium.budgets import clamp_item
    a, b = f"{D1} " + "a" * 3000, f"{D2} " + "b" * 3000
    with tempfile.TemporaryDirectory() as d:
        m, r, line = _one_slot_line(d, a, b)
        head = f"deadline: {clamp_item(_LONG_SUBJECT, 64)} — CONTESTED: "
        assert line.startswith(head + f"{D1} a") and line.endswith(" or 1 more" + TAIL), line[:120]
        assert len(line) - len(head) - len(" or 1 more" + TAIL) < len(clamp_item(a, 512 - 48)), "not the one-slot path"
        assert _cap(m, line) and _clamped(r.context) == 1, r.context
        m.close()


def test_r2s_2_sr1_01_on_the_one_slot_path():
    """R2S-2 (research's P2): SR1-01 on the other path. Two different values whose composition-width displays are
    identical are still two values: the one-slot line counts the second."""
    from veracium.budgets import clamp_item
    a, b = f"{D1} " + "a" * 3000 + "1", f"{D1} " + "a" * 3000 + "2"
    assert clamp_item(a, 512 - 48) == clamp_item(b, 512 - 48)
    with tempfile.TemporaryDirectory() as d:
        m, r, line = _one_slot_line(d, a, b)
        assert {e.object for e in r.edges if e.relation == "deadline"} == {a, b}
        assert line.endswith(" or 1 more" + TAIL), line[-80:]
        m.close()


class _ReviewerScripted:
    def __init__(self, s):
        self.s = list(s)

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role != "distill":
            return ""
        ts, ep = self.s.pop(0)
        return json.dumps({"triples": [{"subject": s, "relation": r, "object": o, "volatility": "durable"}
                                       for s, r, o in ts], "episode": ep, "instructions": []})


def test_sr1_01_the_reviewers_regression(tmp_path):
    """The reviewer's own regression for SR1-01 (shipped-changes round 1, repro/test_review_regressions.py), its
    assertions verbatim: two distinct 2,400-character values sharing their prefix, at the reviewer's fixed clock."""
    from veracium.budgets import est_tokens
    prefix = "appointment details " * 120
    values = [prefix + " ALPHA LOCATION 2026-11-12", prefix + " OMEGA LOCATION 2026-11-14"]
    m = Memory(llm=_ReviewerScripted([([("clinic appointment", "deadline", o)], "A clinic appointment.") for o in values]),
               config=MemoryConfig(db_path=str(tmp_path / "count.db"), require_source_id=False,
                                   wiki_recompile_after_writes=0))
    for i, o in enumerate(values):
        m.remember("u", "USER: My clinic appointment is " + o, date=f"2026-11-0{i + 1}", context=EvidenceContext.direct())
    gs, _ = m._build_contested("u", [], None)
    assert len(gs) == 1 and len(gs[0].exposed) == 2
    ctx, edges, _, _ = proactive.assemble(m.store, "u", m.config, now=datetime(2026, 11, 10, tzinfo=timezone.utc),
                                          token_budget=1200, est=est_tokens,
                                          contested=[(g.subject, g.relation, [e.id for e in g.exposed]) for g in gs])
    assert len({e.object for e in edges}) == 2
    assert " or 1 more (unconfirmed which is current)" in ctx, \
        "two distinct values became one clamped slot without the required omitted-value count"
    m.close()


def test_new1_a_plain_commitment_line_is_held_to_the_item_cap():
    """Research's stage-1 NEW 1: the object's cap (item_cap−48) sat on top of the subject's (item_cap//8), so a
    420-char subject and a 3,000-char object rendered 536 tokens against 512. The whole line is held to the cap,
    framing intact, one clamped item."""
    sub, obj = "dentist appointment " + "x" * 400, f"{D1} " + "o" * 2989
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [(sub, "deadline", obj)])
        r = m.recall(U)
        line = _commitments(m)[0]
        assert _cap(m, line) and line.endswith(f"(due {D1})"), (m._est_tokens(line), line[-80:])
        assert _clamped(r.context) == 1, r.context


def test_new1_a_marked_lone_member_is_held_to_the_item_cap_with_its_mark():
    """The lone member's mark is part of the line it is held to (it was appended after composition)."""
    sub, obj = "dentist appointment " + "x" * 400, f"{D1} " + "o" * 2989
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [(sub, "deadline", obj)], [(sub, "deadline", FAR)])
        line = _commitments(m)[0]
        assert _cap(m, line) and line.endswith(f"(due {D1}){MARK}"), (m._est_tokens(line), line[-80:])


def test_n2_a_clamped_group_is_one_clamped_item():
    """N2 (R-impl4-4: EXACT per clamped item): a grouped member's composed line is discarded, so its clamps are not
    counted; the group line is the one item."""
    big = "dentist appointment " + "x" * 400
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [(big, "deadline", D1)], [(big, "deadline", D2)])
        assert len(_rows(m)) == 1
        assert _clamped(m.recall(U).context) == 1


def test_n2_a_group_beside_a_clamped_plain_commitment_is_two_clamped_items():
    """N2's control (research): removing grouped members' clamps must not remove another line's."""
    big, other = "dentist appointment " + "x" * 400, "haircut appointment " + "y" * 400
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [(big, "deadline", D1)], [(big, "deadline", D2)], [(other, "deadline", D1)])
        assert len(_commitments(m)) == 2
        assert _clamped(m.recall(U).context) == 2


def test_n3_a_group_sorts_at_its_nearest_due_date():
    """0012 §4c-v's Order rule (N3, R3): a group is ONE commitment at its NEAREST due date."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", D1)], [("dentist appointment", "deadline", DAY(5))],
                    [("haircut appointment", "deadline", D2)])
        assert _commitments(m) == [_contested("dentist appointment", D1, DAY(5)), _plain("haircut appointment", D2)]


def test_n3_groups_tied_on_their_nearest_date_sort_newest_observation_first():
    """0012 I10b's tie (N3, R4): observed_at DESC, a group's observation its newest member's."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", D1)], [("dentist appointment", "deadline", DAY(5))],
                    [("haircut appointment", "deadline", D1)], [("haircut appointment", "deadline", DAY(6))])
        assert _commitments(m) == [_contested("haircut appointment", D1, DAY(6)),
                                   _contested("dentist appointment", D1, DAY(5))]


# ---- §4b, INV-OB4: the contested predicate IS the refusal-scoped one ------------------------------------------------
def _edge(eid, subject, obj, *, author=EvidenceAuthor.USER, disc=Disclosure.MENTIONABLE):
    return Edge(id=eid, user_id=U, subject=subject, relation="deadline", object=obj,
                provenance=Provenance(author_of_evidence=author, evidence_ref=f"ev-{eid}", disclosure=disc),
                ungrounded=False)


def test_ob4_two_dated_values_with_no_refusal_row_render_as_two_plain_commitments():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d)
        m.store.add_edge(_edge("e-a", "dentist appointment", D1))
        m.store.add_edge(_edge("e-b", "dentist appointment", D2))
        assert _rows(m) == []
        assert _commitments(m) == [_plain("dentist appointment", D1), _plain("dentist appointment", D2)]


# ---- §4b, INV-OB8: only MENTIONABLE members count; a fenced challenger is never volunteered --------------------------
def test_ob8_a_fenced_third_party_challenger_leaves_one_plain_line():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *RESCHEDULE, author={1: EvidenceAuthor.THIRD_PARTY})
        fenced = [e for e in _deadlines(m) if e.object == D2]
        assert fenced and not fenced[0].assertable and len(_rows(m)) == 1, fenced
        ctx = m.recall(U).context
        assert _commitments(m) == [_plain("dentist appointment", D1)]
        assert "CONTESTED" not in ctx and D2 not in ctx, ctx


# ---- §4b, INV-OB9: 0047's withholding applies per member BEFORE the count --------------------------------------------
def test_ob9_a_challenged_member_is_withheld_before_the_group_is_counted():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *RESCHEDULE)
        late = next(e for e in _deadlines(m) if e.object == D2)
        m.reply(U, late.id, kind="challenge", text="that is wrong")
        ctx = m.recall(U).context
        assert _commitments(m) == [_plain("dentist appointment", D1)], ctx
        assert "CONTESTED" not in ctx and f"— {D2}" not in ctx, ctx
        assert "[withheld: 1 fact(s) the subject disputes" in ctx, ctx


def test_a_withheld_commitments_subject_is_never_rendered():
    """Research S1-4(b): the subject is a field this section never volunteered before, so it passes every disclosure
    rule the object does: a challenged (0047-withheld) commitment's NAME reaches no line."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", D1)], [("tax filing", "deadline", D2)])
        secret = next(e for e in _deadlines(m) if e.subject == "tax filing")
        m.reply(U, secret.id, kind="challenge", text="that is wrong")
        ctx = m.recall(U).context
        assert _commitments(m) == [_plain("dentist appointment", D1)] and "tax filing" not in ctx, ctx


def test_a_lone_member_whose_partner_is_flagged_is_marked_contested():
    """D1's residual, closed: a flagged member renders in CONFIRM WHEN NATURAL (I10f), and the date left alone in DATED
    COMMITMENTS is marked, so it never reads as settled."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *RESCHEDULE)
        late = next(e for e in _deadlines(m) if e.object == D2)
        m.store._conn.execute("UPDATE edges SET json=json_set(json, '$.needs_confirmation', json('true')) WHERE id=?",
                              (late.id,))
        m.store._conn.commit()
        assert _commitments(m) == [_plain("dentist appointment", D1) + " (contested — see CONFIRM)"]


# ---- §4b, research's C1–C3: the mark names no content, and a partner the principal cannot see gives none ------------
def _scoped(d, partner):
    from veracium.graph import apply_supersession
    from veracium.scope import Identity
    a1 = Identity(None, "agent-1")
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0,
                                                          scope_groups={"team-a": [a1]}, require_source_id=False))
    m.store.add_edge(_edge("e-own", "dentist appointment", D1).model_copy(update={"provenance": Provenance(
        author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-own", disclosure=Disclosure.MENTIONABLE,
        source_id="agent-1")}))
    apply_supersession(m.store, partner, m.config.relations)
    assert len(_rows(m)) == 1, "the contest under test was not recorded"
    return m, a1


def _partner(obj, source_id, *, author=EvidenceAuthor.USER, ref="ev-p"):
    return _edge("e-p", "dentist appointment", obj).model_copy(update={"provenance": Provenance(
        author_of_evidence=author, evidence_ref=ref, disclosure=Disclosure.MENTIONABLE, source_id=source_id)})


def _scoped_commitments(m, principal):
    ctx = m.recall(U, principal=principal).context
    return [ln for ln in ctx.split("## DATED COMMITMENTS\n", 1)[1].split("\n\n", 1)[0].splitlines()
            if ln.strip() and not ln.startswith("[")], ctx


def test_c1_a_cross_scope_partner_gives_no_group_and_no_mark():
    """0020 N-1, stricter than N-2's query-path status: in the briefing a partner the principal cannot see leaves the
    principal's own commitment exactly as if the partner did not exist. The unscoped briefing still shows the contest."""
    with tempfile.TemporaryDirectory() as d:
        m, a1 = _scoped(d, _partner(D2, "agent-2"))
        assert _commitments(m) == [_contested("dentist appointment", D1, D2)]
        lines, ctx = _scoped_commitments(m, a1)
        assert lines == [_plain("dentist appointment", D1)] and D2 not in ctx, ctx


def test_c1_an_unresolved_partner_gives_no_mark():
    from veracium.scope import UNRESOLVED
    with tempfile.TemporaryDirectory() as d:
        p = _partner(FAR, "agent-2", author=EvidenceAuthor.SYSTEM, ref="op-0123456789ab")
        m, a1 = _scoped(d, p)
        assert m._scope_view(U, a1, None).evidence(p) == UNRESOLVED
        assert _commitments(m) == [_plain("dentist appointment", D1) + " (contested — unconfirmed which date is current)"]
        lines, ctx = _scoped_commitments(m, a1)
        assert lines == [_plain("dentist appointment", D1)], ctx


def test_c2_a_redacted_partner_gives_no_mark():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", D1)], [("dentist appointment", "deadline", FAR)])
        assert _commitments(m) == [_plain("dentist appointment", D1) + " (contested — unconfirmed which date is current)"]
        far = next(e for e in _deadlines(m) if e.object == FAR)
        m.redact(U, edge_id=far.id, reason="erroneous_capture")
        assert _commitments(m) == [_plain("dentist appointment", D1)]


def test_c2_a_redacted_partner_in_the_window_gives_no_group():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *RESCHEDULE)
        late = next(e for e in _deadlines(m) if e.object == D2)
        m.redact(U, edge_id=late.id, reason="erroneous_capture")
        ctx = m.recall(U).context
        assert _commitments(m) == [_plain("dentist appointment", D1)] and "CONTESTED" not in ctx, ctx


def test_c3_the_mark_names_no_date_object_count_or_attribution():
    """The mark is a status of the eligible member's own key and nothing else: the partner's date, object, any count
    and any attribution stay out of the line."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, [("dentist appointment", "deadline", D1)], [("dentist appointment", "deadline", FAR)])
        line = _commitments(m)[0]
        mark = line[len(_plain("dentist appointment", D1)):]
        assert mark == " (contested — unconfirmed which date is current)"
        assert not any(ch.isdigit() for ch in mark) and FAR not in m.recall(U).context


# ---- §4c, INV-OB5: the doctor count is exact and report-only --------------------------------------------------------
def _chain_store(d):
    """Two subject-`user` deadline retirements (the count), beside what it must NOT count: a subject-`user`
    `located_at` chain (another relation) and a superseded deadline whose subject is not `user` (planted: under §4a's
    subject the subject axis refuses a reschedule, so ingest writes no such chain)."""
    m, _ = _mem(d, [("user", "deadline", f"dentist appointment on {D1}")],
                [("user", "deadline", f"haircut appointment on {D2}")],
                [("user", "deadline", f"lease renewal on {FAR}")],
                [("user", "located_at", "Boston")], [("user", "located_at", "Denver")],
                [("dentist appointment", "deadline", D1)], [("haircut appointment", "deadline", D2)])
    old = _edge("e-old", "lease renewal", DAY(20)).model_copy(update={
        "invalidated_at": datetime.now(timezone.utc), "invalidation_reason": "superseded"})
    m.store.add_edge(old)
    m.store.add_edge(_edge("e-new", "lease renewal", DAY(25)).model_copy(update={"supersedes": "e-old"}))
    m.store.close()
    return f"{d}/t.db"


def test_ob5_the_doctor_counts_the_subject_user_chain_exactly_and_writes_nothing():
    with tempfile.TemporaryDirectory() as d:
        path = _chain_store(d)
        before = pathlib.Path(path).read_bytes()
        rep = doctor.diagnose(path)
        assert pathlib.Path(path).read_bytes() == before
        assert rep.counts["obligation_chain_retired"] == 2, rep.counts
        f = [x for x in rep.findings if x.check == "obligations"]
        assert [x.level for x in f] == ["info"] and "u: 2" in f[0].message, f


def test_ob5_a_store_with_no_chain_reports_none():
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *TWO)
        m.store.close()
        rep = doctor.diagnose(f"{d}/t.db")
        assert rep.counts["obligation_chain_retired"] == 0
        assert [x.message for x in rep.findings if x.check == "obligations"] == [
            "no deadline/scope chain with subject `user`"]


# ---- §4a, INV-OB6: the obligation rule is in the prompt the extractor receives ---------------------------------------
def test_ob6_the_obligation_rule_reaches_the_extractor():
    assert RULE in EXTRACT_PROMPT
    with tempfile.TemporaryDirectory() as d:
        _m, llm = _mem(d, [("dentist appointment", "deadline", D1)])
        assert llm.prompts and RULE in llm.prompts[0], llm.prompts
        assert "except an obligation's date, written as above" in llm.prompts[0]
        assert "never\n  give it a day" in llm.prompts[0]


def test_a_direct_assemble_with_no_contested_argument_renders_per_edge():
    """`contested=None` (a direct caller) is the per-edge rendering, so the carrier is what makes the group."""
    with tempfile.TemporaryDirectory() as d:
        m, _ = _mem(d, *RESCHEDULE)
        ctx = proactive.assemble(m.store, U, m.config)[0]
        assert _plain("dentist appointment", D1) in ctx and _plain("dentist appointment", D2) in ctx, ctx


# ---- the 0.29.0 release blockers B1+B2 (research's notes read on fc9cc15, 1eb722a9; stage 1 on 2088d08, 8b0de7d2; the
# owner, 2026-11-02: "Hold; fix B1+B2 first (Recommended)"): the user's dated obligation, in either form, is judged by
# the speaker backstop on its DATE by 0045's resolution per side, and is eligible for any query ----------------------
FORMS = {"subject-user": "user", "subject-named": "dentist appointment"}


def _words(iso):
    d = datetime.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}"


# research's four rows (8b0de7d2): (event, restricted?) — the extractor writes the ISO date whatever words were said
ROWS = {
    "user-words-assistant-echoes-iso": ("USER: My dentist appointment is on {w}.\nASSISTANT: Noted: {d}.", False),
    "user-words-assistant-words": ("USER: My dentist appointment is on {w}.\nASSISTANT: Noted, {w}th.", False),
    "assistant-only-iso": ("USER: When is my dentist appointment?\nASSISTANT: Your dentist appointment is on {d}.", True),
    "assistant-only-words": ("USER: When is my dentist appointment?\nASSISTANT: It is on {w}.", True),
    # neither side says it: not restricted here (it is ungrounded, and never volunteered: 0045 §4b)
    "in-no-turn": ("USER: When is my dentist appointment?\nASSISTANT: Let me check your calendar.", False),
}
USER_STATES = "USER: My dentist appointment is on {d}.\nASSISTANT: Noted."


def _one(d, subject, relation, obj, text):
    """ONE scripted triple from ONE event, so the extractor's form is the only variable (research's probe shape)."""
    llm = Scripted([(subject, relation, obj)])
    m = Memory(llm=llm, config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
    res = m.remember(U, text, date=DAY(-1), context=EvidenceContext.direct())
    return m, res


def _row(row):
    text, want = ROWS[row]
    return text.format(d=D1, w=_words(D1)), want


@pytest.mark.parametrize("form", list(FORMS))
@pytest.mark.parametrize("row", list(ROWS))
def test_b1_the_backstop_judges_an_obligations_date_by_grounding_per_side(row, form):
    """B1: restricted exactly when the assistant's words ground the date and the user's do not, in BOTH forms. At
    2088d08 the named form was never restricted (the user said its name) and the subject-`user` form matched tokens:
    it missed "It is on November 4." and restricted the user's "November 4" echoed as an ISO date."""
    text, want = _row(row)
    with tempfile.TemporaryDirectory() as d:
        m, res = _one(d, FORMS[form], "deadline", D1, text)
        [e] = _deadlines(m)
        assert res["speaker_restricted"] == int(want), (row, form, res)
        assert e.provenance.disclosure == (Disclosure.USE_ONLY if want else Disclosure.MENTIONABLE), (row, form, e)
        if row == "in-no-turn":
            assert e.ungrounded and D1 not in m.recall(U).context, (e, m.recall(U).context)


@pytest.mark.parametrize("row", ["assistant-only-iso", "assistant-only-words"])
def test_b1_an_assistant_only_date_under_a_named_obligation_is_not_volunteered(row):
    """End to end: the briefing never volunteers it as the user's commitment, and a recall marks its origin."""
    text, _want = _row(row)
    with tempfile.TemporaryDirectory() as d:
        m, _res = _one(d, "dentist appointment", "deadline", D1, text)
        assert D1 not in m.recall(U).context, m.recall(U).context
        line = [ln for ln in m.recall(U, "when is the dentist?").context.splitlines() if D1 in ln]
        assert len(line) == 1 and "[unverified-origin; unconfirmed]" in line[0], line


def test_b1_a_user_stated_date_under_a_named_obligation_is_volunteered():
    with tempfile.TemporaryDirectory() as d:
        m, res = _one(d, "dentist appointment", "deadline", D1, USER_STATES.format(d=D1))
        assert res["speaker_restricted"] == 0 and _commitments(m) == [_plain("dentist appointment", D1)], res


def test_b1_another_partys_deadline_keeps_the_every_side_rule():
    """`person:alice`'s deadline is not the user's obligation (schema.is_obligation's `kind:` exclusion, research
    8b0de7d2): its subject is a side, as for any entity triple, so the user saying "Alice" leaves it unrestricted,
    as before this batch (0051 §4b, unchanged here; the general case is its own row)."""
    with tempfile.TemporaryDirectory() as d:
        m, res = _one(d, "person:alice", "deadline", D1,
                      f"USER: When is Alice's thesis due?\nASSISTANT: Alice's thesis is due {D1}.")
        assert res["speaker_restricted"] == 0, res


def test_b1_a_non_obligation_triple_keeps_both_its_sides_judged():
    with tempfile.TemporaryDirectory() as d:
        m, res = _one(d, "person:alice", "located_at", "Berlin",
                      "USER: Where does Alice live these days?\nASSISTANT: Alice lives in Berlin.")
        assert res["speaker_restricted"] == 0, res


@pytest.mark.parametrize("form", list(FORMS))
def test_b2_a_generic_query_reaches_a_commitment_in_either_form(form):
    """B2: 0.28.0's subject-`user` commitment was eligible for every query (ranked by overlap); the named form must be
    too, or "what do I have coming up?" loses every commitment the extractor names."""
    with tempfile.TemporaryDirectory() as d:
        m, _res = _one(d, FORMS[form], "deadline", D1, USER_STATES.format(d=D1))
        assert D1 in m.recall(U, "what do I have coming up?").context


@pytest.mark.parametrize("form", list(FORMS))
def test_b2_an_as_of_recall_reaches_a_commitment_in_either_form(form):
    """_lexical_scored's third caller (asof/recall.py, research 8b0de7d2)."""
    with tempfile.TemporaryDirectory() as d:
        m, _res = _one(d, FORMS[form], "deadline", D1, USER_STATES.format(d=D1))
        assert D1 in m.recall(U, "what do I have coming up?", as_of=datetime.now(timezone.utc)).context


@pytest.mark.parametrize("subject,relation,obj,text,query,match", [
    ("person:alice", "located_at", "Berlin", "USER: Alice lives in Berlin.", "where does alice live?", "Berlin"),
    ("person:alice", "deadline", D1, f"USER: Alice's thesis is due {D1}.", "when is alice's thesis due?", D1)],
    ids=["entity", "another-partys-deadline"])
def test_b2_an_entity_edge_still_needs_a_token_match(subject, relation, obj, text, query, match):
    with tempfile.TemporaryDirectory() as d:
        m, _res = _one(d, subject, relation, obj, text)
        assert match not in m.recall(U, "what do I have coming up?").context
        assert match in m.recall(U, query).context


def test_b2_an_obligation_ranks_as_a_subject_user_fact_does():
    """The scorer gives a named commitment the subject-`user` base at every overlap, 1 + 2*overlap (+1 active), where an
    entity edge takes 3*overlap and needs a match to enter at all."""
    from veracium import graph
    for q in ("what do I have coming up?", "when is the dentist appointment?", "dentist appointment deadline"):
        for subject in FORMS.values():
            with tempfile.TemporaryDirectory() as d:
                m, _res = _one(d, subject, "deadline", D1, USER_STATES.format(d=D1))
                scored, _rel, _by = graph._lexical_scored(m.store, U, q)
                assert len(scored) == 1, (q, subject, scored)
                [(b, ov, e)] = scored
                assert e.active and b == 1 + 2 * ov + 1, (q, subject, b, ov)


@pytest.mark.parametrize("subject,relation,want", [
    ("dentist appointment", "deadline", True), ("Q3 report", "deadline", True),
    ("user", "deadline", False), ("User", "deadline", False), (" user ", "deadline", False),
    ("person:alice", "deadline", False), ("org:acme", "deadline", False), ("Person:Alice", "deadline", False),
    ("dentist appointment", "located_at", False), ("dentist appointment", "scope", False),
    ("dentist appointment", "Deadline", False), ("person:alice", "third_party_claim", False)],
    ids=["named", "q3", "user", "User", "padded-user", "person-ref", "org-ref", "Person-ref", "located_at", "scope",
         "Deadline", "claim"])
def test_is_obligation_over_its_domain(subject, relation, want):
    from veracium.schema import is_obligation
    assert is_obligation(subject, relation) is want


@pytest.mark.parametrize("subject", ["user", "User", " USER ", "dentist appointment", "users", "", "person:alice"],
                         ids=["user", "User", "padded-USER", "named", "users", "empty", "person-ref"])
def test_is_obligation_and_subject_class_name_one_user(subject):
    """Two carriers of "is this the user?": an obligation's subject is one graph.subject_class calls OTHER (0011 E1),
    so the two can never disagree about the user; an entity ref is OTHER and not an obligation."""
    from veracium.graph import subject_class
    from veracium.schema import is_obligation
    other = subject_class(U, subject) == "OTHER"
    assert is_obligation(subject, "deadline") == (other and not subject.startswith("person:")), (subject, other)
