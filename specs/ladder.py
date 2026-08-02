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
