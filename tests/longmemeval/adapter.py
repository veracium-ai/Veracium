"""LongMemEval V1-S loader with the oracle-annotation firewall.

The dataset ships answer-bearing metadata inline (`has_answer` on turns,
`answer_session_ids`, `question_type`, gold `answer`). Ingesting a raw turn
dict would leak "this turn contains the answer" straight into the extractor.
So the loader splits every instance in two:

  Item      model-facing ONLY — question, question date, and transcripts built
            from (role, content) pairs. Nothing else can reach a provider.
  Eval      evaluation-only — gold answer, has_answer turn indices,
            answer_session_ids, question_type. Never passed to a provider,
            never part of a cache key.

Held separately (not one object with "private" fields) so a leak is a type
error rather than an attention lapse. `tests/test_longmemeval.py` asserts it.

Dataset is NOT committed: ~/Datasets/longmemeval/ (gated-corpus convention).
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path.home() / "Datasets" / "longmemeval"
S_FILE = DATA_DIR / "longmemeval_s_cleaned.json"
ORACLE_FILE = DATA_DIR / "longmemeval_oracle.json"

QUESTION_TYPES = ("single-session-user", "single-session-assistant",
                  "single-session-preference", "temporal-reasoning",
                  "knowledge-update", "multi-session")

# "2023/05/20 (Sat) 02:21" -> "2023-05-20T02:21:00"; lexicographic order on the
# raw string is already chronological (YYYY/MM/DD), so sorting needs no parse —
# but veracium's _event_dt wants ISO, and the time component is what makes
# same-day ordering unambiguous (spec §1 gate 3).
_DATE_RE = re.compile(r"(\d{4})/(\d{2})/(\d{2})\s*\([A-Za-z]{3}\)\s*(\d{2}):(\d{2})")


def _day(stamp: str) -> str:
    """Day key: the granularity at which the benchmark treats dates."""
    return stamp.strip().split(" ")[0]


def to_iso(stamp: str) -> str:
    m = _DATE_RE.match(stamp.strip())
    if not m:
        raise ValueError(f"unparseable benchmark timestamp: {stamp!r}")
    y, mo, d, h, mi = m.groups()
    return f"{y}-{mo}-{d}T{h}:{mi}:00"


@dataclass(frozen=True)
class Turn:
    """One attributable conversational turn. Carries no oracle annotation."""
    role: str          # "user" | "assistant"
    content: str
    index: int         # position within the session, for evidence_ref linkage


@dataclass(frozen=True)
class Session:
    session_id: str    # benchmark id; NOT unique within an instance (see below)
    stamp: str         # raw benchmark timestamp (kept verbatim for the record)
    iso: str           # ISO form handed to remember(date=...)
    turns: tuple[Turn, ...]
    occurrence: int = 0   # 0 unless this id repeats in the instance

    @property
    def iso_day(self) -> str:
        """What reaches `remember(date=...)`: veracium's date parameter is
        day-granular (prompts.date_context parses it with date.fromisoformat).
        The full timestamp still drives ingestion ORDER and lives in the run
        record — but day-level is also the benchmark's own date semantics, so
        nothing is lost that the data actually guarantees."""
        return self.iso[:10]

    @property
    def ref(self) -> str:
        """Unique within the instance — used for evidence_ref/cache identity."""
        return self.session_id if not self.occurrence \
            else f"{self.session_id}~{self.occurrence}"


@dataclass(frozen=True)
class Item:
    """Model-facing half. Everything here may reach a provider."""
    question_id: str
    question: str
    question_date: str      # raw benchmark stamp; official prompt shows it verbatim
    sessions: tuple[Session, ...]   # already in official (date-sorted) order
    repeated_session_ids: tuple[str, ...] = ()   # the disclosed quirk, per instance
    same_day_later_sessions: int = 0   # same day as the question, later clock time


@dataclass(frozen=True)
class Eval:
    """Evaluation-only half. Nothing here may reach a provider."""
    question_id: str
    question_type: str
    answer: str
    answer_session_ids: tuple[str, ...]
    # (session_id, turn_index) of every turn flagged has_answer
    evidence_turns: tuple[tuple[str, int], ...] = field(default_factory=tuple)

    @property
    def is_abstention(self) -> bool:
        return self.question_id.endswith("_abs")


class LoaderError(Exception):
    """Structural problem with an instance. On the canonical run the caller
    aborts rather than silently shrinking the 500-item denominator (spec §10)."""


def _build(raw: dict) -> tuple[Item, Eval]:
    sids = raw["haystack_session_ids"]
    dates = raw["haystack_dates"]
    sessions_raw = raw["haystack_sessions"]
    qid = raw["question_id"]
    if not (len(sids) == len(dates) == len(sessions_raw)):
        raise LoaderError(f"{qid}: misaligned haystack "
                          f"(ids={len(sids)} dates={len(dates)} sessions={len(sessions_raw)})")

    # 13/500 S instances repeat a session id — same content, two different
    # dates (haystack-construction artifact). We do NOT reject: dropping 2.6%
    # of the benchmark is worse than disclosing the quirk. Both dated
    # occurrences are ingested positionally (the faithful reading of the three
    # parallel lists) and disambiguated via Session.ref.
    # KNOWN DEVIATION, recorded per run: the official generation pipeline keys
    # `corpusid2date`/`corpusid2entry` by session id, so a repeated id
    # collapses there (last date wins). Ingesting both is strictly more
    # context; since the content is identical, in veracium the second
    # occurrence reinforces the first (same value, later date) rather than
    # adding facts — so the practical delta is a liveness refresh, not new
    # knowledge. Counted in the manifest either way.
    seen: dict[str, int] = {}
    sessions, evidence = [], []
    for sid, stamp, turns_raw in zip(sids, dates, sessions_raw):
        turns = []
        for i, t in enumerate(turns_raw):
            role = str(t.get("role", "")).strip()
            if role not in ("user", "assistant"):
                raise LoaderError(f"{qid}/{sid}: unexpected turn role {role!r}")
            # ONLY role + content cross into the model-facing structure
            turns.append(Turn(role=role, content=str(t.get("content", "")), index=i))
            if t.get("has_answer"):
                evidence.append((sid, i))
        occ = seen.get(sid, 0)
        seen[sid] = occ + 1
        sessions.append(Session(session_id=sid, stamp=stamp, iso=to_iso(stamp),
                                turns=tuple(turns), occurrence=occ))

    # Official order: run_generation.py sorts retrieved chunks by date; the
    # stamps sort chronologically as strings (YYYY/MM/DD ... HH:MM). Ties keep
    # dataset order (Python's sort is stable) — the documented stable rule.
    sessions.sort(key=lambda s: s.stamp)
    q_stamp = raw["question_date"]
    # Precedence invariant at DAY granularity — the benchmark's own semantics.
    # Measured on the S file: 0 sessions fall on a later DAY than the question,
    # but 1475 sessions across 76 instances carry a same-day LATER CLOCK TIME
    # (question 10:15, session 22:57). The official pipeline only sorts by these
    # stamps and never asserts precedence, so treating clock time as
    # authoritative would impose a stronger temporal reading than the data
    # supports and would reject 15% of instances. Same-day sessions are history;
    # a later DAY is a real structural violation and still aborts.
    if sessions and _day(max(s.stamp for s in sessions)) > _day(q_stamp):
        raise LoaderError(f"{qid}: session dated after the question day "
                          f"({max(s.stamp for s in sessions)} > {q_stamp})")
    same_day_later = sum(1 for s in sessions
                         if _day(s.stamp) == _day(q_stamp) and s.stamp > q_stamp)

    item = Item(question_id=qid, question=raw["question"], question_date=q_stamp,
                sessions=tuple(sessions),
                repeated_session_ids=tuple(sorted(k for k, v in seen.items() if v > 1)),
                same_day_later_sessions=same_day_later)
    ev = Eval(question_id=qid, question_type=raw["question_type"],
              answer=raw["answer"],
              answer_session_ids=tuple(raw.get("answer_session_ids") or ()),
              evidence_turns=tuple(evidence))
    return item, ev


def load(path=S_FILE, *, strict: bool = True) -> tuple[list[Item], dict[str, Eval], dict]:
    """Returns (items, evals_by_qid, manifest). `strict` aborts on any
    structural failure (canonical runs); False collects and reports them
    (pilot wiring diagnosis only, non-canonical)."""
    path = Path(path)
    raw = json.loads(path.read_text())
    items, evals, rejects = [], {}, []
    for r in raw:
        try:
            item, ev = _build(r)
        except LoaderError as e:
            if strict:
                raise
            rejects.append(str(e))
            continue
        items.append(item)
        evals[item.question_id] = ev

    session_refs = sum(len(i.sessions) for i in items)
    unique_sessions = {s.session_id for i in items for s in i.sessions}
    turn_refs = sum(len(s.turns) for i in items for s in i.sessions)
    manifest = {
        "path": str(path), "instances": len(items),
        "rejected": len(rejects), "rejections": rejects[:20],
        "session_refs": session_refs, "unique_sessions": len(unique_sessions),
        "turn_refs": turn_refs,
        "types": {t: sum(1 for e in evals.values() if e.question_type == t)
                  for t in QUESTION_TYPES},
        "abstention_items": sum(1 for e in evals.values() if e.is_abstention),
        # disclosed deviation (see _build): instances where a session id repeats
        "instances_with_repeated_session_ids":
            sum(1 for i in items if i.repeated_session_ids),
        # day-granularity precedence: same-day-later-clock sessions are history
        "same_day_later_sessions": sum(i.same_day_later_sessions for i in items),
        "instances_with_same_day_later": sum(1 for i in items
                                             if i.same_day_later_sessions),
    }
    return items, evals, manifest


# -- pilot sampling (spec §8: minimum-guaranteed, not proportional) -----------

def stratified_pilot(items, evals, *, per_type: int = 6, min_abs: int = 8,
                     seed: int = 0) -> list[Item]:
    """At least `per_type` items of every question type and `min_abs`
    abstention items; grows past any nominal size to satisfy both. Also
    guarantees multi-session-dated coverage by construction (knowledge-update
    and temporal-reasoning are types, so they are always represented)."""
    rng = random.Random(seed)
    by_type: dict[str, list] = {t: [] for t in QUESTION_TYPES}
    abstentions = []
    for it in items:
        ev = evals[it.question_id]
        (abstentions if ev.is_abstention else by_type[ev.question_type]).append(it)

    picked: dict[str, Item] = {}
    for t, pool in by_type.items():
        for it in rng.sample(pool, min(per_type, len(pool))):
            picked[it.question_id] = it
    for it in rng.sample(abstentions, min(min_abs, len(abstentions))):
        picked[it.question_id] = it
    return sorted(picked.values(), key=lambda i: i.question_id)
