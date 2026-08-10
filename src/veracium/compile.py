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

import hashlib
import json
from typing import Optional

from . import budgets as _budgets
from .graph import _value_key, collapse_for_render, render_edges
from .llm.base import Complete
from .schema import DEFAULT_RELATIONS, Relation

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
    compiler-policy inputs, not just `store_version`. The functional-relation registry is
    host-supplied and lives OUTSIDE the store, so reopening the same store under a registry
    that classifies a relation differently changes what the compiler must exclude with NO
    `store_version` change. This digest covers the functional-relation semantics AND the
    contention-policy version; a mismatch forces recompilation regardless of `store_version`."""
    functional = sorted(name for name, r in relations.items() if r.functional)
    blob = json.dumps({"functional": functional, "policy": _CONTENTION_POLICY_VERSION,
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
    referenced edges are active AND still distinct AND the relation is functional (§4c-ii).
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
    excluded: set = set()
    for r in refs:
        prior, inc = active.get(r.prior_edge_id), active.get(r.incoming_edge_id)
        rel = relations.get(r.relation)
        if (prior is not None and inc is not None and rel and rel.functional
                and _value_key(prior.object) != _value_key(inc.object)):
            excluded.add(prior.id)
            excluded.add(inc.id)
    return excluded


def _grounded_inputs(store, user_id: str, relations: dict[str, Relation]):
    """Only assertable material feeds the compile: active, non-quarantined edges
    that are NOT third-party inferences (use_only), plus episodes NOT authored by a
    third party. A use_only inference must be excluded here too — the wiki is placed
    in the gate's assertable GROUNDED block by recall(), so letting it into the wiki
    would make it assertable through the wiki (mirrors gate.partition, which already
    routes use_only to UNVERIFIED). The inference still shapes behavior via recall's
    unverified channel; it is not lost, only kept out of the assertable body.

    specs/0003 §4c-ii: a contested functional group in a LIVE refusal contention is also
    excluded, so the "keep one current value" prompt only ever sees facts that HAVE one —
    a refusal never hands the LLM two competing values to collapse."""
    contested = _live_refusal_contention_edge_ids(store, user_id, relations)
    edges = [e for e in store.edges(user_id, active_only=True, include_quarantined=False)
             if not e.use_only and e.id not in contested]
    # specs/0012 I8: the compiler INPUT collapses strictly-redundant duplicates —
    # N restatements feed the wiki once; the store keeps every edge.
    edges, _since = collapse_for_render(edges)
    # Episodes are excluded by third-party *influence*, not authorship alone: a
    # system-authored episode derived from third-party content (derived_from)
    # carries that content verbatim and must not reach the assertable wiki.
    episodes = [e for e in store.episodes(user_id)
                if not e.provenance.third_party_influenced]
    return edges, episodes


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
                 variant_cap: int = 4, item_cap: int = 512) -> str:
    """specs/0012 I10a/I10j: the compiler INPUT is hard-budgeted (each item clamped to the
    per-item cap; at most `variant_cap` value lines per (subject, relation) group; the whole
    input under `wiki_input_budget` est. tokens) and every drop is COUNTED into the
    authoritative marker line appended BY CODE after sanitizing the LLM output. The marker
    is always present, including the +0/+0 case."""
    _budgets.validate_budget("wiki", wiki_input_budget)    # revalidated at surface
    #                                                        build, not only config (I10e)
    edges, episodes = _grounded_inputs(store, user_id, relations)
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
    groups: dict[tuple, list] = {}
    for e in edges:
        k = (e.subject, e.relation, e.provenance.disclosure.value,
             e.provenance.author_of_evidence.value,
             e.provenance.derived_from.value if e.provenance.derived_from else "")
        groups.setdefault(k, []).append(e)
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
    raw = llm(prompt, system=COMPILE_SYSTEM, role="compile").strip()
    # sanitize FIRST (forged sentinels become inert), then append the code-owned marker
    wiki = _budgets.append_compile_marker(_budgets.sanitize_llm_body(raw),
                                          facts_dropped, eps_dropped)
    digest = _policy_digest(relations, wiki_input_budget=wiki_input_budget,
                            variant_cap=variant_cap, item_cap=item_cap)
    store.set_wiki(user_id, f"{_ENVELOPE}{digest}\n{wiki}",
                   store.store_version(user_id))
    return wiki


def ensure_wiki(store, llm: Complete, user_id: str, recompile_after: int,
                relations: Optional[dict[str, Relation]] = None, *,
                wiki_input_budget: int = 8000, variant_cap: int = 4,
                item_cap: int = 512) -> Optional[str]:
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
    _budgets.validate_budget("wiki", wiki_input_budget)    # I10e at every source
    kw = dict(wiki_input_budget=wiki_input_budget, variant_cap=variant_cap,
              item_cap=item_cap)
    if needs_recompile(store, user_id, recompile_after, relations, **kw):
        if getattr(llm, "_veracium_no_llm", False):       # I10l: provider-free reader
            return _budgets.STALE_WIKI_NOTICE
        return compile_wiki(store, llm, user_id, relations, **kw)
    return _split_envelope(store.get_wiki(user_id)[0])[1]
