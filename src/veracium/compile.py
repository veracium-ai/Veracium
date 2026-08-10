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

from .graph import _value_key, collapse_for_render, render_edges
from .llm.base import Complete
from .schema import DEFAULT_RELATIONS, Relation

# The contention-policy version. Bump it when the derived-view semantics change in a way a
# cached wiki must not survive (independently of the relation registry). It rides in the
# compiler_policy_digest, so a stale-under-the-old-policy cache recompiles (specs/0003 §4c-ii,
# round-10 blocker 2).
_CONTENTION_POLICY_VERSION = "0003-v1"
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


def _policy_digest(relations: dict[str, Relation]) -> str:
    """specs/0003 §4c-ii (round-10 blocker 2): the wiki's cache identity must bind the
    compiler-policy inputs, not just `store_version`. The functional-relation registry is
    host-supplied and lives OUTSIDE the store, so reopening the same store under a registry
    that classifies a relation differently changes what the compiler must exclude with NO
    `store_version` change. This digest covers the functional-relation semantics AND the
    contention-policy version; a mismatch forces recompilation regardless of `store_version`."""
    functional = sorted(name for name, r in relations.items() if r.functional)
    blob = json.dumps({"functional": functional, "policy": _CONTENTION_POLICY_VERSION},
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
                    relations: dict[str, Relation]) -> bool:
    cached = store.get_wiki(user_id)
    if cached is None:
        return True
    stored_text, version_at_compile = cached
    digest, _ = _split_envelope(stored_text)
    if digest != _policy_digest(relations):        # registry/policy changed → recompile
        return True
    return store.store_version(user_id) - version_at_compile >= recompile_after


def compile_wiki(store, llm: Complete, user_id: str, relations: dict[str, Relation],
                 *, budget_tokens: int = 900) -> str:
    edges, episodes = _grounded_inputs(store, user_id, relations)
    facts = render_edges(edges) or "(none)"
    hist = "\n".join(f"[{e.date}] {e.summary}" for e in episodes) or "(none)"
    wiki = llm(COMPILE_PROMPT.format(budget=budget_tokens, facts=facts, episodes=hist),
               system=COMPILE_SYSTEM, role="compile").strip()
    # store WITH the policy-digest envelope so the cache binds its compiler policy
    store.set_wiki(user_id, f"{_ENVELOPE}{_policy_digest(relations)}\n{wiki}",
                   store.store_version(user_id))
    return wiki


def ensure_wiki(store, llm: Complete, user_id: str, recompile_after: int,
                relations: Optional[dict[str, Relation]] = None) -> Optional[str]:
    """Return the current wiki BODY (envelope stripped), recompiling if stale. None disables
    the wiki layer. `relations` (the host registry) reaches the compiler so a custom
    functional relation is excluded from the wiki when contested (§4c-ii); omitted →
    `DEFAULT_RELATIONS`."""
    relations = relations if relations is not None else DEFAULT_RELATIONS
    if recompile_after <= 0:
        return None
    if needs_recompile(store, user_id, recompile_after, relations):
        return compile_wiki(store, llm, user_id, relations)
    return _split_envelope(store.get_wiki(user_id)[0])[1]
