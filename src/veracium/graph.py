"""Graph operations: functional supersession and entity-matched subgraph render.

Pure logic over the store — no LLM, no I/O beyond the store handle — so this is
the offline-testable heart of memory correctness (supersession-with-history is
the category the research found the industry worst at, and where veracium's design
scored best).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from .schema import DEFAULT_RELATIONS, Edge, EvidenceAuthor, Relation


# Filler words that never change a value's meaning. Deliberately tiny: a false
# "same" here silently merges two distinct facts, so anything that can carry
# meaning (prepositions, verbs, qualifiers) stays. my/our/their are kept as
# filler only because edge values are read relative to the edge's subject, so
# first-person and singular-they possessives are redundant; his/her can point
# at a third party ("his assistant" vs "her assistant") and therefore stay
# meaningful — they are NOT filler.
_VALUE_FILLER = {"a", "an", "the", "my", "our", "their", "named", "called"}


def _value_key(text: str) -> tuple[str, ...]:
    """Order-preserving normalization for value equivalence: paraphrases like
    'dog named Ollie' / 'dog Ollie' / 'a dog called Ollie.' compare equal, while
    order-sensitive values ('tea over coffee' vs 'coffee over tea') stay distinct."""
    toks = tuple(w for w in re.findall(r"[a-z0-9]+", text.lower())
                 if w not in _VALUE_FILLER)
    return toks or (text.strip().lower(),)


# T1 absorption bound: the fuller form may carry at most this many tokens beyond
# the shorter one ("cat Miso" over "Miso"). Two genuinely distinct values rarely
# differ by so few tokens while containing each other in order; anything wider
# is left to accumulate (visible, recoverable) rather than risk a false merge.
_ABSORB_MAX_EXTRA = 2


def _subsumes(longer: tuple[str, ...], shorter: tuple[str, ...]) -> bool:
    """True if `shorter` is an ordered subsequence of `longer` with 1..2 extra
    tokens. Ordered, not bag-subset, so the order-sensitivity contract of
    _value_key ('tea over coffee' ≠ 'coffee over tea') survives absorption."""
    if not 0 < len(longer) - len(shorter) <= _ABSORB_MAX_EXTRA:
        return False
    it = iter(longer)
    return all(t in it for t in shorter)


def apply_supersession(store, edge: Edge, relations: dict[str, Relation]) -> None:
    """Persist a new edge with supersession, reinforcement, and absorption:

    - Reinforcement: if an active edge already asserts the same
      (subject, relation, object), refresh its validity instead of adding a
      duplicate — so re-stating a fact keeps it alive (a re-mentioned transient
      state won't lapse) and clears any stale-confirmation flag. "Same" is
      normalized-token equality (see _value_key), so an extractor paraphrase of
      an unchanged value reinforces rather than duplicates. A *less* specific
      restatement of a value we already hold ("Miso" after "cat Miso") also
      reinforces: it is the same evidentiary event, not a new fact.
    - Absorption (T1): a *more* specific form of a prior value ("cat Miso"
      after "Miso", see _subsumes) wins — the shorter prior retires reversibly
      (reason 'absorbed_duplicate', note carries the winner's id). Identity,
      not change: no `supersedes` pointer, and render_edges never shows an
      absorbed value as history. Validity/confidence take the max of the pair;
      the winner keeps its own provenance.
    - Supersession: for a *functional* relation, a new value invalidates the
      prior active value (retained, reason 'superseded'), so history stays queryable.
    - Non-functional relations otherwise accumulate.

    Reinforcement/absorption fire at write time — fresh evidence just arrived —
    which is why they may refresh validity and clear needs_confirmation;
    maintain-time bookkeeping never may.

    Identity merges never cross trust classes: both loops consider only priors
    in the same disclosure class as the incoming edge. Otherwise a third-party
    use_only restatement could retire a user-asserted fact out of assertable
    recall (or refresh its liveness, clear its staleness flag, and inherit its
    confidence) — dedup must not make trust decisions. Cross-class
    restatements accumulate as separate edges, each carrying its own trust;
    the explicit upgrade path for corroborated third-party material is
    confirm()/remember() by the user. (Different-value supersession is
    unaffected: a changed value superseding across classes is correct — the
    old value is stale regardless of who reported the new one.)
    """
    same = _value_key(edge.object)
    priors = [p for p in store.edges(edge.user_id, subject=edge.subject,
                                     relation=edge.relation)
              if p.id != edge.id
              and p.provenance.disclosure == edge.provenance.disclosure]
    for prior in priors:
        pk = _value_key(prior.object)
        if pk == same or _subsumes(pk, same):  # reinforcement
            # valid_from is FIRST-KNOWN and immutable: it is the field the
            # codebase already documents as "when it became true", the field
            # render_edges states to the model as "(since X)", and the field E1
            # clusters on. Overwriting it with the latest restatement made that
            # rendering a false statement in the answer context, not merely lost
            # history. Liveness lives on observed_at, which already means
            # "when veracium recorded this" and is what lifecycle now ages
            # against — so a restatement still refreshes liveness (the lapse
            # argument), it just refreshes the field that means liveness.
            prior.provenance.observed_at = max(prior.provenance.observed_at,
                                               edge.provenance.observed_at)
            prior.provenance.confidence = max(prior.provenance.confidence,
                                              edge.provenance.confidence)
            # M3 (0.4.5): needs_confirmation renders as "confirm before relying
            # on it" — a question addressed to the party who stated the fact.
            # The 0.4.1 guard above compares DISCLOSURE class, and USER and
            # SYSTEM share MENTIONABLE, so a system-authored restatement used to
            # answer a question meant for the user. Same speaker/witness
            # confusion that deferred spec 0001, one layer down. Only evidence
            # from the same author class clears it; confirm() remains the
            # explicit path.
            if (prior.provenance.author_of_evidence
                    == edge.provenance.author_of_evidence):
                prior.needs_confirmation = False
            store.add_edge(prior)
            return
    for prior in priors:
        if _subsumes(same, _value_key(prior.object)):  # absorption
            # the winner is the same fact restated more fully, so it inherits
            # the EARLIEST point at which the fact was known — min, not max
            edge.valid_from = min(edge.valid_from, prior.valid_from)
            edge.provenance.observed_at = max(edge.provenance.observed_at,
                                              prior.provenance.observed_at)
            edge.provenance.confidence = max(edge.provenance.confidence,
                                             prior.provenance.confidence)
            prior.note = ((f"{prior.note}; " if prior.note else "")
                          + f"absorbed_by:{edge.id} (restated as {edge.object!r})")
            store.add_edge(prior)
            store.invalidate_edge(prior.id, edge.valid_from, "absorbed_duplicate")
    rel = relations.get(edge.relation)
    if rel and rel.functional:
        for prior in store.edges(edge.user_id, subject=edge.subject, relation=edge.relation):
            if prior.id != edge.id and _value_key(prior.object) != same:
                store.invalidate_edge(prior.id, edge.valid_from, "superseded")
                edge.supersedes = prior.id
    store.add_edge(edge)


_STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on",
         "for", "and", "or", "s", "does", "did", "what", "who", "when", "where",
         "how", "which", "with", "her", "his", "their", "they", "do", "have",
         # "user" is the implicit owner of a per-user store: it appears in most
         # questions AND is the subject of most edges, so counting it as a match
         # makes every edge look equally relevant — which is precisely how
         # ranking collapsed at scale.
         "user"}

# Crude suffix folding so a question's wording reaches a stored relation:
# "work" must match `works_for`, "pets" must match `has_pet`, "deadlines" must
# match the `deadline` relation. Not a stemmer — just enough morphology to stop
# exact-token matching from failing on ordinary plurals, applied to both sides.
# Deliberately excludes "es": stripping it maps "deadlines"->"deadlin" and so
# stops matching "deadline", i.e. the rule breaks more matches than it makes.
# Known and accepted misses: doubled consonants ("running"/"run") and words
# whose stem ends in s ("address"/"addresses").
_SUFFIXES = ("ing", "ed", "s")


def _stem(w: str) -> str:
    """Fold to a fixed point, never below a 3-character stem.

    Iterating matters: a single pass would map 'addresses'->'address' but
    'address'->'addres', so the two forms would stop matching — a stemmer that
    breaks matches is worse than none. Converging both to 'addre' keeps the
    relation symmetric, which is the only property this needs to have.
    """
    while True:
        for suf in _SUFFIXES:
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                w = w[: -len(suf)]
                break
        else:
            return w


def _tokens(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())
            if w not in _STOP and len(w) > 2}


def subgraph_for_query(store, user_id: str, query: str, *, max_edges: int = 40,
                       coverage_share: float = 0.25) -> list[Edge]:
    """Entity-matched neighborhood: every edge off the user node, plus edges whose
    tokens appear in the query, ranked by how well they match it. This is
    veracium's primary retrieval (the research found it beat similarity search on
    every question type). Includes superseded edges (rendered as history) and
    quarantined edges (rendered flagged) so the caller can show provenance.

    User-subject edges are always *eligible* — that is the "everything off the
    user node" contract, and for a small store they all fit under `max_edges`
    anyway — but eligibility is not ranking. Until 0.4.2 they carried a constant
    score, so once a store grew past `max_edges` the truncation returned
    whichever ones the store listed first (i.e. the oldest), and the query was
    ignored entirely for the subject that owns most facts. On a 1.7k-fact store
    that made recall effectively query-blind; widening the cap only returned
    more old facts. Relevance now decides which ones survive truncation, with
    recency as the tiebreak, and `relation` counts as matchable text so "pet"
    can reach `has_pet`.
    """
    q = _tokens(query)
    scored: list[tuple[int, Edge]] = []
    for e in store.edges(user_id, active_only=False):
        overlap = len(_tokens(f"{e.subject} {e.relation} {e.object} {e.note}") & q)
        if e.subject == "user":
            base = 1 + 2 * overlap      # eligible always; ranked by relevance
        else:
            base = 3 * overlap          # entity edges must match to enter at all
        if base:
            # prefer active over superseded, and closer matches
            scored.append((base + (1 if e.active else 0), e))
    # recency breaks ties: among equally-relevant facts the newer one is the
    # better guess, and it makes truncation deterministic rather than dependent
    # on store insertion order
    # recency tiebreak reads observed_at: "most recently recorded", not
    # "became true earliest" — valid_from is the first-known axis
    scored.sort(key=lambda t: (-t[0], -t[1].provenance.observed_at.timestamp()))
    if len(scored) <= max_edges:
        return [e for _, e in scored]        # nothing to choose between
    return _cover(scored, max_edges, coverage_share)


def _cover(scored: list[tuple[int, Edge]], max_edges: int,
           coverage_share: float) -> list[Edge]:
    """Fill most of the budget by pure relevance, reserve the tail for time
    coverage.

    Pure top-k has no coverage term, so when many facts share vocabulary the
    selection collapses onto whichever period dominates — a question spanning
    months can be answered from a single day's records, and a question about an
    interval gets one endpoint. Reserving a slice of the budget for periods not
    already represented costs a few of the least-relevant head slots and buys
    the ability to see across time.

    Clustering is on `valid_from` (the day a fact became true), because that is
    the only temporal key always available: session identity is a host concept
    that most callers never supply, so a session-based rule would be
    unimplementable outside a benchmark harness.

    Deliberately conservative:
      * the head is filled by relevance alone, so the most relevant facts are
        never displaced by coverage;
      * coverage only spends the reserved tail, and only on candidates that
        already passed the relevance filter;
      * with fewer candidates than the budget this never runs at all, so small
        stores behave exactly as before.

    It optimizes *coverage*, not distinct-day count — the day spread is a
    diagnostic of the problem, and selecting to maximise it would be selecting
    to look good on the diagnostic.
    """
    reserve = int(max_edges * coverage_share)
    head, tail = max_edges - reserve, []
    chosen = [e for _, e in scored[:head]]
    seen_days = {e.valid_from.date() for e in chosen}
    rest = scored[head:]
    # first pass: highest-scoring candidate from each period not yet present
    for _, e in rest:
        if len(chosen) + len(tail) >= max_edges:
            break
        day = e.valid_from.date()
        if day not in seen_days:
            tail.append(e)
            seen_days.add(day)
    # backfill any unused reserve by relevance, so coverage never costs volume
    if len(chosen) + len(tail) < max_edges:
        picked = {id(e) for e in tail}
        for _, e in rest:
            if len(chosen) + len(tail) >= max_edges:
                break
            if id(e) not in picked:
                tail.append(e)
    return chosen + tail


def _outcome_note(e: Edge) -> str:
    """Outcome aggregates rendered as information for the reader — never
    gating: '(in use: 5×, 2 confirmed, 1 corrected)'. Unreviewed uses show
    only in the total (completion is not confirmation)."""
    if not e.times_used:
        return ""
    reviewed = [f"{n} {k}" for k, n in sorted(e.outcome_counts.items())
                if k != "unreviewed" and n > 0]
    detail = (", " + ", ".join(reviewed)) if reviewed else ""
    return f" (in use: {e.times_used}×{detail})"


# Origin labels for `use_only` material. Derived from provenance rather than
# hardcoded, because the string reaches the model as context and a CONFIDENTLY
# WRONG origin is worse than a missing one.
#
# Output is byte-identical to the previous hardcoded string for every author
# that can reach `use_only` today (THIRD_PARTY-authored, and USER/SYSTEM content
# capped by derived_from=THIRD_PARTY — in both cases the claim originates with a
# third party, so "third-party-reported" is accurate).
#
# It exists because a FOURTH author class is proposed (spec 0001,
# EvidenceAuthor.ASSISTANT, deferred). Under that spec every assistant edge sits
# at use_only, and the old hardcoded string would have told the model
# "third-party-reported" about assistant-generated text — an affirmatively false
# origin, in the one release whose entire purpose is stopping hosts from
# mislabelling assistant content. `_ORIGIN_LABELS` has no entry for a new author
# class, and `tests/test_render_origin.py` fails loudly if one appears without
# one. That converts a note in a deferred spec into a tripwire.
_ORIGIN_LABELS: dict[EvidenceAuthor, str] = {
    EvidenceAuthor.THIRD_PARTY: "third-party-reported",
    # USER/SYSTEM only reach use_only via derived_from=THIRD_PARTY, i.e. the
    # claim is a third party's and the author is relaying it
    EvidenceAuthor.USER: "third-party-reported",
    EvidenceAuthor.SYSTEM: "third-party-reported",
}


def _origin_label(e: Edge) -> str:
    """Who this unverified material came from, in the model's words."""
    label = _ORIGIN_LABELS.get(e.provenance.author_of_evidence)
    if label is None:
        # Fail SAFE, not confidently: an unlabelled author class must not
        # inherit another class's origin string.
        return "unverified-origin"
    return label


def render_edges(edges: list[Edge]) -> str:
    """Render edges as provenance-carrying lines for a prompt. Quarantined claims
    are fenced with an explicit never-assert marker; superseded edges show their
    validity range so history is visible without polluting the current value."""
    lines = []
    for e in edges:
        if e.invalidation_reason == "absorbed_duplicate":
            # an absorbed value is the SAME fact as its active winner, not a
            # prior value of it — rendering it as history would show identity
            # as change. Still queryable via the store/Recall.edges.
            continue
        who = "" if e.subject == "user" else f"{e.subject} "
        note = f" — {e.note}" if e.note else ""
        if e.quarantined:
            lines.append(f"[UNVERIFIED third-party claim, never assert as fact] "
                         f"{e.subject} claims: {e.relation} {e.object}{note} ({e.valid_from.date()})")
        elif not e.active:
            lines.append(f"{who}{e.relation}: {e.object}{note} "
                         f"(SUPERSEDED {e.valid_from.date()}→{e.invalidated_at.date() if e.invalidated_at else '?'})")
        else:
            stale = " [possibly stale — confirm before relying on it]" if e.needs_confirmation else ""
            tp = f" [{_origin_label(e)}; unconfirmed]" if e.use_only else ""
            lines.append(f"{who}{e.relation}: {e.object}{note} (since {e.valid_from.date()})"
                         f"{_outcome_note(e)}{tp}{stale}")
    return "\n".join(lines)
