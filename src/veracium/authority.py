"""Supersession authority — the ladder, capped by provenance (specs/0003).

This is the runtime home of the rule `specs/ladder.py` generates its tables from.
Before 0003, the ladder lived only in `specs/ladder.py` (a spec-support module) and
nothing in `src/` computed authority — the functional-supersession loop retired any
differing value regardless of who reported it (`graph.py:139`, the reported defect).

`specs/ladder.py` now imports `_RUNGS`, `effective` and `permitted` from here, so the
rule the code runs and the rule the generated tables state are **one object** (§4a) —
they cannot drift the way v1's hand-written `ASSISTANT` row did.

The rule (§3):

    USER 3  >  SYSTEM 2  >  ASSISTANT 1  >  THIRD_PARTY 0

    effective = min(AUTH[author_of_evidence], AUTH[derived_from or author])

A retirement is permitted only when the incoming edge's *effective* authority is
>= the prior's. `min` caps by provenance — a SYSTEM summary of an attacker's email
(`derived_from=THIRD_PARTY`) scores 0 and retires nothing — using machinery that
already exists rather than splitting the enum (research's Q2 answer).
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Optional

from .schema import EvidenceAuthor

if TYPE_CHECKING:  # avoid a runtime import cycle (schema is always safe; Edge is used only for typing)
    from .schema import Edge


# Rungs for every class that could exist. Only the shipped `EvidenceAuthor` members
# are ever indexed; `assistant` is listed so the map does not need editing when
# specs/0001 lands and the enum gains that member (the ladder regenerates from the
# enum, this map is the superset it draws from).
_RUNGS: dict[str, int] = {"user": 3, "system": 2, "assistant": 1, "third_party": 0}


# `rule_version` stamps WHICH policy refused, so specs/0011 can re-evaluate historical
# refusals. It names the WHOLE policy — the ladder AND the min-capping. Any change that
# could flip whether a pair is allowed or refused REQUIRES a new value (§4f).
# v2 (specs/0011 §4b): the SUBJECT axis joined the policy — a USER
# self-assertion is additionally refused from retiring any OTHER-subject
# prior. A refusal-widening flips pairs from allowed to refused, which is
# exactly the change class this constant exists to version.
RULE_VERSION = "supersession-authority-v2"


def effective(author: EvidenceAuthor, derived_from: Optional[EvidenceAuthor]) -> int:
    """Capped authority: provenance may lower it, never raise it (§3).

    `min` is the whole reason SYSTEM keeps rung 2 without splitting the enum — a
    system summary of an attacker's email scores 0, host state scores 2.
    """
    return min(_RUNGS[author.value], _RUNGS[(derived_from or author).value])


def permitted(prior_author: EvidenceAuthor, prior_from: Optional[EvidenceAuthor],
              inc_author: EvidenceAuthor, inc_from: Optional[EvidenceAuthor]) -> bool:
    """A retirement is permitted only by an equal-or-better-entitled party (§4a)."""
    return effective(inc_author, inc_from) >= effective(prior_author, prior_from)


def self_assertion(author: EvidenceAuthor,
                   derived_from: Optional[EvidenceAuthor]) -> bool:
    """specs/0011 §4b: the chain carries nothing but the user's own
    authority — computed by THIS module's `effective()`, never by the
    presence or absence of a marker (round 3, R3-1: `derived_from is
    None` let `derived(USER)` — identical authority — buy permission;
    keying on authority makes exactly two chains qualify, (USER, None)
    and (USER, USER), by construction rather than enumeration)."""
    return effective(author, derived_from) == effective(
        EvidenceAuthor.USER, None)


def edge_effective(edge: "Edge") -> int:
    """The recorded effective authority of an edge, from its provenance."""
    return effective(edge.provenance.author_of_evidence, edge.provenance.derived_from)


def scope_fingerprint(edges: list["Edge"]) -> str:
    """A canonical, complete fingerprint of the (user, subject, relation) scope a
    plan was computed from — the CAS token for `apply_supersession_plan` (§4f, I9).

    **Complete, not just the active-set (round-9 correction C).** A plan's decision
    reads each candidate's value, `author_of_evidence`, `derived_from`, disclosure and
    validity — so the fingerprint covers all of them. An in-place edit to a same-id row
    that a coarse active-set token would miss changes this fingerprint, so the plan is
    rejected as `PlanStale`. Over-sensitivity only costs a retry; it never misses a
    stale read. Ordered by edge id so it is independent of read order.
    """
    rows = sorted(
        (e.id,
         e.object,
         e.provenance.author_of_evidence.value,
         e.provenance.derived_from.value if e.provenance.derived_from else None,
         e.provenance.disclosure.value,
         e.active)
        for e in edges)
    blob = json.dumps(rows, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
