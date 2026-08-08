"""The supersession authority ladder, and every table derived from it.

specs/0003 v1 stated the ladder as one line of arithmetic and then wrote its
consequences out in prose. Two of the four ASSISTANT cases were inverted --
including `assistant -> third_party`, the unsafe direction -- while the document
being transcribed from had all four right. The first external review caught it.

A consequence of a rule should be computed from the rule. Everything below is.
"""

# Authority is derived from the SHIPPED enum, not restated here. v5 hard-coded
# four classes including `assistant`, which does not exist in
# `veracium.schema.EvidenceAuthor` -- so the generated 400-state tables modelled
# a rule the runtime cannot implement, and the "the code and the table are one
# object" claim was false in the direction that matters.
#
# `ASSISTANT` arrives with specs/0001, which is `deferred`. Until then this
# generates the CURRENT product; when 0001 lands the enum gains a member and
# these tables regenerate with no edit here.
try:
    from veracium.schema import EvidenceAuthor as _E
    CLASSES = tuple(e.value for e in _E)
except ImportError as exc:                        # pragma: no cover
    # FAIL, do not fall back. A hard-coded default is exactly the drift this
    # grounding removed: v5 hard-coded four classes and generated tables for a
    # rule the runtime cannot execute. A wrong table is worse than no table.
    raise SystemExit(
        f"specs/ladder.py needs the veracium package importable "
        f"({exc}).\n\nRun it with the same interpreter and environment you use "
        f"for pytest, with the source on the path:\n"
        f"    PYTHONPATH=src python3 specs/render_ladder.py --check\n\n"
        f"It derives the authority classes from EvidenceAuthor and imports the "
        f"production disclosure rule, so it cannot be checked without them.") from None

# The rungs AND the rule now live in the RUNTIME module `veracium.authority`, and
# are imported here so the code the store runs and the tables this file generates
# are one object (specs/0003 §4a). v1 hand-wrote the ASSISTANT row from the same
# arithmetic and inverted two of four cases; a shared implementation cannot diverge.
# The string-typed wrappers below keep this file's table generators unchanged while
# delegating every authority decision to the runtime rule.
from veracium.authority import _RUNGS  # noqa: E402  (import after the enum-grounding guard)
from veracium.authority import effective as _effective
from veracium.authority import permitted as _permitted

AUTH = {c: _RUNGS[c] for c in CLASSES}


def effective(author: str, derived_from: str | None) -> int:
    """Capped authority — delegates to the runtime rule (`veracium.authority`)."""
    return _effective(_E(author), _E(derived_from) if derived_from else None)


def permitted(prior_author, prior_from, inc_author, inc_from) -> bool:
    """A retirement is permitted only by an equal-or-better-entitled party."""
    return _permitted(_E(prior_author), _E(prior_from) if prior_from else None,
                      _E(inc_author), _E(inc_from) if inc_from else None)


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
    """The PRODUCTION rule, imported -- not a second implementation.

    v5 reimplemented this here and the copy drifted: it treated ordinary
    assistant content as `mentionable`, while specs/0001 v3 places it in
    `use_only` for every subject. The contention count generated from the copy
    was therefore neither the current runtime answer nor the post-0001 one.
    """
    from veracium.ingest import _disclosure_for
    from veracium.schema import EvidenceAuthor
    return _disclosure_for(EvidenceAuthor(author), "works_as",
                           EvidenceAuthor(derived_from) if derived_from else None).value


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
