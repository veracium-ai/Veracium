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
    from .budgets import clamp_item as _clamp, est_tokens as _est0
    _cap = getattr(config, "item_cap_tokens", 512)
    comp_clamped = [0]                         # composition-time clamps are truncation
    #                                            EVENTS and must signal (R-impl2-1)

    def _obj(e, content_cap=None):
        # content clamp BEFORE framing: the due/confirm instructions render after
        # the object, so a whole-line tail clamp would sever them (I10c)
        cap = content_cap if content_cap is not None else max(16, _cap - 48)
        out = _clamp(e.object, cap)
        if content_cap is None and out != e.object:
            comp_clamped[0] += 1
        return out

    for e in surfaced:
        if not e.assertable:
            continue
        dates = _dates_in(e.object + " " + e.note)
        due = [d for d in dates if d <= window]
        # specs/0012 I10f: class assignment is a PRECEDENCE mirroring the surface
        # order — a flagged edge classifies into its WARNING tier even when it also
        # carries a due date (flagged > commitment); it renders ONCE.
        if e.needs_confirmation:
            xn = _c_info.get(e.id, {}).get("flagged_hidden", 0)
            tail = f" (×{xn + 1} restatements need confirmation)" if xn else ""
            confirms.append((f"{e.relation}: {_obj(e)} — confirm when natural "
                             f"(unrefreshed since {e.provenance.observed_at.date()}){tail}", e))
            seen.add(e.id)
            continue
        if due:
            d = min(due)
            flag = f" (OVERDUE — was due {d})" if d < today else f" (due {d})"
            commitments.append((f"{e.relation}: {_obj(e)}{flag}", e))
            seen.add(e.id)
            continue
        if e.volatility in (Volatility.TRANSIENT, Volatility.EPHEMERAL):
            since_dt = _c_info.get(e.id, {}).get("since", e.valid_from)
            current.append((f"{e.relation}: {_obj(e)} "
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

    # specs/0012 I10b: deterministic within-section order — commitments nearest-due
    # first, warnings most-overdue first (ties: observed_at then id); items clamped at
    # the cap (I10a) with framing intact (I10c).
    from .budgets import clamp_item
    cap = getattr(config, "item_cap_tokens", 512)

    def _due_key(pair):
        text, e = pair
        ds = _dates_in(e.object + " " + e.note)
        return (min(ds) if ds else today, e.provenance.observed_at, e.id)

    commitments.sort(key=_due_key)
    confirms.sort(key=lambda pair: (pair[1].provenance.observed_at, pair[1].id))
    # commitments/confirms/current already content-clamped at composition (labels
    # at line end survive); recents are front-framed so a tail clamp is safe
    recents = [(clamp_item(t, ep), e) for (t, e), ep in
               ((pair, cap) for pair in recents)]
    sections = [("## DATED COMMITMENTS", commitments),
                ("## CONFIRM WHEN NATURAL", confirms),
                ("## CURRENT CONTEXT", current),
                ("## RECENT HISTORY", recents)]

    # specs/0012 I10: proactive is ALWAYS budgeted — a direct caller that omits
    # token_budget gets the validated config default, never unbounded (R-impl2-1).
    if token_budget is None:
        token_budget = getattr(config, "proactive_default_budget_tokens", 1200)
    from .budgets import validate_budget
    validate_budget("proactive", token_budget,
                    getattr(config, "group_heading_allowance_tokens", 48))
    # specs/0012 I10b/I10f: ADMISSION runs in the precedence order (warnings above
    # commitments above context above history), independent of the §4c DISPLAY order;
    # the report marker is reserved off the top; the first admitted item is clamped
    # TO FIT rather than admitted oversized; every drop/clamp is counted and reported.
    from .budgets import REPORT_RESERVE, clamp_item as _ci, est_tokens as _et
    truncated = False
    sel_edges: list[Edge] = []
    sel_eps: list[Episode] = []
    admitted: dict[str, list[str]] = {h: [] for h, _ in sections}
    dropped: dict[str, int] = {h: 0 for h, _ in sections}
    n_clamped = 0
    if token_budget is None:
        for header, items in sections:
            for line, unit in items:
                admitted[header].append(line)
                (sel_edges if isinstance(unit, Edge) else sel_eps).append(unit)
    else:
        remaining = token_budget - REPORT_RESERVE
        precedence = ["## CONFIRM WHEN NATURAL", "## DATED COMMITMENTS",
                      "## CURRENT CONTEXT", "## RECENT HISTORY"]
        by_header = dict(sections)
        first_admitted = False
        for header in precedence:
            items = by_header.get(header, [])
            if not items:
                continue
            if header == "## RECENT HISTORY":
                items = list(reversed(items))              # NEWEST first under budget
            header_cost = est(header) + 1
            for line, unit in items:
                cost = est(line) + 1 + (header_cost if not admitted[header] else 0)
                if cost > remaining:
                    if not first_admitted and remaining > header_cost + 24:
                        if isinstance(unit, Edge):
                            # RECOMPOSE with tighter content — a whole-line tail clamp
                            # would sever the end-positioned due/confirm framing (I10c)
                            tight = _obj(unit, max(8, remaining - header_cost - 32))
                            line = line.replace(_obj(unit), tight, 1) \
                                if _obj(unit) in line else _ci(line, remaining - header_cost - 1)
                        else:
                            line = _ci(line, remaining - header_cost - 1)
                        cost = est(line) + 1 + header_cost
                        n_clamped += 1
                        if cost > remaining:
                            dropped[header] += 1
                            continue
                    else:
                        dropped[header] += 1
                        continue
                admitted[header].append(line)
                remaining -= cost
                first_admitted = True
                (sel_edges if isinstance(unit, Edge) else sel_eps).append(unit)
        if admitted["## RECENT HISTORY"]:
            admitted["## RECENT HISTORY"].reverse()        # render chronologically
    n_dropped = sum(dropped.values())
    truncated = bool(n_dropped or n_clamped or comp_clamped[0])

    parts = [header + "\n" + "\n".join(admitted[header])
             for header, _ in sections if admitted[header]]
    context = "\n\n".join(parts).strip() or "(nothing needs attention)"
    if truncated:
        from .budgets import bounded_count as _bc          # bounded-width (R9-2)
        context += (f"\n[budget: dropped {_bc(dropped['## CONFIRM WHEN NATURAL'])} warnings / "
                    f"{_bc(dropped['## DATED COMMITMENTS'])} commitments / "
                    f"{_bc(dropped['## CURRENT CONTEXT'])} context / "
                    f"{_bc(dropped['## RECENT HISTORY'])} history / "
                    f"{_bc(n_clamped + comp_clamped[0])} clamped]")
    return context, sel_edges, sel_eps, truncated
