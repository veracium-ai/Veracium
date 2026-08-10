"""Proactive recall — the session-start briefing (`recall(user_id)`; no query).

Answers "what should I know before starting?" without being asked: dated
commitments coming due (or overdue), facts flagged possibly-stale that a
natural conversation could confirm, the user's current transient state
(worth a follow-up: "how's the flu?"), and recent interaction history.

Security model — proactive surfacing IS volunteering, so `Disclosure` gates
it: only MENTIONABLE facts may appear. `use_only` material ("may shape
behavior; never volunteered") and quarantined claims never surface here —
an unprompted "by the way, someone says you owe $900" is exactly the
volunteering the disclosure tiers exist to prevent. Query-driven recall
still shows claims under the never-assert fence; the difference is the user
asked. Outcome episodes (structured records) never surface either.

Deterministic and LLM-free, like all of veracium's read-path logic outside
the wiki: sections are priority-ordered, and a token budget trims from the
bottom (recent history first, commitments last)."""

from __future__ import annotations

import re
from datetime import date as _date
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from .graph import collapse_for_render
from .schema import Edge, Episode, Volatility

_ISO_DATE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


def _dates_in(text: str) -> list[_date]:
    out = []
    for m in _ISO_DATE.findall(text):
        try:
            out.append(_date.fromisoformat(m))
        except ValueError:
            continue
    return out


def assemble(store, user_id: str, config, *, now: Optional[datetime] = None,
             token_budget: Optional[int] = None,
             est: Callable[[str], int] = lambda s: max(1, len(s) // 4)
             ) -> tuple[str, list[Edge], list[Episode], bool]:
    """Build the briefing. Returns (context, edges, episodes, truncated).

    Sections, in priority order (budget trims lower sections first):
      1. DATED COMMITMENTS — active mentionable edges whose object/note carries
         an ISO date that is overdue or within `proactive_deadline_window_days`.
      2. CONFIRM WHEN NATURAL — active mentionable edges flagged
         possibly-stale ("still at Acme?").
      3. CURRENT CONTEXT — active mentionable transient/ephemeral facts
         (current state worth a follow-up).
      4. RECENT HISTORY — grounded interaction episodes from the last
         `proactive_recent_days` days (never outcome records, never
         third-party-influenced episodes).
    """
    now = now or datetime.now(timezone.utc)
    today = now.date()
    window = today + timedelta(days=config.proactive_deadline_window_days)
    recent_cutoff = today - timedelta(days=config.proactive_recent_days)

    commitments: list[tuple[str, Edge]] = []
    confirms: list[tuple[str, Edge]] = []
    current: list[tuple[str, Edge]] = []
    seen: set[str] = set()

    # specs/0012 I8: collapse strictly-redundant duplicates BEFORE categorization
    # (a suppressed member is category-identical to its survivor: distinct notes,
    # volatilities and flags all surface by the predicate). The info labels carry
    # the truthful earliest-since and the ×N flagged count.
    surfaced, _c_info = collapse_for_render(list(store.edges(user_id)))
    # volunteering gate: active + assertable (mentionable) only
    for e in surfaced:
        if not e.assertable:
            continue
        dates = _dates_in(e.object + " " + e.note)
        due = [d for d in dates if d <= window]
        if due:
            d = min(due)
            flag = f" (OVERDUE — was due {d})" if d < today else f" (due {d})"
            commitments.append((f"{e.relation}: {e.object}{flag}", e))
            seen.add(e.id)
            continue
        if e.needs_confirmation:
            xn = _c_info.get(e.id, {}).get("flagged_hidden", 0)
            tail = f" (×{xn + 1} restatements need confirmation)" if xn else ""
            confirms.append((f"{e.relation}: {e.object} — confirm when natural "
                             f"(unrefreshed since {e.provenance.observed_at.date()}){tail}", e))
            seen.add(e.id)
            continue
        if e.volatility in (Volatility.TRANSIENT, Volatility.EPHEMERAL):
            since_dt = _c_info.get(e.id, {}).get("since", e.valid_from)
            current.append((f"{e.relation}: {e.object} "
                            f"(since {since_dt.date()} — worth a follow-up)", e))
            seen.add(e.id)

    recents: list[tuple[str, Episode]] = []
    for ep in store.episodes(user_id):
        if ep.kind == "outcome" or ep.provenance.third_party_influenced:
            continue
        try:
            ep_date = _date.fromisoformat(ep.date)
        except ValueError:
            continue
        if ep_date >= recent_cutoff:
            recents.append((f"[{ep.date}] {ep.summary}", ep))
    recents = recents[-config.max_recent_episodes:]

    sections = [("## DATED COMMITMENTS", commitments),
                ("## CONFIRM WHEN NATURAL", confirms),
                ("## CURRENT CONTEXT", current),
                ("## RECENT HISTORY", recents)]

    remaining = token_budget if token_budget is not None else None
    truncated = False
    parts: list[str] = []
    sel_edges: list[Edge] = []
    sel_eps: list[Episode] = []
    for header, items in sections:
        if not items:
            continue
        kept: list[str] = []
        header_cost = est(header)
        for line, unit in items:
            cost = est(line) + (header_cost if not kept else 0)
            if remaining is not None and cost > remaining and (parts or kept):
                truncated = True
                break
            kept.append(line)
            if remaining is not None:
                remaining -= cost
            (sel_edges if isinstance(unit, Edge) else sel_eps).append(unit)
        if kept:
            parts.append(header + "\n" + "\n".join(kept))
        if truncated:
            break

    context = "\n\n".join(parts).strip() or "(nothing needs attention)"
    return context, sel_edges, sel_eps, truncated
