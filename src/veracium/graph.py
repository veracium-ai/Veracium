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

from . import authority
from .schema import (DEFAULT_RELATIONS, Edge, EvidenceAuthor, Relation,
                     SupersessionPlan, SupersessionRefusalDraft)
from .store.base import PLAN_STALE


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

    - Reinforcement (specs/0012, Design 1): if an active same-class edge already
      asserts the same (subject, relation, object), the incoming restatement is
      PERSISTED as its own edge with its own provenance, and the prior is left
      byte-untouched — reinforcement transfers NOTHING (not `observed_at`, not
      `confidence`, not `valid_from`). The fact stays live *through the new
      edge* (each edge ages against its own `observed_at`), the persisted edge
      IS the attribution of the contributing source (closes finding M9), and a
      restatement can no longer silently renew a fact's currency or raise its
      confidence (the measured 0012 §1 bypass). "Same" is normalized-token
      equality (see _value_key); a *less* specific restatement of a value we
      already hold ("Miso" after "cat Miso") is the same evidentiary event and
      takes this branch too — it must never fall through to absorption or
      functional contention (0012 I6).
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
    # specs/0003 §4f: the WHOLE outcome is applied as one atomic, CAS-linearized plan.
    # `apply_supersession` computes a plan from a store READ; the Store revalidates the
    # scope `expected_state` inside the transaction and applies all-or-nothing, or returns
    # PLAN_STALE (a concurrent write changed the state the plan assumed) and we recompute.
    op_id = f"sup-{edge.id}"
    for _ in range(_MAX_PLAN_ATTEMPTS):
        plan = _build_supersession_plan(store, edge, relations, op_id)
        result = store.apply_supersession_plan(plan)
        if result is not PLAN_STALE:
            return
    raise RuntimeError(
        f"apply_supersession_plan kept returning PlanStale for edge {edge.id!r} after "
        f"{_MAX_PLAN_ATTEMPTS} attempts — the (user, subject, relation) scope is being "
        f"mutated faster than one supersession can commit (specs/0003 §4f)")


_MAX_PLAN_ATTEMPTS = 16


def _build_supersession_plan(store, edge: Edge, relations: dict[str, Relation],
                             op_id: str) -> SupersessionPlan:
    """Compute the plan for one incoming edge from a store read (specs/0003 §4f). Pure —
    it reads and returns a plan, it does not mutate; the Store applies it atomically."""
    same = _value_key(edge.object)
    # The scope the plan reasons about and the CAS token it carries: ALL active edges of
    # this (user, subject, relation), incl. quarantined — the same set the Store recomputes.
    scope = store.edges(edge.user_id, subject=edge.subject, relation=edge.relation,
                        active_only=True, include_quarantined=True)
    expected = authority.scope_fingerprint(scope)
    same_class = [p for p in scope
                  if p.id != edge.id
                  and p.provenance.disclosure == edge.provenance.disclosure]

    # Reinforcement (specs/0012 §4a, Design 1): an active same-class prior asserts the
    # same-or-subsuming value. The branch KEEPS its guard predicate and position (before
    # absorption, before the functional branch — deleting it would mis-route a SUBSUMED
    # value like "Miso" after "cat Miso" into functional contention, 0012 I6) but its
    # ACTION is persist-incoming-untouched: the restatement is stored with byte-unchanged
    # provenance (I1), the prior is not read-modified-written (I2 — the old max() transfers
    # are deleted, not relocated; a restatement can no longer renew currency or raise
    # confidence, 0012 §1/I5), and nothing else happens — no upsert, no invalidation, no
    # refusal, no supersedes pointer (I6). needs_confirmation is untouched trivially
    # (specs/0008 — only confirm() clears; the prior is not written at all, I4). The
    # persisted edge is the attribution of the contributing source (M9, I7).
    for prior in same_class:
        pk = _value_key(prior.object)
        if pk == same or _subsumes(pk, same):
            return SupersessionPlan(incoming_edge=edge, insert_incoming=True,
                                    operation_id=op_id, expected_state=expected)

    incoming = edge.model_copy(deep=True)
    upserts: list[Edge] = []
    invalidations: list[tuple] = []
    refusals: list[SupersessionRefusalDraft] = []
    absorbed: set[str] = set()

    # Absorption (T1): a MORE specific same-class form of a prior value wins — the shorter
    # prior retires reversibly (absorbed_duplicate; note carries the winner's id), and the
    # winner inherits the earliest valid_from / max observed_at+confidence. Identity, not
    # change — no supersedes pointer.
    for prior in same_class:
        if _subsumes(same, _value_key(prior.object)):
            incoming.valid_from = min(incoming.valid_from, prior.valid_from)
            incoming.provenance.observed_at = max(incoming.provenance.observed_at,
                                                  prior.provenance.observed_at)
            incoming.provenance.confidence = max(incoming.provenance.confidence,
                                                 prior.provenance.confidence)
            noted = prior.model_copy(deep=True)
            noted.note = ((f"{noted.note}; " if noted.note else "")
                          + f"absorbed_by:{incoming.id} (restated as {incoming.object!r})")
            upserts.append(noted)
            invalidations.append((prior.id, incoming.valid_from, "absorbed_duplicate"))
            absorbed.add(prior.id)

    # Supersession (§4a): for a FUNCTIONAL relation, a differing value retires the prior —
    # but ONLY when the incoming edge's recorded effective authority is >= the prior's
    # (the reported defect was the unconditional retirement). Otherwise the retirement is
    # REFUSED: the prior stays active, the incoming edge is stored, both are visible (§4b),
    # and a durable content-free refusal is recorded. Reads ALL classes (a cross-class
    # differing value is exactly the attack); a same-value prior of another class is left
    # alone; an already-absorbed prior is skipped.
    rel = relations.get(edge.relation)
    if rel and rel.functional:
        for prior in scope:
            if prior.id == edge.id or prior.id in absorbed:
                continue
            if _value_key(prior.object) == same:
                continue
            if authority.permitted(prior.provenance.author_of_evidence,
                                    prior.provenance.derived_from,
                                    incoming.provenance.author_of_evidence,
                                    incoming.provenance.derived_from):
                invalidations.append((prior.id, incoming.valid_from, "superseded"))
                incoming.supersedes = prior.id
            else:
                refusals.append(SupersessionRefusalDraft(
                    prior_edge_id=prior.id, incoming_edge_id=incoming.id,
                    relation=edge.relation,
                    prior_effective=authority.edge_effective(prior),
                    incoming_effective=authority.edge_effective(incoming)))

    return SupersessionPlan(incoming_edge=incoming, insert_incoming=True,
                            operation_id=op_id, expected_state=expected,
                            prior_upserts=upserts, prior_invalidations=invalidations,
                            refusals=refusals)


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


def _permute_contention_groups(edges: list[Edge],
                               relations: dict[str, Relation]) -> list[Edge]:
    """specs/0003 §4e: within an active functional-contention group — the active edges
    sharing a `(subject, relation)` key whose relation is functional and which hold >1
    DISTINCT value — recorded effective authority dominates, ahead of relevance and
    recency. It is a PERMUTATION, not a global sort: only the positions a group's members
    already occupy are reordered; every unrelated edge keeps its position (I6b). Conservative
    in the same direction as the guard — it can only prefer higher-authority evidence."""
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for i, e in enumerate(edges):
        rel = relations.get(e.relation)
        if e.active and rel and rel.functional:
            groups[(e.subject, e.relation)].append((i, e))
    out = list(edges)
    for members in groups.values():
        if len({_value_key(e.object) for _, e in members}) <= 1:
            continue                                   # same value → not a contention
        positions = [i for i, _ in members]            # the exact slots to permute within
        # authority DESC, then original relevance (position) ASC, then recency DESC
        ordered = sorted(members, key=lambda ie: (
            -authority.edge_effective(ie[1]), ie[0],
            -ie[1].provenance.observed_at.timestamp()))
        for pos, (_orig, e) in zip(positions, ordered):
            out[pos] = e
    return out


def subgraph_for_query(store, user_id: str, query: str, *, max_edges: int = 40,
                       coverage_share: float = 0.25,
                       relations: Optional[dict[str, Relation]] = None) -> list[Edge]:
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
    # specs/0003 §4e: the relation registry decides which relations are functional (and so
    # which groups are contentions). Additive with a defined default — a host that has
    # customised `MemoryConfig.relations` MUST pass it (exactly as it must to `ingest`),
    # else a relation it made functional is treated as ordinary and its contention is not
    # authority-ordered (round-6 correction C).
    relations = relations if relations is not None else DEFAULT_RELATIONS
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
    ordered = ([e for _, e in scored] if len(scored) <= max_edges
               else _cover(scored, max_edges, coverage_share))
    # authority permutation WITHIN functional-contention groups; unrelated order unchanged
    return _permute_contention_groups(ordered, relations)


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

    Deliberately conservative, with one edge that is NOT conservative and is
    stated here because measurement found it (R2, 2026-08-01):
      * the head is filled by relevance alone, so the TOP-RANKED facts are never
        displaced by coverage — but the head SHRINKS by the reserve, so
        candidates ranked between `max_edges - reserve` and `max_edges` ARE
        displaced, by construction. **Relevance rank is not answer-bearingness.**
        In R2 an item whose single answer-bearing fact ranked 34/40 lost it
        entirely at share=0.25 (head 30), taking its hit rate from 1.000 to
        0.000. Across that sample 8 of 30 items had exactly ONE answer-bearing
        turn, so "costs a few of the least-relevant head slots" can mean
        "costs the whole answer" and is not a rare shape;
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
