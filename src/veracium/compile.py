"""The curated view (finding 20): an LLM cartographer compiles a budgeted "wiki"
from the store, cached and recompiled after N writes.

Security-critical design (finding 23-C — the injection surface is the episode,
not the wiki): the compiler is fed ONLY grounded, user/system-authored material.
Third-party claims and third-party-authored episodes are never compiled into the
assertable body; they surface only through recall's unverified channel, where the
abstention gate governs them. This is why excluding claims from the wiki *text*
alone was insufficient in the research — the claim re-entered via its episode. Here
the episode itself is withheld from the grounded compile.
"""

from __future__ import annotations

import logging
from .census import declare_site

_log = logging.getLogger(__name__)

import hashlib
import json
from typing import Optional

from . import budgets as _budgets
from .graph import collapse_for_render, render_edges
from .contention import is_live_refusal, retained_refusal_ids
from .llm.base import Complete
from .schema import DEFAULT_RELATIONS, Relation, assertion_view
from .registry import declared_arity

# The contention-policy version. Bump it when the derived-view semantics change in a way a
# cached wiki must not survive (independently of the relation registry). It rides in the
# compiler_policy_digest, so a stale-under-the-old-policy cache recompiles (specs/0003 §4c-ii,
# round-10 blocker 2).
# specs/0012 §7b: the contention-policy version BUMPS on 0012's landing — the wiki cache
# identity now binds the §4c input→cache-effect MATRIX (accepted 0003's registry binding
# PRESERVED, plus the compiler-relevant 0012 inputs; render-time knobs deliberately
# excluded — binding them would force spurious recompiles).
_CONTENTION_POLICY_VERSION = "0012-v1"
_ENVELOPE = "\x00policy:"      # cache-envelope marker: the digest precedes the wiki body
# The body when there is NO grounded input (research's adoption probe 3, 2026-10-29): fixed by code, never model prose.
# Asked to compile `(none)`/`(none)`, a compiler wrote "Document is empty pending user information" above an
# UNVERIFIED section, and drivers then told the user their memory was empty. recall's own placeholder uses it too.
EMPTY_GROUNDED_BODY = "(no verified facts yet)"

COMPILE_SYSTEM = (
    "You are the memory curator for an AI assistant. You compile a compact, "
    "accurate memory document from a user's known facts and interaction history. "
    "You never invent; you keep names, dates, and numbers exact; you merge "
    "duplicates and keep one current value per changing fact with brief inline "
    "history."
)

COMPILE_PROMPT = """Compile the material below into ONE curated memory document,
<= {budget} tokens, with these sections (omit a section if empty):

## USER MODEL
## CURRENT STATE
## WORK & PROJECT KNOWLEDGE
## NOTABLE EVENTS

GROUNDED FACTS (verified — user-stated or system-observed):
{facts}

INTERACTION HISTORY (user's own interactions):
{episodes}

Rules:
- Merge duplicates; one line per fact. Keep names/dates/numbers EXACT.
- For a changed fact, give the current value with brief inline history:
  "X (since <date>; previously Y)".
- NOTABLE EVENTS: keep recent events as dated one-liners; compress older periods,
  but ALWAYS keep first occurrences of failures, their fixes, and dated commitments.
- Output only the document. No preamble, no commentary."""


def _policy_digest(relations: dict[str, Relation], *, wiki_input_budget: int = 8000,
                   variant_cap: int = 4, item_cap: int = 512) -> str:
    """specs/0003 §4c-ii (round-10 blocker 2): the wiki's cache identity must bind the
    compiler-policy inputs, not just `store_version`. The relation registry is host-supplied
    and lives OUTSIDE the store, so reopening the same store under a registry that classifies
    a relation differently changes what the compiler must exclude with NO `store_version`
    change. specs/0044 §2 (T5-3): the digest binds every relation's ARITY — the whole
    `(name, arity)` map, read through `registry.declared_arity`, not the subset that is
    `single` — AND the contention-policy version; a mismatch forces recompilation regardless
    of `store_version`. Changing what the digest binds re-keys every cached wiki: one
    recompilation per cached user view, on its next read."""
    arity = sorted((name, declared_arity(r)) for name, r in relations.items())
    blob = json.dumps({"arity": arity, "policy": _CONTENTION_POLICY_VERSION,
                       # the 0012 additions (I10k): compiler selection/serialization inputs
                       "wiki_input_budget": wiki_input_budget, "variant_cap": variant_cap,
                       "item_cap": item_cap,
                       "marker_grammar": _budgets.MARKER_GRAMMAR_VERSION},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _split_envelope(stored: str) -> tuple[Optional[str], str]:
    """(policy_digest, body) from a stored wiki. A pre-0003 cache has no envelope → its
    digest is None, which never matches the current one, so it recompiles (§7a)."""
    if stored.startswith(_ENVELOPE):
        head, _, body = stored.partition("\n")
        return head[len(_ENVELOPE):], body
    return None, stored


def _live_refusal_contention_edge_ids(store, user_id: str,
                                      relations: dict[str, Relation]) -> set:
    """The edge ids in a LIVE refusal contention — a refusal record exists AND both
    referenced edges are active AND still distinct AND the relation is functional (§4c-ii), or the refusal's
    protection is retained across 0044's reclassification (§4d) — `veracium.contention.is_live_refusal`.
    These are excluded from the one-value LLM wiki so a refusal cannot collapse the pair;
    the derived-view treatment is REFUSAL-scoped (Option B), not every contention."""
    try:
        refs = store.refusals(user_id)
    except NotImplementedError:                    # a Store without the 0003 primitive
        return set()
    if not refs:
        return set()
    active = {e.id: e for e in store.edges(user_id, active_only=True,
                                           include_quarantined=True)}
    retained = retained_refusal_ids(store, user_id)          # specs/0044 §4d
    excluded: set = set()
    for r in refs:
        prior, inc = active.get(r.prior_edge_id), active.get(r.incoming_edge_id)
        if is_live_refusal(r, prior, inc, relations, retained):   # the ONE predicate (veracium.contention)
            excluded.add(prior.id)
            excluded.add(inc.id)
    return excluded


_SITE_GROUNDED_INPUTS = declare_site("compile.grounded-inputs")   # specs/0042 (declined= is explicit)
_SITE_FENCE_DISPUTED = declare_site("compile.fence.disputed", declines=True)   # specs/0047 INV-R18
_SITE_BIND_UNBOUND = declare_site("compile.bind.unbound", declines=True)   # specs/0047 INV-R18, R-II round 2's RII-01


def _drew_a_challenged_fact(store, user_id: str, edges) -> bool:
    """specs/0047 INV-R18, the in-flight fence's challenge branch: did this compile draw on a fact a NOW-read challenge
    snapshot withholds (a challenge, or a twin of one, committed since the inputs were read)? True withholds the body."""
    now = store.challenge_snapshot(user_id)
    with _SITE_FENCE_DISPUTED.consult():
        return _SITE_FENCE_DISPUTED.fire(sum(1 for e in edges if now.withheld(e)) > 0, "withhold-body")


def _grounded_inputs(store, user_id: str, relations: dict[str, Relation]):
    """Only assertable material feeds the compile: active, non-quarantined edges
    that are NOT third-party inferences (use_only), plus episodes NOT authored by a
    third party. A use_only inference must be excluded here too — the wiki is placed
    in the gate's assertable GROUNDED block by recall(), so letting it into the wiki
    would make it assertable through the wiki (mirrors gate.partition, which already
    routes use_only to UNVERIFIED). The inference still shapes behavior via recall's
    unverified channel; it is not lost, only kept out of the assertable body.

    specs/0003 §4c-ii: a contested group in a LIVE refusal contention is also excluded, so
    a refusal never hands the "keep one current value" prompt two competing values to
    collapse. That is the claim, and only that: since specs/0044 the non-refused values of a
    `multi` relation reach the compiler by design (§4c — several can be current at once)."""
    with _SITE_GROUNDED_INPUTS.consult():
        # specs/0047 §4d (INV-R18): a challenged fact — and, by the owner's F7 ruling, its active same-value twin —
        # is EXCLUDED from the compiler's input: a free-text compiler cannot be made to carry the unit. One snapshot,
        # read before the edges
        snap = store.challenge_snapshot(user_id)
        contested = _live_refusal_contention_edge_ids(store, user_id, relations)
        # specs/0019 §4c (F4 — reviewer-executed): the compiler stores an LLM's
        # free-text output, and a code-owned marker cannot survive a re-rendering
        # it does not control — so flagged facts are EXCLUDED from the compiler
        # INPUT (the 0003 contested-exclusion precedent). The wiki is the curated
        # grounded view; a possibly-fabricated specific has no place in it. The
        # fact remains fully reachable through query recall, with its marker.
        # specs/0037 §4a (V-RENDER-SITES): the wiki compiler's input IS model
        # context — a procedural record is out of scope by its own stamp/basis
        # (`gate.exclude_procedural`, PROCEDURAL_OUT_OF_SCOPE), before any
        # other filter
        from .gate import exclude_procedural
        _in_scope, _n_procedural = exclude_procedural(
            store.edges(user_id, active_only=True, include_quarantined=False))
        # specs/0041 §4b-iii (tranche 4a): an attested-redacted record never feeds the wiki — the cache is
        # dropped at redaction and would otherwise be recompiled over the marker; by the record, not the bytes
        redacted_edges = store.redacted_targets(user_id, "edge")
        redacted_episodes = store.redacted_targets(user_id, "episode")
        edges = [e for e in _in_scope
                 if not e.use_only and e.id not in contested and not e.ungrounded and e.id not in redacted_edges
                 and not snap.withheld(e)]
        # specs/0012 I8: the compiler INPUT collapses strictly-redundant duplicates —
        # N restatements feed the wiki once; the store keeps every edge.
        edges, _since = collapse_for_render(edges, snap)
        # 0023 §4a-iv (F1): the SHARED predicate, not an open-coded copy of the
        # condition. assertable subsumes third-party influence AND the disclosure
        # ingest now writes AND 0022's retirement axis — the wiki input is the
        # assertable set, by the same rule every other consumer reads.
        all_episodes = list(store.episodes(user_id))
        episodes = [e for e in all_episodes if e.assertable and e.id not in redacted_episodes]   # specs/0041 §4b-iii
        withheld = _n_procedural + (len(_in_scope) - len(edges)) + (len(all_episodes) - len(episodes))
        return _SITE_GROUNDED_INPUTS.fire((edges, episodes), "withhold", declined=withheld > 0)


def needs_recompile(store, user_id: str, recompile_after: int,
                    relations: dict[str, Relation], *, wiki_input_budget: int = 8000,
                    variant_cap: int = 4, item_cap: int = 512) -> bool:
    cached = store.get_wiki(user_id)
    if cached is None:
        return True
    stored_text, version_at_compile = cached
    digest, _ = _split_envelope(stored_text)
    if digest != _policy_digest(relations, wiki_input_budget=wiki_input_budget,
                                variant_cap=variant_cap, item_cap=item_cap):
        return True                                # identity-stale → recompile (I10k)
    return store.store_version(user_id) - version_at_compile >= recompile_after


def compile_wiki(store, llm: Complete, user_id: str, relations: dict[str, Relation],
                 *, budget_tokens: int = 900, wiki_input_budget: int = 8000,
                 variant_cap: int = 4, item_cap: int = 512, _retry: bool = False,
                 _bind: Optional[dict] = None) -> str:
    """specs/0012 I10a/I10j: the compiler INPUT is hard-budgeted (each item clamped to the
    per-item cap; at most `variant_cap` value lines per (subject, relation) group; the whole
    input under `wiki_input_budget` est. tokens) and every drop is COUNTED into the
    authoritative marker line appended BY CODE after sanitizing the LLM output. The marker
    is always present, including the +0/+0 case."""
    _budgets.validate_surface_params("wiki", wiki_input_budget,
                                     item_cap=item_cap, variant_cap=variant_cap)
    # specs/0041 §4e (tranche 5): the version is read BEFORE the inputs and the publish is conditional on
    # it — a store that moves during the slow compile (a redaction, any write) is never published over
    version_at_begin = store.store_version(user_id)
    edges, episodes = _grounded_inputs(store, user_id, relations)
    if _bind is not None:              # specs/0047 §4d (R-II RII-01): the records this body drew on, for bound_wiki
        _bind["drew"], _bind["drew_episodes"] = edges, episodes
    # I10g: the bound governs the COMPLETE serialized prompt — reserve the fixed
    # scaffolding (COMPILE_SYSTEM + the prompt skeleton) BEFORE item selection, so a
    # full dynamic payload can never push the serialized text past wiki_input_budget.
    scaffold = (_budgets.est_tokens(COMPILE_PROMPT.format(budget=budget_tokens,
                                                          facts="", episodes=""))
                + _budgets.est_tokens(COMPILE_SYSTEM))
    items_budget = max(0, wiki_input_budget - scaffold)
    facts_dropped = eps_dropped = 0
    spent = 0
    # I10b/I10f (the frozen compiler total order): ONE survivor per (subject, relation)
    # group FIRST — no group's sole representative is displaced by another group's
    # variants — then variants up to the per-group cap, then episodes NEWEST first.
    # I8f: the compiler group key carries the COMPLETE authority envelope — USER and
    # SYSTEM members of the same value are DISTINCT groups, each owed a survivor.
    # Group iteration is DETERMINISTIC ((subject, relation, disclosure, author,
    # derived_from) sort order), never dict/input order (R-impl2-3).
    from .graph import value_groups as _value_groups
    env_buckets: dict[tuple, list] = {}
    for e in edges:
        k = (e.subject, e.relation, e.provenance.disclosure.value,
             e.provenance.author_of_evidence.value,
             e.provenance.derived_from.value if e.provenance.derived_from else "")
        env_buckets.setdefault(k, []).append(e)
    # I8's FULL group = the envelope × unique-anchor VALUE grouping (R-impl3-2):
    # incomparable same-envelope values are DISTINCT groups, each owed a survivor.
    from .graph import _collapse_survivor_order
    groups: dict[tuple, list] = {}
    for k in sorted(env_buckets):
        for vk, members in sorted(_value_groups(env_buckets[k]).items()):
            # the I8j survivor total order (note-bearing → specificity → freshest →
            # edge id) decides each group's representative — NEVER input order
            groups[k + (vk,)] = sorted(members, key=_collapse_survivor_order)
    ordered_keys = sorted(groups)
    survivors = [groups[k][0] for k in ordered_keys]
    variants = [e for k in ordered_keys for e in groups[k][1:]]
    key_of = {e.id: k for k, members in groups.items() for e in members}
    fact_lines: list[str] = []
    per_group: dict[tuple, int] = {}
    for tier, is_variant in ((survivors, False), (variants, True)):
        for e in tier:
            g = key_of[e.id]
            # the cap applies to VARIANTS BEYOND the survivor (R-impl2-3)
            if is_variant and per_group.get(g, 0) >= 1 + variant_cap:
                facts_dropped += 1
                continue
            # I10c: content-first clamping — the stale/use_only labels render at the
            # line END; a prefix clamp would keep attacker text and delete the label
            line = _budgets.clamp_edge_line(e, item_cap, render_edges)
            if not line:
                continue
            cost = _budgets.est_tokens(line) + 1          # +1: the join newline
            if spent + cost > items_budget:               # the hard input budget
                facts_dropped += 1
                continue
            per_group[g] = per_group.get(g, 0) + 1
            spent += cost
            fact_lines.append(line)
    ep_lines: list[str] = []
    for e in reversed(episodes):                          # newest first under budget
        line = _budgets.clamp_item(f"[{e.date}] {e.summary}", item_cap)
        cost = _budgets.est_tokens(line) + 1              # +1: the join newline
        if spent + cost > items_budget:
            eps_dropped += 1
            continue
        spent += cost
        ep_lines.append(line)
    ep_lines.reverse()                                    # render chronologically
    facts = "\n".join(fact_lines) or "(none)"
    hist = "\n".join(ep_lines) or "(none)"
    prompt = COMPILE_PROMPT.format(budget=budget_tokens, facts=facts, episodes=hist)
    # nothing grounded to compile: the fixed line, not the model (a model narrates an empty input as an empty memory)
    raw = (EMPTY_GROUNDED_BODY if not edges and not episodes
           else llm(prompt, system=COMPILE_SYSTEM, role="compile").strip())
    # sanitize FIRST (forged sentinels become inert), then append the code-owned marker
    wiki = _budgets.append_compile_marker(_budgets.sanitize_llm_body(raw),
                                          facts_dropped, eps_dropped)
    digest = _policy_digest(relations, wiki_input_budget=wiki_input_budget,
                            variant_cap=variant_cap, item_cap=item_cap)
    published = store.set_wiki(user_id, f"{_ENVELOPE}{digest}\n{wiki}", version_at_begin)
    if published and _bind is not None:    # RII-R2-01 (D2): the row this compile published, for bound_wiki to discard
        _bind["published"] = (f"{_ENVELOPE}{digest}\n{wiki}", version_at_begin)
    if not published:
        # the store moved under the compile: nothing is published (the next read recompiles from the store
        # of record). specs/0041 round 10 (found in sweep A): if what moved is a REDACTION of a record this compile
        # drew on, the body must not be served either — it was compiled from content redacted since. Recompile
        # ONCE from the post-redaction state (whose inputs exclude the attested records); if that too cannot
        # publish and a record IT drew on was redacted meanwhile, return the closed stale notice — never a body
        # drawn from an attested record, and never a loop. A plain concurrent write keeps the behaviour below.
        drew_edges = {e.id for e in edges} & store.redacted_targets(user_id, "edge")
        drew_episodes = {e.id for e in episodes} & store.redacted_targets(user_id, "episode")
        # specs/0047 §4d (INV-R18): the fence ALSO withholds a body compiled before a challenge of a fact it drew on
        drew_challenged = _drew_a_challenged_fact(store, user_id, edges)
        if drew_challenged and not (drew_edges or drew_episodes):
            if _retry:
                return _budgets.DISPUTED_DURING_COMPILE_NOTICE
            return compile_wiki(store, llm, user_id, relations, budget_tokens=budget_tokens,
                                wiki_input_budget=wiki_input_budget, variant_cap=variant_cap, item_cap=item_cap,
                                _retry=True, _bind=_bind)
        if drew_edges or drew_episodes:
            if _retry:
                _log.info("wiki compile for %r withheld: a record it drew on was redacted during the compile "
                          "(specs/0041 §4e, round 10)", user_id)
                return _budgets.REDACTED_DURING_COMPILE_NOTICE
            return compile_wiki(store, llm, user_id, relations, budget_tokens=budget_tokens,
                                wiki_input_budget=wiki_input_budget, variant_cap=variant_cap, item_cap=item_cap,
                                _retry=True, _bind=_bind)
        # otherwise the wiki text is returned for THIS call's own use — it was compiled from a consistent read,
        # and it is never cached
        _log.info("wiki compile for %r not published: the store moved during the compile (specs/0041 §4e)", user_id)
    return wiki


def ensure_wiki(store, llm: Complete, user_id: str, recompile_after: int,
                relations: Optional[dict[str, Relation]] = None, *,
                wiki_input_budget: int = 8000, variant_cap: int = 4,
                item_cap: int = 512, _bind: Optional[dict] = None) -> Optional[str]:
    """Return the current wiki BODY (envelope stripped), recompiling if stale. None disables
    the wiki layer. `relations` (the host registry) reaches the compiler so a custom
    functional relation is excluded from the wiki when contested (§4c-ii); omitted →
    `DEFAULT_RELATIONS`.

    specs/0012 I10l: a PROVIDER-FREE reader (the CLI's store-only verbs mark their stub
    with `_veracium_no_llm`) with an identity-stale cache is served the deterministic
    stale-notice INSTEAD of a recompile — never the stale body, never the LLM, never a
    failure."""
    relations = relations if relations is not None else DEFAULT_RELATIONS
    if recompile_after <= 0:
        return None
    _budgets.validate_surface_params("wiki", wiki_input_budget,
                                     item_cap=item_cap, variant_cap=variant_cap)
    kw = dict(wiki_input_budget=wiki_input_budget, variant_cap=variant_cap,
              item_cap=item_cap)
    if needs_recompile(store, user_id, recompile_after, relations, **kw):
        if getattr(llm, "_veracium_no_llm", False):       # I10l: provider-free reader
            return _budgets.STALE_WIKI_NOTICE
        return compile_wiki(store, llm, user_id, relations, _bind=_bind, **kw)
    row = store.get_wiki(user_id)
    if row is None:                    # evicted between the staleness check and this read: stale, as above
        if getattr(llm, "_veracium_no_llm", False):
            return _budgets.STALE_WIKI_NOTICE
        return compile_wiki(store, llm, user_id, relations, _bind=_bind, **kw)
    if _bind is not None:
        _bind["row"] = row             # specs/0047 §4d (R-II RII-01): the row this body was served from, for bound_wiki
    return _split_envelope(row[0])[1]


# the code-owned bodies ensure_wiki can return in place of a compiled one: each asserts no fact
_WIKI_NOTICES = frozenset({_budgets.STALE_WIKI_NOTICE, _budgets.REDACTED_DURING_COMPILE_NOTICE,
                           _budgets.DISPUTED_DURING_COMPILE_NOTICE})


def _unbound_by(store, user_id: str, snap, edges, episodes):
    """Why a body drawn on `edges` and `episodes` may NOT be served beside `snap` — the notice that replaces it — or None
    when it may. The round-10 fence's predicate (compile_wiki: a challenge, a redaction), read AFTER the compile and
    against the call's own snapshot, plus erasure: a fact the snapshot withholds; an edge or an episode redacted since
    it was read; an edge or an EPISODE no longer in the store (forget_user, whatever the body drew on: research's R-II
    round 2 landing read, L1, an episodes-only body passed an edge-presence test that holds vacuously over no edges);
    and (specs/0004 W9, the owner's D10 ruling) an edge since INVALIDATED for a reason that drops the wiki, by W1's own
    rule (schema.wiki_drops_on, the function the store's eviction calls): a revoking invalidation of a fact the body
    drew on withholds it, published or not; a retaining one (W3's staleness, W8's absorption) keeps it. Presence is read
    through the Store API, so an episode a consolidation cutover hides reads as absent too: a recompute, never a wrong
    body. Research's stage-2 probe: a redaction in this window passed a bind that read only
    `withheld`, which reads open challenges and nothing else.

    R-II round 2's RII-R2-01 (research's stage-1 S2): the bind reads each drawn record's CURRENT row, never the object
    the compile drew. A same-ID replacement in the window — a demotion to quarantined or use_only, a changed value, a
    revoking retirement — changes the record's `schema.assertion_view` (the rule the store's eviction applies at the
    write) and withholds the body, with no notice that would be true — a replacement that makes a drawn record a twin of
    a challenged one included, since it moves the drawn record's value. The revoking-invalidation rule above is the
    view's liveness component."""
    if any(snap.withheld(e) for e in edges):
        return _budgets.DISPUTED_DURING_COMPILE_NOTICE
    if ({e.id for e in edges} & store.redacted_targets(user_id, "edge")
            or {e.id for e in episodes} & store.redacted_targets(user_id, "episode")):
        return _budgets.REDACTED_DURING_COMPILE_NOTICE
    now = {e.id: e for e in store.edges(user_id, active_only=False, include_quarantined=True)}
    now_episodes = {e.id: e for e in store.episodes(user_id, include_retired=True)}
    if (any(assertion_view(now.get(e.id)) != assertion_view(e) for e in edges)
            or any(assertion_view(now_episodes.get(e.id)) != assertion_view(e) for e in episodes)):
        return _NO_WIKI                # erased, revoked or replaced since the compile drew it
    # past this point every drawn record's current view equals its drawn one, and the snapshot's twin match reads
    # only view fields (the id, the procedural stamp, subject, relation, object), so the first clause above has
    # already asked the snapshot about the current rows: a challenged record moving onto a drawn value is caught
    # there (tests/test_rii_r2_01_writer_inventory.py pins the snapshot to the view)
    return None


_NO_WIKI = object()                    # erased or revoked since the compile: no wiki, and no notice that would be true


def _bind_withholds(why) -> bool:
    """specs/0047 INV-R18 (R-II round 2's RII-01): bound_wiki's decision, for both of its binds — True withholds the
    body this call would serve (`why`, its cause, is not None)."""
    with _SITE_BIND_UNBOUND.consult():
        return _SITE_BIND_UNBOUND.fire(why is not None, "withhold-body")


def bound_wiki(store, llm: Complete, user_id: str, recompile_after: int,
               relations: Optional[dict[str, Relation]] = None, **kw):
    """specs/0047 §4d, INV-R18 (R-II RII-01): the wiki body a recall serves AND the call's one challenge snapshot,
    returned as `(body, snapshot)` and bound to one state, so the body never asserts a fact the same call reports as
    challenged, nor one redacted, erased or revokingly invalidated before the call served it. ensure_wiki produces the body before any
    snapshot exists; the snapshot is read after it, and the body is served only if it is bound to that snapshot:

    - a body COMPILED in this call is bound by what it drew on (`_unbound_by`): no input fact withheld by the snapshot,
      no input edge or episode redacted or erased, no input edge invalidated for a reason that drops the wiki
      (specs/0004 W9, by W1's rule) — read after the snapshot. Any other write in the window (a plain add, a retaining
      invalidation: W3's staleness, W8's absorption) keeps the body for this call;
    - a CACHED body is bound by its row: the wiki row read AFTER the snapshot is the very row (text and version) the
      body was served from. Every write that evicts the wiki does so in its own transaction (a reply, a redaction, an
      erasure, the import; tests/test_0047_rii01_wiki_bind.py's census holds the set and classes each writer), so a
      row unchanged across the snapshot proves none of them was committed between the body's read and the snapshot's.

    No read window is held across the reads (a writer is never made to wait on this call): a row evicted just AFTER
    the snapshot reads as a failed bind too, which costs a recompute and is never wrong. A body that fails its bind is
    recomputed once (the evicted row recompiles; a compile re-reads its inputs, which exclude what the snapshot
    withholds, what is redacted and what is inactive); failing again, the notice for its cause is served — the
    disputed or the redacted one — and after an erasure or a revoking invalidation no wiki at all. A notice or a disabled layer asserts nothing and is returned with the
    snapshot as is. Never compares written_at."""
    why = _budgets.DISPUTED_DURING_COMPILE_NOTICE
    for _attempt in range(2):
        box: dict = {}
        body = ensure_wiki(store, llm, user_id, recompile_after, relations, _bind=box, **kw)
        snap = store.challenge_snapshot(user_id)
        if body is None or body in _WIKI_NOTICES:
            return body, snap
        if "drew" in box:
            why = _unbound_by(store, user_id, snap, box["drew"], box["drew_episodes"])
        elif box.get("row") is not None and store.get_wiki(user_id) == box["row"]:
            why = None
        else:                          # the row moved: its cause is not recorded with a cached body
            why = _budgets.DISPUTED_DURING_COMPILE_NOTICE
        if not _bind_withholds(why):
            return body, snap
        if box.get("published") is not None:
            # RII-R2-01 (D2, defence in depth): a compiled body that failed its bind takes its own published row with
            # it, so the retry cannot be served that body back from the cache and pass on the row's equality. The
            # write that unbound it evicts the row already (schema.assertion_view at the store's writers); this
            # discard is conditional on the row still being the published one, so it never drops a newer compile
            store.discard_wiki(user_id, *box["published"])
    return (None if why is _NO_WIKI else why), snap
