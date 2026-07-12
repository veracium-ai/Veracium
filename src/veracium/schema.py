"""Core memory types.

The store of record is a typed **graph** of edges (entity-centric facts and
work knowledge) plus dated **episodes** (interaction history). Both carry
provenance. A compiled "wiki" view is derived from them and cached; it is never
the source of truth.

This structure is what the research converged on (findings 20/21): the graph's
relational provenance is an unforgeable security primitive, episodes supply the
narrative the graph lacks, and an LLM curator compiles the working view. See the
`agent-memory` research repo for the evidence behind every design choice here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Provenance — shared by edges and episodes. The abstention gate reads these.
# --------------------------------------------------------------------------- #

class SourceType(str, Enum):
    STATED = "stated"      # the user told the agent directly
    OBSERVED = "observed"  # inferred from the user's behavior with the agent
    INFERRED = "inferred"  # derived from granted data (email, documents, tools)


class EvidenceAuthor(str, Enum):
    """Who authored the evidence. The core injection-resistance signal:
    third-party-authored content (e.g. received mail) is an attack surface."""
    USER = "user"                # user-authored: chat, sent mail
    THIRD_PARTY = "third_party"  # received mail, external docs — untrusted
    SYSTEM = "system"            # the agent's own observations / consolidation


class Disclosure(str, Enum):
    MENTIONABLE = "mentionable"  # may be volunteered to the user
    USE_ONLY = "use_only"        # may shape behavior; never volunteered
    QUARANTINED = "quarantined"  # unverified third-party claim; never asserted


class Provenance(BaseModel):
    source_type: SourceType
    author_of_evidence: EvidenceAuthor
    evidence_ref: str = Field(description="Stable id of the event/message/doc this derives from")
    observed_at: datetime = Field(default_factory=utcnow)
    disclosure: Disclosure = Disclosure.MENTIONABLE
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


# --------------------------------------------------------------------------- #
# Volatility — expected lifetime of a fact, independent of confidence.
# --------------------------------------------------------------------------- #

class Volatility(str, Enum):
    PERMANENT = "permanent"  # identity (gender, birthplace) — never re-confirm
    DURABLE = "durable"      # family, employer, pets — years
    SLOW = "slow"            # current project — months
    TRANSIENT = "transient"  # sick, traveling — days
    EPHEMERAL = "ephemeral"  # in a hurry today — this session


class ExpiryBehavior(str, Enum):
    CONFIRM = "confirm"  # queue for in-context reconfirmation when next relevant
    DECAY = "decay"      # confidence degrades past the expected lifetime
    LAPSE = "lapse"      # silently expire; absence of reuse means irrelevant


# Confirm where staleness is plausible and asking is natural (durable/slow —
# "still at Acme?"); silently lapse where a stale value is just irrelevant
# (transient/ephemeral — nobody asks about a flu from three months ago). Permanent
# never expires (its lifetime is None), so its behavior is never reached.
DEFAULT_EXPIRY = {
    Volatility.PERMANENT: ExpiryBehavior.LAPSE,
    Volatility.DURABLE: ExpiryBehavior.CONFIRM,
    Volatility.SLOW: ExpiryBehavior.CONFIRM,
    Volatility.TRANSIENT: ExpiryBehavior.LAPSE,
    Volatility.EPHEMERAL: ExpiryBehavior.LAPSE,
}


# --------------------------------------------------------------------------- #
# Relations — the graph's edge vocabulary. `functional` relations hold at most
# one current value per (subject, relation): a new value supersedes the old.
# --------------------------------------------------------------------------- #

class Relation(BaseModel):
    name: str
    functional: bool = False  # one current value per subject → supersede on change
    desc: str = ""  # one-clause gloss rendered into the distill prompt


# A small, extensible default registry. Hosts can add their own via config.
# Starred/functional relations supersede; the rest accumulate.
# Glosses matter: the extractor sees only these names + glosses, and confusable
# pairs (works_as vs works_on) otherwise drift between runs — which silently
# defeats supersession for facts filed under the wrong relation.
DEFAULT_RELATIONS: dict[str, Relation] = {
    r.name: r for r in [
        # user model
        Relation(name="partner_of", desc="romantic partner"),
        Relation(name="relative_of", desc="family member"),
        Relation(name="has_pet", desc="a pet: kind and name"),
        Relation(name="has_diet", desc="dietary practice or restriction"),
        Relation(name="works_as", functional=True,
                 desc="the user's employment — employer and/or role; use for jobs"),
        Relation(name="prefers", functional=True,
                 desc="a standing preference, one current value"),
        Relation(name="located_at", functional=True,
                 desc="where the user lives or is based"),
        Relation(name="health_state", functional=True,
                 desc="a current health condition or state"),
        # work knowledge
        Relation(name="works_on",
                 desc="a project, codebase, or workstream — NOT employment"),
        Relation(name="client_of", desc="a client relationship"),
        Relation(name="contact_person", desc="who to contact for what"),
        Relation(name="uses_tool", desc="a tool/service the user uses"),
        Relation(name="avoids_tool", desc="a tool/service the user avoids"),
        Relation(name="source_reliable", desc="a source that proved reliable"),
        Relation(name="source_dead_end", desc="a source that proved a dead end"),
        Relation(name="deadline", functional=True,
                 desc="a dated obligation for a named thing"),
        Relation(name="scope", functional=True,
                 desc="agreed scope of a named piece of work"),
        # the quarantine channel — third-party claims never become direct facts
        Relation(name="third_party_claim",
                 desc="an unverified claim by a third party; subject is the claimant"),
    ]
}

QUARANTINE_RELATION = "third_party_claim"


# --------------------------------------------------------------------------- #
# Store-of-record units
# --------------------------------------------------------------------------- #

class Edge(BaseModel):
    """A typed relational fact. `subject`/`object` are entity refs (e.g. 'user',
    'person:tansy', 'org:thornbury'). Bi-temporal: superseded/invalidated edges
    are retained (invalidated_at set) so history is queryable."""
    id: str
    user_id: str
    subject: str
    relation: str
    object: str
    note: str = ""
    volatility: Volatility = Volatility.DURABLE
    provenance: Provenance
    valid_from: datetime = Field(default_factory=utcnow)
    invalidated_at: Optional[datetime] = None
    invalidation_reason: Optional[str] = None  # "superseded" | "lapsed" | "decayed"
    supersedes: Optional[str] = None
    needs_confirmation: bool = False  # past its expected lifetime; may be stale

    @property
    def active(self) -> bool:
        return self.invalidated_at is None

    @property
    def quarantined(self) -> bool:
        # A quarantined edge is an unverified third-party CLAIM — never asserted
        # as fact. Benign third-party *inferences* (employer learned from a
        # received email) are not quarantined; they're marked use_only at ingest
        # (finding B: content-type quarantine, not blanket sender distrust).
        return (self.relation == QUARANTINE_RELATION
                or self.provenance.disclosure == Disclosure.QUARANTINED)

    @property
    def use_only(self) -> bool:
        # A benign third-party *inference* (finding B): may shape behavior, but
        # the user never confirmed it — never volunteered or asserted as fact.
        return self.provenance.disclosure == Disclosure.USE_ONLY

    @property
    def assertable(self) -> bool:
        """Safe to state as fact: active, not a quarantined claim, and not an
        unconfirmed third-party inference. The gate's GROUNDED bucket keys on
        this — everything else is context, not assertion material."""
        return self.active and not self.quarantined and not self.use_only


class Episode(BaseModel):
    """A dated narrative record of what happened in one interaction/event.
    Episodes are the store's memory of events; they supply the narrative the
    graph lacks. A third-party-authored episode records that a claim was
    *received*, not that it is true — the abstention gate depends on this."""
    id: str
    user_id: str
    date: str  # ISO date the event occurred (may differ from wall clock)
    summary: str
    provenance: Provenance
