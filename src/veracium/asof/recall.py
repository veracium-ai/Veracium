"""specs/0028 §4c — recall's AS-OF BRANCH: the §4a resolution produces the
candidate set, then normal recall (lexical / 0027 semantic + gate + budget)
runs over it. As-of is a pre-filter; ranking is unchanged in construction —
only its assertability predicate is the branch's own T-verdict, so neither
the I6 reserve nor the budget partition consults `Edge.assertable` here
(V-ONE-CLOCK, mutant 2). Under `as_of` the wiki and episode sections are
OMITTED (§4c: a now-wiki and now-history inside a T-answer would assert
present truth), and so is 0003's contested block — contention is derived per
read from the CURRENT refusal set, a now-fact by the same argument, and
building it runs the recall path's `assertable`. Lives under `asof/` so the
recording-clock proof attributes every predicate access on this branch.
"""
from __future__ import annotations

from .resolve import GROUNDED_OUTCOMES, AsOfAnswer, render_fn_for, resolve_as_of


def recall_at(mem, user_id: str, query: str, token_budget: int, *, as_of,
              view, principal, filters, semantic, usage_finish):
    from .. import Recall, RecalledEdge
    from ..graph import _lexical_scored, fused_subgraph
    from ..scope_read import narrow_edges

    answer = resolve_as_of(mem.store, user_id, as_of, principal=principal,
                           policy=mem.scope_policy, view=view)
    by_res = {f.edge.id: f.resolution for f in answer.facts}
    candidates = [f.edge for f in answer.facts]

    def grounded(e) -> bool:
        r = by_res.get(e.id)
        return r is not None and r.outcome in GROUNDED_OUTCOMES

    def claim(e) -> bool:
        return not grounded(e)

    scored, relevant_ids, by_id = _lexical_scored(
        mem.store, user_id, query, view=view, candidates=candidates)
    sem_status, sm_pairs = "disabled", []
    if semantic is not False:
        sem_status, sm_pairs = mem._semantic_lane(
            user_id, query, visible_ids=set(by_id))
    edges, raw_meta = fused_subgraph(
        scored, relevant_ids, by_id, sm_pairs if sem_status == "ok" else [],
        max_edges=mem.config.max_subgraph_edges,
        coverage_share=mem.config.subgraph_coverage_share,
        relations=mem.config.relations, assertable=grounded)
    sem_meta = {k: RecalledEdge(**v) for k, v in raw_meta.items()}
    if view is not None:
        edges = view.narrow(edges)
    elif filters:
        edges = narrow_edges(edges, filters)

    _wiki, detail, unverified, truncated = mem._fit_to_budget(
        None, edges, [], token_budget, query,
        assertable=grounded, claims=claim, render=render_fn_for(answer))
    grounded_text = (("## RELEVANT DETAIL\n" + detail) if detail
                     else f"(nothing held as of {answer.T.isoformat()} for this user)")
    context = grounded_text
    if unverified:
        context += ("\n\n## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)\n"
                    + unverified)
    mem._record("recall", {**usage_finish(),
                           "wiki_used": False, "subgraph_edges": len(edges),
                           "grounded_items": sum(1 for e in edges if grounded(e)),
                           "unverified_items": sum(1 for e in edges if not grounded(e)),
                           "trimmed": 1 if truncated else 0}, user_id)
    final_ids = {e.id for e in edges}
    return Recall(context=context, grounded=grounded_text, unverified=unverified,
                  edges=edges, episodes=[],
                  tokens_estimated=mem._est_tokens(context), truncated=truncated,
                  recalled_edges={k: v for k, v in sem_meta.items() if k in final_ids},
                  semantic_status=sem_status,
                  as_of=AsOfAnswer(T=answer.T, now=answer.now,
                                   facts=tuple(f for f in answer.facts
                                               if f.edge.id in final_ids)))
