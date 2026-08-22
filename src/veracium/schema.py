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

from pydantic import BaseModel, Field, model_serializer, StrictBool


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Provenance — shared by edges and episodes. The abstention gate reads these.
# --------------------------------------------------------------------------- #

# specs/0016 D2: `SourceType` and `Provenance.source_type` are DELETED (the
# D1 deprecation cycle's named removal). The field gated nothing and could not
# be honestly attested; the vocabulary is freed for the frozen evidence_basis
# contract (0016 §1b — NOT shipped here). Historical `source_type` keys in
# stored JSON and ≤6 export files are dropped on read (pydantic extra=ignore;
# portability strips them explicitly at import).


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


# --------------------------------------------------------------------------- #
# Confirmation — specs/0008. `confirm()` is the ONLY path that clears
# `needs_confirmation`, so its metadata is a CLOSED, validated surface: a
# free-form string would quietly turn the audit record into a content store
# (§6b/§6c). Both fields are audit metadata and grant NOTHING — authority comes
# from the protected `confirm()` call path, not from any label (§6a, C2a).
# --------------------------------------------------------------------------- #
class ConfirmationCallPath(str, Enum):
    """Which entry point invoked the confirmation. `0008` has one — the host
    API, never model-reachable (§2c-ii). A closed enum so an unknown value is
    rejected rather than stored as free text; recording *which* privileged path
    was used, and gating it, is evidence-basis's concern and on no roadmap (§4)."""
    HOST_API = "host_api"


class ConfirmationActor(str, Enum):
    """Who the host attributes the confirmation to — audit metadata, embedded in
    the confirmation episode's summary. Closed (§6b, finding 7): `actor` used to
    be a free-form string embedded in a content-bearing episode, so a host could
    smuggle prose past the constraints on the other fields."""
    USER = "user"   # the default: the user affirmed the fact
    HOST = "host"   # the host application affirmed on the user's behalf


# The confirmation RULE's identity. It enters the idempotency digest (§6c) so a
# request replayed after the rule changed does not collide with the old digest.
# Tied to the spec that defines the rule; bump if the clearing rule changes.
CONFIRMATION_RULE_VERSION = "0008"

_CORRELATION_ID_RE = __import__("re").compile(r"[A-Za-z0-9._:-]{1,64}")


def validate_correlation_id(value: str) -> str:
    """`correlation_id` is opaque, ≤64 chars, `[A-Za-z0-9._:-]` (§6c). Validated
    BEFORE any mutation (C9). Raises `ValueError` on anything else."""
    if not (isinstance(value, str) and _CORRELATION_ID_RE.fullmatch(value)):
        raise ValueError(
            f"correlation_id must be ≤64 chars of [A-Za-z0-9._:-], not "
            f"{value!r} — it is an opaque idempotency key, not a content field")
    return value


class Confirmation(BaseModel):
    """The mandatory audit record of one confirmation (§6b) — the store writes it
    in the SAME transaction as the flag transition; if it cannot commit, the
    confirmation fails and the flag stays set (C7). `request_digest` is the
    canonical-request identity used to tell a true replay from a collision (§6c)."""
    id: str
    user_id: str
    edge_id: str
    confirmed_at: datetime
    actor: ConfirmationActor
    call_path: ConfirmationCallPath
    correlation_id: str
    request_digest: str
    replayed: bool = False        # runtime only: True when returned for a replay,
    #                               not a persisted column (§6c)


class Provenance(BaseModel):
    author_of_evidence: EvidenceAuthor
    evidence_ref: str = Field(description="Stable id of the event/message/doc this derives from")
    observed_at: datetime = Field(default_factory=utcnow)
    disclosure: Disclosure = Disclosure.MENTIONABLE
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    # Authorship is per-event, but an event's CONTENT can embed lower-trust
    # material (a system-authored triage verdict quoting a received email's
    # subject). derived_from declares that: trust is capped at the minimum of
    # author and derived_from, closing the "system-event laundering" bypass.
    derived_from: Optional[EvidenceAuthor] = None
    # specs/0006 — source identity, the pair (origin, source_id). DIAGNOSTIC ONLY
    # (I5: it groups, never grants — affects no trust/authority/disclosure/staleness/
    # supersession decision in v1). `source_id`: opaque, host-supplied, NEVER model- or
    # extractor-derived (I1). `origin`: a STORE-minted collision namespace, never set by
    # a local caller (I2a); ABSENT on a local record and resolved to the store_identity
    # singleton at read (§4 rule 6) — a foreign/imported record keeps its own (I2b).
    # Both optional; absent = unknown = least favourable (I3). Non-empty and length-
    # bounded (§4 rule 5 — an empty string is not a valid opaque id).
    source_id: Optional[str] = Field(default=None, min_length=1, max_length=512)
    origin: Optional[str] = Field(default=None, min_length=1, max_length=512)

    @property
    def third_party_influenced(self) -> bool:
        """True if a third party authored the evidence OR influenced its content
        (derived_from). The gate and the wiki compiler key episode routing on
        this — never on authorship alone."""
        return (self.author_of_evidence == EvidenceAuthor.THIRD_PARTY
                or self.derived_from == EvidenceAuthor.THIRD_PARTY)


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
        Relation(name="measures", functional=True,
                 desc="a changing quantity with one current value — weight, "
                      "reading progress, savings balance, score; the number "
                      "updates, history is kept"),
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

# specs/0025 (accepted v13) — the reserved registry members, module constants
# on the QUARANTINE_RELATION pattern. `unclassified` is the NON-FUNCTIONAL
# fallback every off-vocabulary relation lands on (§4b); its gloss is
# spec-authored and it is NEVER extractor-selectable (§4b-iv — the prompt
# renderer excludes it). `third_party_claim`'s canonical form IS the shipped
# DEFAULT_RELATIONS entry above. A host entry bearing either name must match
# the canonical form COMPLETELY (functional AND desc) or the boundary
# refuses it (§4b-ii step 3); both are injected when absent (X8).
UNCLASSIFIED_RELATION = "unclassified"
RESERVED_RELATIONS = {
    UNCLASSIFIED_RELATION: Relation(
        name=UNCLASSIFIED_RELATION, functional=False,
        desc="reserved fallback for off-vocabulary relations; "
             "never extractor-selectable"),
    QUARANTINE_RELATION: DEFAULT_RELATIONS[QUARANTINE_RELATION],
}


# --------------------------------------------------------------------------- #
# Store-of-record units
# --------------------------------------------------------------------------- #

# specs/0004 W5 — the invalidation-reason registries. TWO constants, not one,
# and the split carries §4's polarity into the code:
#
#   WIKI_RETAINING_REASONS is what the RUNTIME consults: membership → the wiki
#   survives the invalidation; every other reason — including one no spec has
#   named yet — DROPS it. The runtime never branches on a drop-list, so the
#   registry can only fail the build, never widen what is served (internal R1:
#   v2 had this inverted, retaining on an unknown reason, which serves revoked
#   content if the unknown reason meant "revoked").
#
#   DISPOSITIONED_REASONS is the process record W5's registry test diffs
#   against: every reason any producer can pass, each explicitly dispositioned.
#   A producer growing a new reason fails test_invalidation_reason_registry_is
#   _total until the spec that adds it dispositions it here.
#
# "revoked_source" is the seat specs/0022 reserves: a sole-basis survivor
# retired by the revocation sweep drops the wiki through this registry.
WIKI_RETAINING_REASONS: frozenset = frozenset({
    "lapsed",              # W3 — staleness is not a trust event
    "decayed",             # W3
    "absorbed_duplicate",  # W8 / W-Q1 — absorption is trust-preserving
})
DISPOSITIONED_REASONS: dict = {
    "disputed": "drop",            # W1 — the host revoked its trust
    "corrected": "drop",           # the host replaced the content
    "superseded": "drop",          # W2 — the supersession path
    "revoked_source": "drop",      # 0022's sweep (reserved seat)
    "lapsed": "retain",            # W3
    "decayed": "retain",           # W3
    "absorbed_duplicate": "retain",  # W8
}


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
    invalidation_reason: Optional[str] = None  # "superseded" | "lapsed" | "decayed" | "disputed" | "corrected" | "absorbed_duplicate"
    supersedes: Optional[str] = None
    # specs/0025 (accepted v13): the original relation for ANY structural
    # re-disposition — written ONLY by the vocabulary fallback (and, when
    # 0024 lands, its coherence rewrite; the pair's ONE definition, 0025 §2).
    # None everywhere else, and OMITTED from every serialization when None
    # (the field-level rule below) so an unaffected Edge's serialized JSON
    # is byte-identical to its pre-0025 shape — X6's first preserved carrier.
    original_relation: Optional[str] = None
    needs_confirmation: bool = False  # past its expected lifetime; may be stale

    @model_serializer(mode="wrap")
    def _omit_none_original_relation(self, handler):
        # specs/0025 §2 (round 2, R2-3): an optional field still serializes
        # its None and breaks every byte contract — so when None, the key is
        # ABSENT from model_dump AND model_dump_json, at every call site.
        d = handler(self)
        if d.get("original_relation") is None:
            d.pop("original_relation", None)
        return d
    # specs/0019: "the specifics in this fact's object were not all grounded in
    # the event text it was extracted from" — a property of the EXTRACTION,
    # never of the fact's truth. Derived once at ingest (§4b); a STORED row's
    # flag never changes (§4d — the store refuses every same-ID transition);
    # strengthening exists only pre-persist via absorption's N-ary OR.
    # StrictBool (F7): plain bool COERCES "yes"/0/1; the strict form refuses
    # every non-boolean — the 0005 P13 closed-predicate posture.
    ungrounded: StrictBool = False
    # Outcome aggregates — DERIVED, mutable-by-design life-history (recomputable
    # from the kind="outcome" episode record; engine-written via record_outcome,
    # never provenance and never an MCP surface). times_used counts uses the
    # host explicitly acted on, not recalls.
    times_used: int = 0
    outcome_counts: dict[str, int] = Field(default_factory=dict)
    last_outcome: Optional[Outcome] = None
    last_outcome_at: Optional[datetime] = None

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


class Outcome(str, Enum):
    """Did a conclusion built on memory survive contact with reality?
    Actor provenance rides on the outcome episode's authorship: human
    judgments are USER-authored (strong), LLM-judge opinions SYSTEM-authored
    (weak — a flag, never truth). Completion is not confirmation: most uses
    stay UNREVIEWED forever, and unreviewed repetition must never accumulate
    authority (the laundering failure class, via repetition)."""
    UNREVIEWED = "unreviewed"    # used, no judgment yet (the default; most stay here)
    CONFIRMED = "confirmed"      # human marked the conclusion correct
    CORRECTED = "corrected"      # human supplied the true value (strongest signal)
    CHALLENGED = "challenged"    # LLM judge disagreed — evidence-to-review
    CONCURRED = "concurred"      # LLM judge agreed — weak positive


class Episode(BaseModel):
    """A dated narrative record of what happened in one interaction/event.
    Episodes are the store's memory of events; they supply the narrative the
    graph lacks. A third-party-authored episode records that a claim was
    *received*, not that it is true — the abstention gate depends on this.

    `kind="outcome"` episodes are the outcome-tracking record (source of
    truth for the edge-level aggregate counters, which are derived state):
    each records one use-and-judgment of `edge_id`, upgradeable in place from
    UNREVIEWED when a later judgment arrives with the same evidence_ref."""
    id: str
    user_id: str
    date: str  # ISO date the event occurred (may differ from wall clock)
    summary: str
    provenance: Provenance
    kind: str = "interaction"           # "interaction" | "outcome"
    edge_id: Optional[str] = None       # outcome episodes: the edge judged
    outcome: Optional[Outcome] = None   # outcome episodes: current status
    context_ref: Optional[str] = None   # optional comparability key (e.g. rubric hash)
    # specs/0014 §4c (R5-3/R6-3): STORE-ASSIGNED consolidation output identity —
    # the position of this output within its operation's outputs. ONLY
    # `write_consolidation_output_if_current` may set it; caller-supplied values
    # on generic paths are REFUSED (fabricated store identity). Serialized in
    # the existing json blob; the EXPORT path emits it with exclude-none
    # semantics (omitted when None — R7-3's stated exception), and an explicit
    # JSON null on import is malformed. FORMAT_VERSION 4→5 rides on this field.
    consolidation_output_index: Optional[int] = None

    # --- specs/0022 §4b-ii (R18; internal S1) — episode retirement -----------
    # Quentin's ruled mechanism (2026-08-17): a JSON field plus the
    # store.episodes() read seam, no DDL. The sweep retires an episode whose
    # resolved source identity is revoked, exactly as it retires an edge;
    # store.episodes() default-EXCLUDES retired rows so every reader inherits
    # the exclusion, and Q9's successor spec owns a first-class carrier.
    retired_reason: Optional[str] = None
    retired_at: Optional[datetime] = None

    # --- specs/0023 §4a (N12/N14/N15; internal S3, external F1) --------------
    # DERIVED, never stored, mirroring Edge's pair: the value already exists
    # in `disclosure` (and, post-0022, in `retired_reason`), and a second
    # stored copy is a second source of truth. The reason neither existed is
    # the reason S3 and F1 both happened — five readers could not consult a
    # property nobody had derived for this type, so each invented its own.
    @property
    def quarantined(self) -> bool:
        return self.provenance.disclosure == Disclosure.QUARANTINED

    @property
    def use_only(self) -> bool:
        # SUBSUMES the legacy signal: pre-0023 episodes carry the DEFAULT
        # disclosure (ingest never set one — S3's finding), so disclosure
        # alone would read a stored third-party episode as assertable. The
        # derived property is the floor of both carriers; disclosure is the
        # forward carrier ingest now writes, and third_party_influenced keeps
        # every legacy row fenced exactly as the open-coded sites fenced it.
        return (self.provenance.disclosure == Disclosure.USE_ONLY
                or self.provenance.third_party_influenced)

    @property
    def active(self) -> bool:
        # 0022 §4b-ii: retirement is the episode's active/inactive axis
        return self.retired_reason is None

    @property
    def assertable(self) -> bool:
        """THE SHARED PREDICATE the text consumers call (0023 §4a-iv): safe
        to render as ordinary narrative — active (not retired by 0022's
        sweep), not a quarantined claim, not an unconfirmed third-party
        inference. LIFECYCLE MUST NOT CALL THIS (the §7a lifecycle row,
        internal R3-3): expiry applies to fenced content too, and routing
        lifecycle through assertable dropped ordinary quarantined episodes
        from aging in stores with zero revocations."""
        return self.active and not self.quarantined and not self.use_only

    # --- specs/0009 outcome-authorship chain (append-only history) --------------
    # Store-assigned, OUTCOME-ONLY (None on any non-outcome episode). Never
    # host-supplied: `append_outcome_if_head` mints them. `seq` is the per-chain
    # authority order (root == 1, contiguous); `supersedes_episode` links to the
    # in-chain predecessor (None at the root). `judgment_time_known` is REQUIRED
    # True/False on every v3 outcome record: True when `date` is the real judgment
    # time, False on a legacy-converted root whose `date` is the original use date
    # (H1/H8/H12). `judgment_time_known == False ⇒ seq == 1 ∧ supersedes_episode is None`.
    seq: Optional[int] = None
    supersedes_episode: Optional[str] = None
    judgment_time_known: Optional[bool] = None

    # --- specs/0010 crash-safe consolidation ------------------------------------
    # `claimed_by`/`operation_id`: on a claimed INPUT while an operation holds it
    # (cleared on release). `lineage`: on a consolidated OUTPUT, the whole claimed
    # set it absorbed (HistoricalEpisodeId strings — a namespace no live id inhabits,
    # X19); non-empty lineage is the sole "this is an output" discriminator (X16/X18).
    # `date_start`/`date_end`: the min/max input dates on an output; `date := date_start`.
    claimed_by: Optional[str] = None
    operation_id: Optional[str] = None
    lineage: Optional[list[str]] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None


class OutcomeJudgmentDraft(BaseModel):
    """The caller-owned payload of one outcome judgment (specs/0009 §4a, H9).

    STRUCTURALLY excludes every store-owned field — no `id`, `seq`,
    `supersedes_episode`: the Store's `append_outcome_if_head` mints identity
    and allocates the per-chain `seq`. Making "store-assigned" a
    property of the type is what stops a caller-supplied `seq`/`id` turning an
    append into a replace. `summary` is built by `Memory.record_outcome` before
    the Store boundary (it carries corrected-value text); `context_ref` is
    inherit-on-omit for a non-root append."""
    author: EvidenceAuthor
    event_timestamp: str
    outcome: Outcome
    summary: str
    context_ref: Optional[str] = None


# --- specs/0010 crash-safe consolidation ------------------------------------

# A consolidation output's `lineage` ids live in a namespace NO live Episode id can
# inhabit (X19): once a generation finalizes, its absorbed inputs are gone and their
# ids become HISTORICAL references — so `add_episode`/import may never mint or accept
# a live episode whose id is in this namespace, and the two can never collide.
HISTORICAL_PREFIX = "hist:"


def to_historical_id(episode_id: str) -> str:
    """The deterministic (retry-stable, no persisted map) HistoricalEpisodeId for a
    now-absorbed input — X19. Idempotent: already-historical ids pass through."""
    return episode_id if episode_id.startswith(HISTORICAL_PREFIX) \
        else f"{HISTORICAL_PREFIX}{episode_id}"


def is_historical_id(episode_id: str) -> bool:
    return episode_id.startswith(HISTORICAL_PREFIX)


class ConsolidationState(str, Enum):
    """The durable state machine of one crash-safe consolidation (specs/0010 §4b-ii).
    CLAIMED→GENERATING→OUTPUTS_DURABLE→FINALIZED is the happy path; ABANDONED is the
    cleanup-complete state a new fence may revive. OUTPUTS_DURABLE is the point of no
    return — before it nothing counts, after it everything does."""
    CLAIMED = "claimed"
    GENERATING = "generating"
    OUTPUTS_DURABLE = "outputs_durable"
    FINALIZED = "finalized"
    ABANDONED = "abandoned"


# Ops in these states are recovery-pending (pending_consolidations, X13) — NOT
# FINALIZED (done) and NOT ABANDONED (quiescent, revived only by takeover).
RECOVERY_PENDING_STATES = (ConsolidationState.CLAIMED, ConsolidationState.GENERATING,
                           ConsolidationState.OUTPUTS_DURABLE)


class ConsolidationOp(BaseModel):
    """The persistent operation record (specs/0010 §4a) — a fence alone orders but does
    not prove liveness, so the whole record is durable. `owner` is COOPERATIVE identity
    (§4a-ii), not an auth capability. `lease_duration` is a persisted bounded duration
    (seconds); the STORE sets `lease_expires_at = store_now + lease_duration`, so
    renewal has one durable source that survives restart. Every `claimed_id` belongs to
    `user_id`, and `forget_user()` erases the record with the rest of that user."""
    user_id: str
    operation_id: str
    fence: int
    state: ConsolidationState
    owner: str
    lease_duration: int              # seconds; 0 < lease_duration <= LEASE_MAX
    lease_expires_at: str            # RFC3339 UTC, store-clock-derived
    claimed_ids: list[str]


class ConsolidationOutputDraft(BaseModel):
    """The worker-owned payload of ONE consolidation output (specs/0010 §4b-ii, X22) —
    the exact store-assigned-identity shape `OutcomeJudgmentDraft` uses. STRUCTURALLY
    excludes every store-owned field — no `id`, `user_id`, `operation_id`, `claimed_by`,
    `lineage`: the store mints a fresh id, BINDS the operational fields to the fenced op
    (`lineage == op.claimed_ids`), INSERTs (never replaces), and DERIVES the trust floor
    + date range from `op.claimed_ids`, not from this draft (X23). `date_start`/`date_end`
    are the LLM's proposal; the store validates them against the claimed set (§4d-ii)."""
    summary: str
    date_start: str
    date_end: str


# --- supersession authority (specs/0003) ---------------------------------------
# The write-time supersession outcome is applied as ONE atomic, CAS-linearized plan
# (§4f). These are the plan the write layer computes, the durable refusal record the
# store keeps, and the result the store returns. Content-free by construction: a refusal
# carries opaque edge ids, the relation and two authority levels — never subject/object/
# note (§4b). RULE_VERSION and effective-authority live in `veracium.authority`.

class ContributionDraft(BaseModel):
    """specs/0014 §4b — what a consumption site emits: REFERENCES ONLY (R2-1).
    The store derives identity digests and the payload from authoritative rows
    inside the consuming transaction; there is no caller-supplied payload. A
    draft that does not resolve to a row this transaction is consuming — or
    resolves to another tenant's row — aborts the whole op (A7)."""
    site: str                      # 'absorption' | 'consolidation' (closed set)
    survivor_type: str             # 'edge' | 'episode' (R1-5: independent namespaces)
    survivor_id: str
    contributor_type: str
    contributor_id: str


class ContributionRecord(BaseModel):
    """A ledger row as read back (specs/0014 §4a/§4d). Content-free: identity
    is digests; `payload` carries scalar field names and values only.
    `contributor_type`/`contributor_ref` are the SCHEMA-v8 typed contributor
    link (0021 §7b, the 0014 amendment; the 0019 rider): populated on new
    native absorption rows from the draft's `contributor_type`/`contributor_id`;
    None on legacy (pre-v8) rows."""
    id: str
    user_id: str
    survivor_type: str
    survivor_id: str
    site: str
    identity_digest: Optional[str]
    evidence_ref_digest: Optional[str]
    payload: dict
    op_key: Optional[str]
    created_at: datetime
    contributor_type: Optional[str] = None
    contributor_ref: Optional[str] = None


class SupersessionRefusalDraft(BaseModel):
    """One refused retirement, as the write layer proposes it. The store BINDS the
    identity fields (mints `refusal_id`/`created_at`, stamps `rule_version`, validates
    `incoming_edge_id` == the plan's incoming edge and `prior_edge_id` belongs to the
    user) so a malformed caller cannot forge a refusal against an edge this commit does
    not write or another user's edge (§4f, round-6 correction C)."""
    prior_edge_id: str
    incoming_edge_id: str
    relation: str
    prior_effective: int
    incoming_effective: int


class SupersessionPlan(BaseModel):
    """The WHOLE persistent outcome of one supersession, computed from a store read and
    applied all-or-nothing conditional on `expected_state` (§4f, I9).

    `insert_incoming` is EXPLICIT because the plan type decides what is representable:
    reinforcement PERSISTS the incoming edge and touches nothing else (`True`, accepted
    `0012` Design 1 — the pre-0012 refresh-and-discard form is withdrawn); absorption
    and ordinary supersession insert the incoming edge (`True`). `prior_upserts` are
    in-place refreshes (absorption notes; reinforcement no longer writes one — `0012`); `prior_invalidations`
    are `(edge_id, at, reason)` retirements/absorptions. `expected_state` is the complete
    scope fingerprint (`authority.scope_fingerprint`) the plan assumed; `operation_id` is
    the whole-plan idempotency key. `rule_version`/`store_version`/cache effects are
    Store-owned, not carried here."""
    incoming_edge: Edge
    insert_incoming: bool
    operation_id: str
    expected_state: str
    prior_upserts: list[Edge] = Field(default_factory=list)
    prior_invalidations: list[tuple[str, datetime, str]] = Field(default_factory=list)
    refusals: list[SupersessionRefusalDraft] = Field(default_factory=list)
    # specs/0014 (plan-transient — never persisted as such):
    # `contribution_drafts` — reference-only drafts, one per absorbed prior (§4b);
    # the store enforces EXACT SET EQUALITY with the plan's `absorbed_duplicate`
    # invalidations (R5-1). `absorption_pre_image` — the incoming edge's ORIGINAL
    # values over the closed §4a field set, snapshotted BEFORE the planner's
    # inheritance mutation (R3-1; canonical key order); it is the `base` side of
    # every absorption payload and enters the v2 outcome digest (R5-2/R9-2).
    contribution_drafts: list[ContributionDraft] = Field(default_factory=list)
    absorption_pre_image: Optional[dict] = None
    # `raw_request` (R7-1, plan-transient): the CANONICAL snapshot of the raw
    # edge as submitted — the COMPLETE JSON-mode dump captured by the PUBLIC
    # entry point BEFORE planning. The STORE verifies it against the plan under
    # the exhaustive field partition and computes the request digest ITSELF;
    # there is NO request_digest field on the plan (a caller-constructible
    # digest was the R7-1 forgery). Absent → phase-2 semantics only.
    raw_request: Optional[dict] = None


class SupersessionRefusal(BaseModel):
    """A durable, content-free refusal record as read back from the store (§4b). The
    inventory `specs/0011` re-evaluates: `rule_version` stamps which policy refused."""
    refusal_id: str
    user_id: str
    prior_edge_id: str
    incoming_edge_id: str
    relation: str
    prior_effective: int
    incoming_effective: int
    rule_version: str
    created_at: datetime


class SupersessionResult(BaseModel):
    """What `apply_supersession_plan` returns on success (an `Applied`). `replayed` is
    True when a durable receipt for `operation_id` already existed and the store replayed
    it as a no-op rather than re-applying (§4f idempotency)."""
    inserted_incoming: bool
    invalidated: int
    refused: int
    replayed: bool = False


class ContestedLinkage(BaseModel):
    """Content-free linkage for an UNSEEN FENCED cross-partition challenger in a live
    refusal contention (specs/0003 §4c-ii, round-10 correction A). It carries only the
    member's position — edge id, gate partition, effective-authority — and NO memory
    content (no object/value/provenance), so a fenced lower-trust source gains no
    query-independent reach through the structured API, the same guarantee the model-
    context surface already has."""
    edge_id: str
    partition: str            # "unverified" — the fenced side of the gate
    authority: int            # effective-authority position within the contention


class ContestedGroup(BaseModel):
    """One live refusal contention as it reaches `Recall.contested` (§4c-ii). `exposed`
    carries a FULL `Edge` for every member the reach contract already exposes — the
    preserved higher-authority grounded prior, every member the deterministic same-partition
    surface renders (incl. a grounded challenger the query did not select — round-11), and
    any relevance-selected member. `linkage` carries content-free entries for the unseen
    fenced cross-partition challenger. I6's rendered surface and this structured carrier
    agree: a value rendered in `context` is a full member here, never content-free."""
    subject: str
    relation: str
    exposed: list[Edge] = Field(default_factory=list)
    linkage: list[ContestedLinkage] = Field(default_factory=list)
    # specs/0012 §4c (impl round 3): the ids of the PRESERVED PRIOR edge(s) in this
    # group — the carrier the contested packer needs to resolve the mandatory roles
    # (highest-effective-authority member + grounded prior, which MAY ALIAS). Additive,
    # defaulted; populated by _build_contested from the refusal records.
    prior_edge_ids: list[str] = Field(default_factory=list)


# -- specs/0016 D2: the deletion ------------------------------------------------
# D1's deprecation surface (the lazy __getattr__s, the Field(deprecated=...)
# warning, the notice text) is RESOLVED by removal: `SourceType` is no longer
# a name this module provides, on any access path — attribute access,
# from-import, star-import, pickling — and `Provenance` has no `source_type`
# field. __all__ remains the star-import pin, now 41 names (was 42).
__all__ = [
    "BaseModel", "CONFIRMATION_RULE_VERSION", "Confirmation",
    "ConfirmationActor", "ConfirmationCallPath", "ConsolidationOp",
    "ConsolidationOutputDraft", "ConsolidationState", "ContestedGroup",
    "ContestedLinkage", "ContributionDraft", "ContributionRecord",
    "DEFAULT_EXPIRY", "DEFAULT_RELATIONS", "Disclosure", "Edge", "Enum",
    "Episode", "EvidenceAuthor", "ExpiryBehavior", "Field",
    "HISTORICAL_PREFIX", "Optional", "Outcome", "OutcomeJudgmentDraft",
    "Provenance", "QUARANTINE_RELATION", "RECOVERY_PENDING_STATES",
    "Relation", "SupersessionPlan", "SupersessionRefusal",
    "SupersessionRefusalDraft", "SupersessionResult", "Volatility",
    "annotations", "datetime", "is_historical_id", "timezone",
    "to_historical_id", "utcnow", "validate_correlation_id",
]
