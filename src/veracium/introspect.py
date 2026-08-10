"""introspect(): the formatted transparency view — "what do you know about me,
and where did it come from?"

The raw material has always been exposed (`recall().edges/.episodes` with full
provenance, `export_memory()` as the complete right-to-know dump); this is the
convenience layer over it, for hosts that want to show a user their memory
without writing the aggregation themselves. LLM-free, deterministic, store-only.

Modes:
  summary     counts only — by relation, by evidence author, by disclosure
              tier, lifecycle state, retired history by reason, episodes.
  categories  summary plus the facts themselves, grouped by relation and
              rendered with their provenance markers (render_edges), so
              unverified claims appear exactly as recall would flag them.
"""

from __future__ import annotations

from .graph import render_edges


def _count(counter: dict, key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def _wiki_compile_record(store, user_id: str) -> dict:
    """specs/0012 §4c(iv): read `get_wiki()` (never recompile, never mutate) and parse
    the frozen marker grammar. status: ok | absent | legacy | malformed."""
    from .budgets import parse_compile_marker
    from .compile import _split_envelope
    cached = store.get_wiki(user_id)
    if cached is None:
        return parse_compile_marker(None)
    return parse_compile_marker(_split_envelope(cached[0])[1])


def report(store, user_id: str, *, mode: str = "summary") -> dict:
    """Aggregate one user's memory into a JSON-able transparency report."""
    if mode not in ("summary", "categories"):
        raise ValueError(f"unknown introspect mode {mode!r} (summary | categories)")

    edges = store.edges(user_id, active_only=False, include_quarantined=True)
    episodes = store.episodes(user_id)

    active = [e for e in edges if e.active]
    facts = [e for e in active if not e.quarantined]
    claims = [e for e in active if e.quarantined]

    by_relation: dict[str, int] = {}
    by_author: dict[str, int] = {}
    by_disclosure: dict[str, int] = {}
    retired: dict[str, int] = {}
    for e in facts:
        _count(by_relation, e.relation)
    for e in active:
        _count(by_author, e.provenance.author_of_evidence.value)
        _count(by_disclosure, "quarantined" if e.quarantined
               else "use_only" if e.use_only else "mentionable")
    for e in edges:
        if not e.active:
            _count(retired, e.invalidation_reason or "unknown")

    # first/last OBSERVED would be wrong from observed_at alone: it is max()ed
    # on restatement, so "first" would report the latest recording. The
    # first-known axis is valid_from.
    firsts = [e.valid_from for e in edges]
    lasts = [e.provenance.observed_at for e in edges]
    out = {
        "user_id": user_id,
        "facts": len(facts),
        "unverified_claims": len(claims),
        # specs/0012 R11-5 (frozen public schema): the cached wiki's authoritative
        # compile-drop record, parsed from the marker — VERBATIM in marker_line, and
        # ONLY the cached record (no current-store hypothetical; non-mutating).
        "wiki_compile_record": _wiki_compile_record(store, user_id),
        "by_relation": dict(sorted(by_relation.items())),
        "by_author": dict(sorted(by_author.items())),
        "by_disclosure": dict(sorted(by_disclosure.items())),
        "needs_confirmation": sum(1 for e in facts if e.needs_confirmation),
        "in_use": sum(1 for e in facts if e.times_used),
        "retired": dict(sorted(retired.items())),  # superseded history, disputes, absorbed dups
        "episodes": {"interaction": sum(1 for ep in episodes if ep.kind != "outcome"),
                     "outcome": sum(1 for ep in episodes if ep.kind == "outcome")},
        # specs/0010 X13: the recovery-pending consolidation ops observed now
        # ({CLAIMED, GENERATING, OUTPUTS_DURABLE}). Distinct from consolidate()'s
        # per-pass `recovered` count — a live op is pending, never recovered.
        "consolidation_pending": len(store.pending_consolidations(user_id)),
        "first_known": min(firsts).isoformat() if firsts else None,
        "last_recorded": max(lasts).isoformat() if lasts else None,
    }
    if mode == "categories":
        cats: dict[str, list[str]] = {}
        for e in sorted(active, key=lambda e: (e.relation, e.valid_from)):
            line = render_edges([e])
            if line:
                cats.setdefault(e.relation, []).append(line)
        out["categories"] = cats
    return out
