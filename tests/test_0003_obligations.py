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
