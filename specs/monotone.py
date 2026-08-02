"""The N9 relation, as executable code.

specs/0002 v7 stated N9 as a product of per-field comparisons including

    post.invalidation_reason == pre.invalidation_reason

which forbids the first-time retirement the trust matrix calls clean: expiry
moves that field from None to "lapsed". The seventh external review caught it.
Equality is right for an ALREADY-RETIRED edge and wrong for THE TRANSITION THAT
RETIRES IT.

The relation is written here rather than in prose, and the spec's table is
generated from it, so the rule and its statement cannot disagree -- the same
move that fixed the authority ladder in specs/0003.
"""
from __future__ import annotations

# MENTIONABLE > USE_ONLY > QUARANTINED
DISCLOSURE_RANK = {"quarantined": 0, "use_only": 1, "mentionable": 2}

# Which operation may assign each reason. A reason is not a free-text label:
# it says what happened, and only the operation that did that may claim it.
REASON_OWNER = {
    "lapsed":             "expire()",
    "decayed":            "expire()",
    "superseded":         "supersede_edge()  (specs/0003)",
    "absorbed_duplicate": "supersede_edge()  (specs/0003)",
    "corrected":          "correct()",
    "disputed":           "dispute()",
}
# Reasons an EVIDENCE-FREE operation may assign. `corrected` and `disputed` are
# authorised acts, `superseded`/`absorbed_duplicate` arrive with new evidence --
# none of those is evidence-free, so none may be assigned under N9.
EVIDENCE_FREE_REASONS = {"lapsed", "decayed"}


def _rank(d):
    return DISCLOSURE_RANK[d.value if hasattr(d, "value") else d]


def violations(pre, post, *, evidence_free: bool = True) -> list[str]:
    """Every N9 clause `post` breaks relative to `pre`. Empty list = holds."""
    v = []

    # -- the retirement transition, which v7 got wrong --------------------
    if not pre.active:
        if post.active:
            v.append("a retired edge was reactivated")
        if post.invalidation_reason != pre.invalidation_reason:
            v.append(f"why an edge retired was rewritten: "
                     f"{pre.invalidation_reason!r} -> {post.invalidation_reason!r}")
    elif not post.active:
        # THE transition. A reason must be assigned, and must be one this
        # operation class is entitled to assign.
        r = post.invalidation_reason
        if not r:
            v.append("an edge was retired without recording why")
        elif r not in REASON_OWNER:
            v.append(f"unknown invalidation reason {r!r}")
        elif evidence_free and r not in EVIDENCE_FREE_REASONS:
            v.append(f"an evidence-free operation claimed reason {r!r}, "
                     f"which belongs to {REASON_OWNER[r]}")
    else:
        if post.invalidation_reason != pre.invalidation_reason:
            v.append("invalidation_reason changed on an edge that stayed active")

    # -- monotone narrowing ------------------------------------------------
    if post.assertable > pre.assertable:
        v.append("assertability widened")
    if post.needs_confirmation < pre.needs_confirmation:
        v.append("a staleness caveat was cleared")
    if _rank(post.provenance.disclosure) > _rank(pre.provenance.disclosure):
        v.append("disclosure widened")
    if post.provenance.confidence > pre.provenance.confidence:
        v.append("confidence was raised")
    if post.provenance.observed_at > pre.provenance.observed_at:
        v.append("currency was advanced without new evidence")

    # -- categorical: any change rewrites provenance -----------------------
    if post.provenance.author_of_evidence != pre.provenance.author_of_evidence:
        v.append("authorship was rewritten")
    if post.provenance.derived_from != pre.provenance.derived_from:
        v.append("derivation was rewritten")
    if post.valid_from != pre.valid_from:
        v.append("first-known date was mutated")
    return v


def holds(pre, post, **kw) -> bool:
    return not violations(pre, post, **kw)
