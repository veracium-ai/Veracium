"""The supersession authority ladder, and every table derived from it.

specs/0003 v1 stated the ladder as one line of arithmetic and then wrote its
consequences out in prose. Two of the four ASSISTANT cases were inverted --
including `assistant -> third_party`, the unsafe direction -- while the document
being transcribed from had all four right. The first external review caught it.

A consequence of a rule should be computed from the rule. Everything below is.
"""

AUTH = {"user": 3, "system": 2, "assistant": 1, "third_party": 0}
CLASSES = ("user", "system", "assistant", "third_party")


def effective(author: str, derived_from: str | None) -> int:
    """Capped authority: provenance may lower it, never raise it.

    `min` is the whole reason SYSTEM can keep rung 2 without splitting the enum
    -- a system summary of an attacker's email scores 0, host state scores 2.
    """
    return min(AUTH[author], AUTH[derived_from or author])


def permitted(prior_author, prior_from, inc_author, inc_from) -> bool:
    """A retirement is permitted only by an equal-or-better-entitled party."""
    return effective(inc_author, inc_from) >= effective(prior_author, prior_from)


def author_matrix() -> list[tuple[str, str, bool]]:
    """The raw-author table, no derivation. 16 rows once ASSISTANT exists."""
    return [(p, i, permitted(p, None, i, None)) for p in CLASSES for i in CLASSES]


def effective_matrix() -> list[tuple[str, str | None, str, str | None, bool]]:
    """The FULL product the rule actually operates on.

    The review's finding 2: v1's I1 enumerated author pairs, but the rule reads
    `min(author, derived_from)`, so each edge has two authority inputs and the
    interesting cases are exactly where raw and effective authority differ.
    """
    opts = [None, *CLASSES]
    return [(pa, pf, ia, if_, permitted(pa, pf, ia, if_))
            for pa in CLASSES for pf in opts
            for ia in CLASSES for if_ in opts]


def divergent() -> list:
    """Rows where the capped answer differs from the raw-author answer.

    These are the cases a matrix over authors alone cannot see, and the ones an
    attacker reaches by omitting `derived_from`.
    """
    return [r for r in effective_matrix()
            if r[4] != permitted(r[0], None, r[2], None)]


# --- disclosure, so contention routing is computed rather than reasoned -----
# specs/0003 v4 argued from the six author-only blocked pairs and concluded
# "exactly one pair puts both values in the grounded block". Over the real
# 400-state product that is 44 states across six author shapes: derivation caps
# by `assistant` and `system` lower authority WITHOUT changing disclosure, and
# the author-only projection cannot see them.

def disclosure(author: str, derived_from: str | None) -> str:
    """Mirrors ingest._disclosure_for for a non-quarantine relation."""
    if author == "third_party" or derived_from == "third_party":
        return "use_only"
    return "mentionable"


def blocked_states() -> list[tuple]:
    opts = [None, *CLASSES]
    return [(pa, pf, ia, if_) for pa in CLASSES for pf in opts
            for ia in CLASSES for if_ in opts
            if not permitted(pa, pf, ia, if_)]


def same_block_contention() -> list[tuple]:
    """Blocked states where both edges land in the SAME read partition.

    These are the ones a reader sees as two competing values; the rest are
    already separated by the existing gate.
    """
    return [b for b in blocked_states()
            if disclosure(b[0], b[1]) == disclosure(b[2], b[3])]
