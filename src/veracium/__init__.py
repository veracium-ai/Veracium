"""veracium — a provenance-aware memory plug-in for agentic systems.

    from veracium import Memory
    from veracium.llm.anthropic import AnthropicComplete

    mem = Memory(llm=AnthropicComplete())          # or any Complete callable
    mem.remember("alice", "USER: I'm vegetarian and have a dog named Ollie.")
    ctx = mem.recall("alice", "what should I keep in mind for lunch?")
    print(ctx.context)   # grounded, provenance-flagged memory for your prompt

Design (validated in the `agent-memory` research repo): a typed graph + dated
episodes are the store of record; recall assembles an entity-matched subgraph
(and, when enabled, an LLM-curated wiki) with third-party claims structurally
quarantined. Memory is per-user; one user's memory never reaches another's.
"""

from __future__ import annotations

import hashlib
import dataclasses
import json
import re
import threading
import time
import contextlib
from contextlib import contextmanager
from uuid import uuid4
from dataclasses import dataclass, field
from typing import Optional

from . import compile as _compile
from .compile import EMPTY_GROUNDED_BODY, EMPTY_VIEW_BODY
from . import gate as _gate
from . import lifecycle as _lifecycle
from .config import MemoryConfig

# Local-only abstention heuristic: computed on the answer text to emit a
# content-free boolean for telemetry. The text itself never leaves. Imported
# from gate rather than restated — the previous local copy was narrower than
# selfcheck's and under-counted abstentions.
from .gate import ABSTAINED as _ABSTAINED  # noqa: E402
from .graph import subgraph_for_query, render_edges
from .graph import _lexical_scored, fused_subgraph, fused_subgraph_with_receipt
from .graph import _asserted_today
from .challenge import EdgeInspection, withheld_line
from .asof.resolve import AsOfAnswer, AsOfFact, FutureAsOfRefused
from . import semantic as _semantic_mod
from .ingest import _event_dt, ingest_event
from .llm.base import Complete, Embed
from .authority import edge_effective as _edge_effective
from .graph import _value_key as _value_key
from .contention import contested_group_key, is_live_refusal, retained_refusal_ids
from .schema import (CONFIRMATION_RULE_VERSION, ConfirmationActor, is_procedural,
                     ConfirmationCallPath, ContestedGroup, ContestedLinkage,
                     Disclosure, Edge,
                     Episode, EvidenceAuthor, EvidenceContext,
                     OutcomeJudgmentDraft, Provenance, ReplyActor,
                     utcnow, validate_correlation_id)
from .scope import UNRESOLVED as _SCOPE_UNRESOLVED
from .store.base import HEAD_MOVED, Store, UnknownEdge
from .store.sqlite import SqliteStore
from .llm.metered import METERING_CAPABILITY, count_valid as _count_valid
from .usage import (ATTRIBUTED_PAIRS, ROLE_FIELDS, ArmingComplete,
                    active_call as _active_call,
                    routing_frame as _routing_frame)
from .census import declare_site
from . import credentials as _cred
from . import trust_tools as _trust_tools  # noqa: F401 — specs/0031 §4f: registers its census sites at import

# specs/0042 (tranche 3): the enforcement points of this module, each a declared site the
# decision is returned THROUGH — consult() brackets the decision, fire() wraps the value
_SITE_SCOPE_LOCAL_ORIGIN = declare_site("memory.scope.local-origin-missing")
_SITE_ASOF_ON_PROACTIVE = declare_site("memory.recall.as-of-on-proactive")
_SITE_RECALL_RECEIPT_AS_OF = declare_site("memory.recall.render-receipt-with-as-of")  # specs/0031 §4f §4b (INV-TT3)
# specs/0031 §4f (the trust tools): research's 0042 stage-1 classification (2026-11-15) — each an enforcement point
_SITE_TRUST_SCOPE_GATE = declare_site("trust.scope-gate")                        # §3b: INV-TT16, INV-TT18, INV-TT7
_SITE_TRUST_ERASE_PREVIEW = declare_site("trust.erase.preview.principal-scoped")  # INV-TT17
_SITE_TRUST_ERASE_PREVIEW_CONTEXT = declare_site("trust.erase.preview.issuer-context")  # §4e: the issuer's context
_SITE_TRUST_ERASE_CONFIRM = declare_site("trust.erase.confirm.principal-scoped")  # INV-TT17
_SITE_TRUST_RECEIPT_FILTER = declare_site("trust.receipt.scope-filter")          # §4d: INV-TT19
_SITE_POLICY_WITH_ASOF = declare_site("memory.recall.policy-with-as-of")
_SITE_EDGE_UNKNOWN_TARGET = declare_site("memory.edge.unknown-target")
# specs/0008 §6c (INV-Q2), R-A RA-03: confirm()'s unknown-edge refusal, reached only AFTER the store's registry decision
_SITE_CONFIRM_UNKNOWN_TARGET = declare_site("memory.confirm.unknown-target")
_SITE_DISPUTE_INACTIVE = declare_site("memory.dispute.inactive-edge")
_SITE_FEEDBACK_ATTESTED = declare_site("memory.feedback.attested-target")
# specs/0049 §5 (E2, E2b): edges_since refuses rather than guess a learned time (research stage 1 and the round-1
# verdict's Q5: both ENFORCEMENT)
_SITE_EDGES_SINCE_NO_JOURNAL = declare_site("memory.edges-since.no-journal")
_SITE_EDGES_SINCE_NO_EVENT = declare_site("memory.edges-since.no-journal-event")
_SITE_OUTCOME_ACTOR = declare_site("memory.record-outcome.actor-vocabulary")
_SITE_OUTCOME_HUMAN = declare_site("memory.record-outcome.human-judgment")
_SITE_OUTCOME_SYSTEM = declare_site("memory.record-outcome.system-judgment")
_SITE_CORRECT_INACTIVE = declare_site("memory.correct.inactive-edge")
_SITE_CORRECT_PROCEDURAL = declare_site("memory.correct.procedural")
_SITE_CORRECT_REFUSED = declare_site("memory.correct.refused")

__all__ = ["Memory", "MemoryConfig", "Recall", "PolicyLane", "PolicyReceipt", "FutureAsOfRefused", "AsOfAnswer",
           "AsOfFact", "Store", "SqliteStore",
           "Complete", "Embed", "EvidenceAuthor", "EvidenceContext"]


@dataclass
class Recall:
    """The result of a recall.

    `context` is a ready-to-inject block (grounded memory + a fenced never-assert
    section). For hosts that want the abstention gate, `grounded` and `unverified`
    are the two partitions the gate operates on (see `Memory.answer`).

    When recall ran with a `token_budget`, `tokens_estimated` is the heuristic
    size of `context` (chars/4 — veracium is tokenizer-agnostic by design) and
    `truncated` says whether anything was left out to fit. `edges`/`episodes`
    always carry the full retrieved units regardless of budget — the budget
    shapes the rendered context, not the raw material."""
    context: str
    grounded: str
    unverified: str
    edges: list[Edge]
    episodes: list[Episode]
    tokens_estimated: int = 0
    truncated: bool = False
    # specs/0003 §4c-ii: the structured contested-facts surface. One entry per LIVE refusal
    # contention, carrying full Edges for exposed members and content-free linkage for the
    # unseen fenced cross-partition challenger. Appended, defaulted — no existing constructor
    # call breaks. `edges` becomes the de-duplicated union of query-selected edges and the
    # exposed preservation members.
    contested: list["ContestedGroup"] = field(default_factory=list)
    # specs/0027 §4b — recall provenance rides a PARALLEL id-keyed field;
    # `edges: list[Edge]` is PRESERVED unchanged (retyping it was breaking,
    # R3-3). Entries exist for EXACTLY the ranked query selection; a
    # contention/I6a-preserved edge has NO entry — it was never scored, so
    # inventing route/fused_rank/cosine for it is forbidden (V7):
    # `recall.recalled_edges.get(e.id)` → None means "present by
    # contention-preservation, not by ranked selection". Both fields are
    # APPENDED WITH DEFAULTS (R5-4: `field(default_factory=dict)` — a mutable
    # literal default would not import), so existing construction is
    # unaffected and a semantic-less caller sees {} and "disabled".
    recalled_edges: dict[str, "RecalledEdge"] = field(default_factory=dict)
    semantic_status: str = "disabled"
    # specs/0028 §4c — the as-of provenance: None unless the call passed
    # `as_of=T`; then the normalised T, the ONE `now` the resolution read,
    # and a resolution per returned edge (interval, reason, tag, 0030 status,
    # disclosed cause, pointer). APPENDED WITH A DEFAULT (V-COMPAT).
    as_of: Optional["AsOfAnswer"] = None
    # specs/0027 v13 §4c — the POLICY RECEIPT: None unless the call passed a
    # `policy` whose lane FIRED (a rank landed on a candidate the membership
    # lanes hold). It records the counterfactual — the selection the same
    # inputs give with the policy term removed — so `displaced` is the event
    # `recalled_edges` structurally cannot hold. Written on the non-semantic
    # path too (research C1: a trace that exists only when another feature is
    # on reproduces the defect it was built to expose). APPENDED WITH A
    # DEFAULT (V-COMPAT).
    policy_receipt: Optional["PolicyReceipt"] = None
    # specs/0047 §4d / 0045 §4c — the INSPECTION carrier for every edge in `edges`: g(e) and its version (from
    # `attv`), the open-challenge count, the latest challenge, the mandatory unit and, for a withheld twin, the
    # challenged records withholding it. Read from the call's ONE challenge snapshot. A caller must not assert an
    # edge whose entry is not `assertable`, and must show the unit wherever it shows the record (the consumer duty).
    # APPENDED WITH A DEFAULT (V-COMPAT).
    inspection: dict[str, "EdgeInspection"] = field(default_factory=dict)
    # specs/0031 §4f §4b — the RENDER RECEIPT: None unless the call asked for it (`render_receipt=True`); then one
    # unit per record the renderer ADMITTED into `context`, in admission order: {kind, id, text as admitted,
    # partition, annotations, subject iff not the user, mutable iff a principal is bound}. Built at the admission
    # points, never by matching the prose; a withheld record is never a unit. APPENDED WITH A DEFAULT (V-COMPAT).
    render_receipt: Optional[list] = None


@dataclass(frozen=True)
class RecalledEdge:
    """specs/0027 §4b — one edge's recall provenance: how the ranked query
    selection found it. `route` is which lane(s) ranked it; a user-subject
    edge present only via the eligibility floor (overlap 0, not in the
    semantic lane) is route="lexical", exactly its status today."""
    edge_id: str
    lexical_overlap: int
    semantic_cosine: Optional[float]
    fused_rank: int
    fused_score: float
    route: str          # "lexical" | "semantic" | "both"


IDENTIFIER_RE = re.compile(r"[A-Za-z0-9._:-]{1,64}")    # matched WHOLE (fullmatch): `$` admits a trailing newline
MAX_POLICY_TAGS = 64


def _require_identifier(field: str, value) -> None:
    """specs/0027 v14.1: a host-supplied policy identity string is an
    IDENTIFIER — letters, digits and `._:-`, 1–64 characters, no whitespace —
    refused otherwise (a `bool` is not a string). The shape bounds what the
    receipt row can carry; it does not make the string content-free."""
    if not isinstance(value, str) or isinstance(value, bool) or not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(
            f"{field} must be an identifier (letters, digits and ._:- only, 1-64 "
            f"characters, no whitespace); got {value!r:.80}")


@dataclass(frozen=True)
class PolicyLane:
    """specs/0027 v13 §4c — a host-supplied policy application for ONE recall:
    which rule acted (`policy_id`, `policy_version` — the versioned policy the
    #12 prerequisite asks for), which host tags fired it (`tags_matched`, §2:
    opaque strings the host passes, never inferred), and the ranks it assigns
    (`ranks`: edge id → rank ≥ 1, the third RRF lane of §4a Stage 2). The lane
    contributes to `fused_score` only; a rank on an id the membership lanes do
    not hold contributes nothing. The library does not learn, choose or store
    policies: the host is the policy controller (C1)."""
    policy_id: str
    policy_version: str
    ranks: dict
    tags_matched: tuple = ()
    max_displaced: Optional[int] = None

    def __post_init__(self):
        # specs/0027 v15 §4h — THE DISPLACEMENT BUDGET: the lane's declared
        # maximum number of records it may displace from the returned
        # selection; an int >= 0 (a bool refused — True == 1 — as policy_rank
        # already refuses it; a negative refused); None means NO CAP, recorded
        # as such on every receipt. 0 is the strong setting: the lane may
        # reorder the returned set and never change its membership.
        if self.max_displaced is not None:
            if isinstance(self.max_displaced, bool) or not isinstance(self.max_displaced, int):
                raise ValueError(f"PolicyLane.max_displaced must be an int >= 0 or None; got {self.max_displaced!r}")
            if self.max_displaced < 0:
                raise ValueError(f"PolicyLane.max_displaced must be >= 0; got {self.max_displaced!r}")
        # specs/0027 v14.1 (research's pre-adoption read of 0041, 2026-09-14):
        # the policy's identity fields are HOST-SUPPLIED strings that the
        # receipt persists VERBATIM, so they are bounded to identifier shape
        # — IDENTIFIER_RE, at most 64 characters each, at most 64 tags — and
        # refused otherwise; the receipt's blob column then carries nothing a
        # host did not shape as an identifier. Bounded, not content-free: an
        # identifier can still be a label about a person
        # (`diagnosis:hiv-positive` passes every rule here), which is 0041's
        # class for `evidence_ref`, `source_id` and `correlation_id`, and is
        # stated as the limit rather than claimed away.
        _require_identifier("PolicyLane.policy_id", self.policy_id)
        _require_identifier("PolicyLane.policy_version", self.policy_version)
        if isinstance(self.tags_matched, list):
            object.__setattr__(self, "tags_matched", tuple(self.tags_matched))
        if not isinstance(self.tags_matched, tuple):
            raise TypeError("PolicyLane.tags_matched must be a tuple of identifiers")
        if len(self.tags_matched) > MAX_POLICY_TAGS:
            raise ValueError(f"PolicyLane.tags_matched carries {len(self.tags_matched)} tags; "
                             f"at most {MAX_POLICY_TAGS}")
        for i, tag in enumerate(self.tags_matched):
            _require_identifier(f"PolicyLane.tags_matched[{i}]", tag)
        if not isinstance(self.ranks, dict):
            raise TypeError("PolicyLane.ranks must be a dict of edge id -> rank")


@dataclass(frozen=True)
class PolicyReceipt:
    """specs/0027 v13 §4c (research T1) — the receipt of one recall in which a
    policy lane FIRED. `baseline_order` is the ranking WITHOUT the lane (Stages
    4-5 over the unadjusted order — the counterfactual); `adjusted_order` is
    what was returned; `displaced` = baseline[:n] − adjusted[:n], the event
    `recalled_edges` cannot record; `admitted` the converse; `delta_fused` the
    per-edge score change (bounded by 1/(K+1) per lane); `budget_state` proves
    whether displacement was possible at all (below `max_edges` nothing is
    truncated); `reserve_unchanged` asserts V-RESERVE-UNADJUSTED held on this
    call, with the reserved ids under both orders as its evidence (so the
    boolean is derivable, not declared); `budget_state.coverage_share` is the
    deployment's share, without which R4-1's displacement bound cannot be
    recomputed from the receipt; `recall_id` is a minted opaque correlation
    key (no content, no oracle) the host joins to its own logs. Ids only — no
    content, no query, no digest of the query (a digest of user prose is a
    confirmation oracle, 0041 §4); a receipt naming a record later redacted
    becomes unreadable, which is the correct degradation."""
    recall_id: str
    policy_id: str
    policy_version: str
    tags_matched: tuple
    baseline_order: list
    adjusted_order: list
    displaced: list
    admitted: list
    delta_fused: dict
    budget_state: dict
    reserved_baseline: list
    reserved_adjusted: list
    reserve_unchanged: bool
    ranks_applied: dict
    semantic_status: str
    recorded_at: str
    # specs/0027 v15 §4h (the displacement budget): the declared cap — None
    # RECORDED when none was declared, never omitted — and whether this recall
    # breached it; on a breach `adjusted_order` is the baseline (what was
    # returned) while `displaced`, `admitted` and `reserved_adjusted` keep what
    # the lane WOULD have done (V-BREACH-EVIDENCE-PRESERVED).
    max_displaced_declared: Optional[int]
    budget_breached: bool


_RECEIPT_FIELDS = tuple(f.name for f in dataclasses.fields(PolicyReceipt))


def _trust_edge_annotations(edge) -> list:
    from .trust_tools import edge_annotations
    return edge_annotations(edge)


def _agent_call_path(call_path) -> Optional[ConfirmationCallPath]:
    """specs/0031 §4f: the call path an AUDIT EPISODE carries. An agent path (`mcp_direct`, `adapter_direct`) is
    written; absence and `host_api` are both written as ABSENT, because absence on an audit episode means the host
    API (§2's Provenance row) and a host-API write must stay byte-identical (INV-TT5's `host_api written explicitly`
    mutant)."""
    if call_path is None:
        return None
    cp = ConfirmationCallPath(call_path)
    return None if cp is ConfirmationCallPath.HOST_API else cp


def _today_utc() -> str:
    """The date an omitted event date defaults to — the UTC calendar date,
    the clock ingestion reads a bare date in (`_event_dt`: a date is UTC
    midnight). The amendments reviewer, round 9 (F2): the default was the
    host's LOCAL calendar date, so at 22:01 UTC on a runtime whose local date
    was already tomorrow a routine was stored with valid_from = tomorrow 00:00
    UTC and withheld as not_yet_valid until then. One clock for the default
    and the reading, so an omitted date can never be in the future."""
    return utcnow().date().isoformat()


def receipt_row(receipt: "PolicyReceipt") -> dict:
    """specs/0027 §4g (v14): the store row for one receipt — the identity
    columns a reader lists by, and `receipt`: the receipt's JSON, keys sorted,
    the ONLY serialisation (V-RECEIPT-DURABLE reads it back field-equal).
    `tags_matched` travels as a JSON list and returns as a tuple."""
    return {"recall_id": receipt.recall_id, "policy_id": receipt.policy_id,
            "policy_version": receipt.policy_version, "recorded_at": receipt.recorded_at,
            "receipt": json.dumps(dataclasses.asdict(receipt), sort_keys=True,
                                  separators=(",", ":"))}


def receipt_from_row(row: dict) -> "PolicyReceipt":
    """The inverse of `receipt_row`: the verbatim text parsed back; a row whose
    text does not name exactly the receipt's fields is REFUSED (a store that
    hands back something else is not handing back the receipt)."""
    d = json.loads(row["receipt"])
    if not isinstance(d, dict) or set(d) != set(_RECEIPT_FIELDS):
        raise ValueError(
            f"policy receipt row {row.get('recall_id')!r} does not carry the receipt's fields "
            f"(has {sorted(d) if isinstance(d, dict) else type(d).__name__}, "
            f"wants {sorted(_RECEIPT_FIELDS)})")
    d["tags_matched"] = tuple(d["tags_matched"])
    for key in ("recall_id", "policy_id", "policy_version", "recorded_at"):
        if d[key] != row[key]:
            raise ValueError(f"policy receipt row {row.get('recall_id')!r}: column {key} "
                             f"disagrees with the receipt text")
    return PolicyReceipt(**d)


# specs/0027 §4b (V-STATUS) — the CLOSED semantic_status vocabulary.
SEMANTIC_STATUSES = frozenset({
    "ok",           # semantic lane ran and fused
    "disabled",     # semantic=False
    "no_embedder",  # Memory.embed / Embed.id()/dim() absent
    "unavailable",  # embedder raised / storage absent
    "timeout",      # exceeded semantic_timeout_ms
    "degraded",     # ran but the query vector was refused (V5)
})


class Memory:
    def __init__(self, *, llm: Complete, store: Optional[Store] = None,
                 embed: Optional[Embed] = None, config: Optional[MemoryConfig] = None,
                 telemetry=None, diagnostics=None, audit=None,
                 _register_metering: bool = True):
        self.config = config or MemoryConfig()
        if self.config.census_enabled:          # specs/0042 Part A-2: opt-in, default OFF, process-wide
            from . import census as _census
            _census.enable(True)
        self.store = store or SqliteStore(self.config.db_path)
        self.llm = llm
        self.embed = embed
        # specs/0020 §4a-ii — THE SCOPE POLICY, validated AT LOAD and never at
        # recall. `MemoryConfig.__post_init__` already ran the §4a-ii validator
        # for SHAPE; this is the authoritative validation, against the STORE's
        # real `local_origin()` — the singleton 0006 I9 resolves an absent
        # origin to, and therefore the only value against which digest OVERLAP
        # between an absent-origin rule and an explicit-origin rule is
        # decidable. `None` = the feature is disabled (a principal-bearing call
        # then REFUSES; it never degrades to unscoped).
        self.scope_policy = self._build_scope_policy()
        # specs/0017 §4b/§4d — the attribution state: ONE instance lock, the
        # ACTIVE-OPERATION REGISTRY (five-field entries keyed by op_token),
        # the per-user accumulator, and the listener-active flag whose
        # close-deactivate transition is the eighth of §4d's atomic set.
        self._usage_lock = threading.Lock()
        self._usage_registry: dict = {}
        self._llm_usage: dict = {}
        self._listener_active = True
        self._metered_handle = None
        self._metering_note = None   # one debug-visible fact on a failed opt-in
        # §4a — opt-in is the AFFIRMATIVE capability constant, matched exactly;
        # a coincidental totals() shape is never probed, invoked, or routed
        # (I11). The registration control plane is itself untrusted (R3-4):
        # missing/raising add_usage_listener or a None handle → treated
        # unmetered, no retries. `_register_metering=False` is the §4e
        # self-check path — its temporary memories never subscribe.
        if (_register_metering
                and getattr(llm, "metering_capability", None) == METERING_CAPABILITY):
            add = getattr(llm, "add_usage_listener", None)
            if add is None:
                self._metering_note = ("metering capability present but "
                                       "add_usage_listener missing — treated unmetered")
            else:
                try:
                    handle = add(self._usage_listener)
                except Exception:
                    handle = None
                    self._metering_note = ("add_usage_listener raised — "
                                           "treated unmetered")
                if handle is not None:
                    self._metered_handle = handle
                elif self._metering_note is None:
                    self._metering_note = ("add_usage_listener returned None — "
                                           "treated unmetered")
        # Optional content-free telemetry sink (a telemetry.Collector). None = off.
        # The library never creates one implicitly; entry points wire a consented
        # collector. See veracium.telemetry.
        self.telemetry = telemetry
        # Optional error-reporting sink (a diagnostics.Reporter). None = off. Logs
        # genuine errors locally and, only with consent, offers to send that log.
        # See veracium.diagnostics; sending is a separate, more careful channel than
        # telemetry because a log can contain memory content.
        self.diagnostics = diagnostics
        # Optional operation audit sink (an audit.AuditLog). None = off. One
        # content-free line per operation: who called what, when, which user.
        # See veracium.audit.
        self.audit = audit

    # -- specs/0020: the scope policy and the per-call view ------------------
    def _build_scope_policy(self):
        """The §4a-ii validator over the host's configured groups, keyed on
        THIS store's local origin. Raises at construction (config load), never
        at recall (§7)."""
        if self.config.scope_groups is None:
            return None
        from .scope import ScopeError, validate_policy
        local = getattr(self.store, "local_origin", None)
        with _SITE_SCOPE_LOCAL_ORIGIN.consult():
            if local is None:
                raise _SITE_SCOPE_LOCAL_ORIGIN.fire(ScopeError(
                    f"a scope policy is configured but {type(self.store).__name__} "
                    f"has no local_origin() — scope keys on the 0006 identity "
                    f"namespace, which this store does not provide"))
        return validate_policy(self.config.scope_groups,
                               self.config.cross_scope_visible,
                               local_origin=local())

    def _scope_view(self, user_id: str, principal, filters=None):
        """The per-call principal boundary, or None when unscoped. `principal
        is None` runs NO scope code at all — the mechanical form of V1."""
        from . import scope_read as _scope_read
        return _scope_read.view_for(self.store, user_id, principal,
                                    self.scope_policy, filters=filters)

    # -- specs/0017: the usage listener and operation context ---------------
    def _usage_listener(self, ev) -> None:
        """The §4b six-step algorithm. Steps 1–5 are cheap early-outs; STEP 6
        IS THE ONLY AUTHORITY — it re-checks everything inside one critical
        section (external R9-1: the step-1 read alone was check-then-act).
        Fail-closed throughout: nothing here raises into the operation."""
        # 1. closed-Memory early-out (the binding check is inside step 6)
        if not self._listener_active:
            return
        # 2. the module-global routing frame; owner check (external R3-1)
        frame = _routing_frame.get()
        if frame is None or frame[0] is not self:
            return
        op_token = frame[1]
        # 3./4. resolve the entry; missing or cancelled → nothing
        entry = self._usage_registry.get(op_token)
        if entry is None or entry["cancelled"]:
            return
        # 5. validate the event dict fail-closed BEFORE any state (§4a): the
        # exact mapping shape, the (event, role) pair against the producer
        # registry — the EVENT comes from the registry entry (external R5-3)
        # — and the §4c SHARED count predicate. Drop silently on any failure.
        if not isinstance(ev, dict) or set(ev.keys()) != {"role", "in_tok", "out_tok"}:
            return
        role = ev["role"]
        if not isinstance(role, str) or (role, entry["event"]) not in ATTRIBUTED_PAIRS:
            return
        if not (_count_valid(ev["in_tok"]) and _count_valid(ev["out_tok"])):
            return
        # 6. ONE critical section — re-check everything, compare-consume, append
        with self._usage_lock:
            if not self._listener_active:
                return
            entry = self._usage_registry.get(op_token)
            if entry is None or entry["cancelled"]:
                return
            armed = entry["armed_call"]
            ctx_call = _active_call.get()
            if armed is None or ctx_call is None:
                return
            call_id, consumed = armed
            if consumed or call_id is not ctx_call:
                return                    # stale copied context / duplicate: drop
            entry["armed_call"] = (call_id, True)     # consume, call-exact
            buf = entry["buffer"].setdefault(role, [0, 0, 0])
            buf[0] += ev["in_tok"]
            buf[1] += ev["out_tok"]
            buf[2] += 1

    @contextmanager
    def _usage_operation(self, user_id: str, event: str):
        """Enter one attributed operation (§4b/§4d): register the five-field
        entry, push the immutable routing frame, and yield
        `(op_llm, finish)` — the arming provider proxy and the
        terminal-merge callable. `finish()` merges the buffer into the
        accumulator EXACTLY ONCE (transition 6, cancelled-checked) and
        returns the per-role token fields for the operation's `_record`;
        the raise path never calls it, so a failed operation records
        nothing. The `finally` is transition 7 (remove the entry)."""
        if self._metered_handle is None:
            yield self.llm, dict
            return
        op_token = object()
        with self._usage_lock:                       # transition 1: register
            self._usage_registry[op_token] = {
                "user_id": user_id, "event": event, "buffer": {},
                "cancelled": False, "armed_call": None}
        frame_token = _routing_frame.set((self, op_token))
        finished = []

        def finish() -> dict:
            if finished:
                return {}
            finished.append(True)
            fields: dict = {}
            with self._usage_lock:                   # transition 6: merge
                entry = self._usage_registry.get(op_token)
                if entry is None or entry["cancelled"]:
                    return {}
                acc = self._llm_usage.setdefault(entry["user_id"], {})
                for role, (i, o, c) in entry["buffer"].items():
                    slot = acc.setdefault(role,
                                          {"calls": 0, "in_tok": 0, "out_tok": 0})
                    slot["calls"] += c
                    slot["in_tok"] += i
                    slot["out_tok"] += o
                    in_f, out_f = ROLE_FIELDS[role]
                    fields[in_f] = i
                    fields[out_f] = o
            return fields

        try:
            yield ArmingComplete(self, op_token, self.llm), finish
        finally:
            _routing_frame.reset(frame_token)
            with self._usage_lock:                   # transition 7: remove
                self._usage_registry.pop(op_token, None)

    def _record(self, event: str, fields: dict,
                user_id: Optional[str] = None) -> None:
        if self.telemetry is not None:
            try:
                self.telemetry.record(event, fields)
            except Exception:
                pass  # telemetry must never break memory
        if self.audit is not None and user_id is not None:
            try:
                self.audit.record(event, user_id, fields)
            except Exception:
                pass  # auditing must never break memory, even a broken sink

    def _on_degrade(self, where: str, user_id: Optional[str], kind: str, payload: dict) -> None:
        """specs/0039 §2c: hand a DEGRADE record to the diagnostics reporter — the
        sibling of `_on_error` for the paths that continue instead of raising.
        The record is `op`, `degrade`, `user_hash` (the `_on_error` convention:
        sha256 of the user id, first 12 hex) plus the site's content-free fields.
        Best-effort; never raises (the site invokes this only through
        `_emit_degrade`, which contains it a second time)."""
        if self.diagnostics is None:
            return
        try:
            uh = hashlib.sha256(user_id.encode()).hexdigest()[:12] if user_id else None
            self.diagnostics.record_degrade(where, kind, {"user_hash": uh, **payload})
        except Exception:
            pass

    def _on_error(self, where: str, exc: BaseException, user_id: Optional[str] = None) -> None:
        """Hand a genuine error to the diagnostics reporter (log locally; send only
        with consent). Best-effort — never masks or delays the real exception, which
        the caller re-raises."""
        if self.diagnostics is None:
            return
        try:
            uh = hashlib.sha256(user_id.encode()).hexdigest()[:12] if user_id else None
            self.diagnostics.record_error(where, exc, {"user_hash": uh})
        except Exception:
            pass

    # -- specs/0055: credential-shaped text is never stored ------------------
    def _cred_refused(self, user_id: str, op: str, field: str, cls: str, *, source: str = "caller"):
        """Record one `credential_refused` audit fact (§4g) and return the exception to raise. Content-free: the
        field and the class, never the value."""
        self._record("credential_refused", _cred.audit_fields(op, field, source=source, cls=cls), user_id)
        return _cred.CredentialRefused(field, cls)

    def _cred_ingress(self, user_id: str, op: str, *, ids=(), free=()) -> tuple[list, dict]:
        """specs/0055 §4b, the ingress screen: run at the top of an entry point, before any digest, length check,
        model call, log line or write (D1). Each identifier `(field, value)` carrying a shape refuses the whole call
        (`CredentialRefused`; nothing written). Each free-text `(field, text)` is masked. Returns the masked texts,
        in order, and the report `{field: {class: count}}`."""
        for field_name, value in ids:
            if isinstance(value, str) and value:
                cls = _cred.first_class(value)
                if cls is not None:
                    raise self._cred_refused(user_id, op, field_name, cls)
        out: list = []
        report: dict = {}
        for field_name, text in free:
            if isinstance(text, str) and text:
                text, rep = _cred.mask(text)
                _cred.merge_report(report, field_name, rep)
            out.append(text)
        return out, report

    def _refuse_shaped_identity(self, user_id: str, edge) -> None:
        """specs/0055 §4c-ii row 8: `correct`'s replacement copies the prior's `subject` and `relation`, the fact's
        identity that supersession joins on, so a credential shape in either refuses the correction rather than being
        masked; 0041 redaction is the remedy. Raised inside the correction's transaction, before anything is written."""
        for field_name, value in (("subject", edge.subject), ("relation", edge.relation)):
            cls = _cred.first_class(value) if isinstance(value, str) else None
            if cls is not None:
                raise self._cred_refused(user_id, "correct", field_name, cls, source="derived")

    def _cred_withheld(self, user_id: str, op: str, report: dict, *, source: str) -> None:
        """One `credential_withheld` audit fact per field of `report` (§4g: surface, field, class counts, source,
        shapes_version)."""
        for field_name, classes in report.items():
            self._record("credential_withheld", _cred.audit_fields(op, field_name, source=source,
                                                                    classes=classes), user_id)

    # -- write -------------------------------------------------------------
    def remember(self, user_id: str, event_text: str, *,
                 author: EvidenceAuthor = EvidenceAuthor.USER,
                 date: Optional[str] = None, event_type: str = "chat",
                 evidence_ref: Optional[str] = None,
                 derived_from: Optional[EvidenceAuthor] = None,
                 context: Optional[EvidenceContext] = None,
                 source_id: Optional[str] = None) -> dict:
        """Ingest one interaction event into `user_id`'s memory.

        `author` is the trust-critical input: use EvidenceAuthor.THIRD_PARTY for
        received email / external documents so their claims are quarantined.

        `context` (specs/0011 §4d) is the host's POSITIVE ingress declaration
        about the event's CONTENT source: pass `EvidenceContext.direct()` to
        attest first-party capture, or `EvidenceContext.derived(X)` to declare
        derivation from class X. ⚠ Absent any declaration (no `context`, no
        `derived_from`), the content class floors to derived(THIRD_PARTY) —
        absence stopped being the trusted cell at 0011's acceptance. This
        method deliberately does NOT mint `direct()` on the caller's behalf:
        doing so would recreate trusted-by-omission one layer up. A malformed
        context raises and nothing is written.

        Authorship is per-event; if the event's *content* embeds material a
        lower-trust party influenced — a system-authored summary quoting a
        received email's subject or body — declare it with `derived_from`
        (e.g. `author=SYSTEM, derived_from=THIRD_PARTY`). Trust is capped at
        the minimum of the two: nothing extracted from such an event is ever
        assertable, closing the system-event laundering bypass.

        ONE SPEAKER PER EVENT. A conversation holding both the user's turns
        and an assistant's is not one user event: pass each turn as its own
        event — the user's under `author=USER`, the assistant's under
        `author=ASSISTANT` — or pass only the user's turns. Ingest does not
        separate speakers inside an event, so a whole transcript passed under
        `author=USER` can store the assistant's own first-person statements
        ("I live in Denver") as the user's facts and assert them; turns with
        no speaker labels are the likeliest case.

        `source_id` (specs/0006) optionally records WHICH source produced this
        event — an opaque, host-chosen id (a mailbox, a connector instance). It
        is DIAGNOSTIC: it groups records for inspection/dedup/attribution but
        grants no trust and changes no answer (I5). It is host-supplied only,
        never model-derived (I1).

        specs/0055 §4b: credential-shaped text in `event_text` is withheld before the extractor sees it, and the
        result's `credentials_withheld` (present only when something was withheld) names the field and the classes,
        never the value. A shape in `source_id`, `evidence_ref` or `event_type` refuses the call
        (`veracium.credentials.CredentialRefused`, `reason="credential_refused"`); nothing is written."""
        (event_text,), caller_report = self._cred_ingress(
            user_id, "remember", ids=(("source_id", source_id), ("evidence_ref", evidence_ref),
                                      ("event_type", event_type)),
            free=(("event_text", event_text),))
        date = date or _today_utc()
        t0 = time.perf_counter()
        with self._usage_operation(user_id, "ingest") as (op_llm, usage_finish):
            try:
                r = ingest_event(self.store, op_llm, user_id, event_text=event_text,
                                 author=author, date=date, event_type=event_type,
                                 evidence_ref=evidence_ref, derived_from=derived_from,
                                 context=context,
                                 source_id=source_id, relations=self.config.relations,
                                 require_source_id=self.config.require_source_id,
                                 # specs/0039 §2c: the degrade channel — an event, not
                                 # a counter; the result's key set does not change
                                 on_degrade=(lambda kind, payload:
                                             self._on_degrade("remember", user_id, kind, payload)))
            except Exception as e:
                self._on_error("remember", e, user_id)
                raise
            fields = {"facts": r["facts"], "quarantined": r["quarantined"],
                      "episodes": 1 if r["episode"] else 0,
                      "unparseable": 1 if r.get("unparseable") else 0,
                      "supersessions": r["supersessions"],
                      "reinforcements": r["reinforcements"],
                      # specs/0025 §4c: the five public counters, telemetry
                      # carrier — same consent gating as every ingest field.
                      "invalid": r["invalid"], "retried": r["retried"],
                      "recovered": r["recovered"], "residual": r["residual"],
                      "redispositioned": r["redispositioned"],
                      "subject_refused": r["subject_refused"],
                      # specs/0003/within-episode: a content-free count, MCP-stripped and outside telemetry's
                      # consented schema (AWAITING consent, 0025 §4c's declared difference): the whitelist drops it
                      "within_episode_contested": r["within_episode_contested"],
                      # specs/0023 Q4: audit-only facts — the AuditLog
                      # records them; telemetry's whitelist drops them.
                      "quarantined_at_birth": r["quarantined_at_birth"],
                      "birth_revocation_digest": r["birth_revocation_digest"],
                      "ms": int((time.perf_counter() - t0) * 1000)}
            fields.update(usage_finish())          # specs/0017: the terminal merge
            self._record("ingest", fields, user_id)
        # specs/0055 §4g: the caller's withheld spans and the extractor's (§4c, source `model_output`), one key
        model_report = r.pop("credentials_withheld", None) or {}
        self._cred_withheld(user_id, "remember", caller_report, source="caller")
        # a dropped triple is a refusal (I5: counted as credential_refused, source model_output); a masked summary
        # is a withholding
        for field_name, classes in model_report.items():
            self._record("credential_refused" if field_name == "extracted_fact" else "credential_withheld",
                         _cred.audit_fields("remember", field_name, source="model_output", classes=classes),
                         user_id)
        if caller_report or model_report:
            r["credentials_withheld"] = {**caller_report, **model_report}
        # specs/0027 §4c: the embedding write is OUTSIDE the store write
        # transaction (post-commit, best-effort) — an embedder failure never
        # fails or blocks ingest. The diff-driven backfill also sweeps up
        # edges other write paths (correct, absorption) created since.
        try:
            self.embed_backfill(user_id)
        except Exception:
            pass
        return r

    # -- read --------------------------------------------------------------
    def _semantic_lane(self, user_id: str, query: str, *, visible_ids=None):
        """specs/0027 §4d — resolve the semantic lane to (status, candidates).

        Never raises: every failure is a `semantic_status` value and a lexical
        degrade (V6). The query embed runs on a daemon worker joined for
        `semantic_timeout_ms` — recall never blocks longer than the deadline
        on the embedder (the CONTRACT; the abandoned worker's late result is
        discarded)."""
        embedder = self.embed
        eid, dim, st = _semantic_mod.embedder_identity(embedder)
        if st != "ok":
            return st, []
        # R6-3 + R7-4: THE SAME validator as construction runs against the
        # LIVE values — strict types included, so a post-construction
        # mutation to a bool timeout or float fetch size refuses exactly as
        # it would have at __post_init__ (a config error, not a degrade);
        # then auto-resolve tracks the live max_subgraph_edges
        self.config.validate_semantic()
        k = self.config.semantic_fetch_k
        if k is None:
            k = max(200, self.config.max_subgraph_edges)
        result: dict = {}

        def _embed_query():
            try:
                result["vecs"] = embedder([query])
            except Exception as e:                    # never propagates (V6)
                result["err"] = e

        t = threading.Thread(target=_embed_query, daemon=True)
        t.start()
        t.join(self.config.semantic_timeout_ms / 1000.0)
        if t.is_alive():
            return "timeout", []
        if "err" in result:
            return "unavailable", []
        vecs = result.get("vecs")
        vec = vecs[0] if isinstance(vecs, list) and len(vecs) == 1 else None
        qv = _semantic_mod.validate_vector(vec, dim)
        if qv is None:
            return "degraded", []                      # query vector refused (V5)
        try:
            sm = self.store.semantic_candidates(
                user_id, qv, embedder_id=eid, dim=dim, k=k,
                min_cosine=self.config.semantic_min_cosine,
                visible_ids=visible_ids)
        except NotImplementedError:
            return "unavailable", []                   # storage absent
        except Exception:
            return "unavailable", []
        return "ok", list(sm)

    def embed_backfill(self, user_id: str) -> int:
        """specs/0027 §4c — embed this user's edges that lack a FRESH vector
        under the configured embedder. Idempotent and best-effort: computed
        OUTSIDE any store write transaction, persisted via the
        digest-conditional `upsert_embedding` (a racing text update simply
        drops the stale write). Returns the number of vectors written; 0 when
        no embedder (or none missing). Called post-commit by `remember`; also
        the explicit backfill for pre-existing stores (recall quality ramps
        with it — an un-embedded edge is still found lexically)."""
        eid, dim, st = _semantic_mod.embedder_identity(self.embed)
        if st != "ok":
            return 0
        try:
            have = self.store.embedding_keys(user_id, eid)
        except NotImplementedError:
            return 0
        pending = []
        # specs/0041 D3 (round-9 R9-07): an ATTESTED-redacted edge is SKIPPED by the rebuild — its vector was deleted
        # by the redaction and the tombstone is never embedded. Keyed on the attestation record: an UNATTESTED
        # marker row is an ordinary record and is embedded under its own contract. A redaction landing after this
        # read is caught by the digest-conditional upsert below (the stored row's digest no longer matches).
        redacted = self.store.redacted_targets(user_id, "edge")
        for e in self.store.edges(user_id, active_only=False):
            if e.id in redacted:
                continue
            d = _semantic_mod.content_digest(e)
            if (e.id, d) not in have:
                pending.append((e, d))
        if not pending:
            return 0
        try:
            vecs = self.embed([_semantic_mod.embedded_text(e)
                               for e, _d in pending])
        except Exception:
            return 0                                   # never fails the caller
        if not isinstance(vecs, list) or len(vecs) != len(pending):
            return 0
        written = 0
        now = utcnow().isoformat()
        for (e, d), v in zip(pending, vecs):
            fv = _semantic_mod.validate_vector(v, dim)
            if fv is None:
                continue                               # refused vector (V5)
            try:
                if self.store.upsert_embedding(
                        edge_id=e.id, user_id=user_id, embedder_id=eid,
                        content_digest=d, dim=dim,
                        vec=_semantic_mod.pack_vec(fv), built_at=now):
                    written += 1
            except NotImplementedError:
                return written
        return written

    def record_procedure(self, user_id: str, summary: str, *, author: EvidenceAuthor,
                         context: EvidenceContext, relation: str = "follows_procedure",
                         note: Optional[str] = None, when=None,
                         evidence_ref: Optional[str] = None,
                         source_id: Optional[str] = None) -> str:
        """specs/0037 §4b — record a PROCEDURAL record and return its edge id (a `str`, the 0037 contract). The
        same call with the specs/0055 report is `record_procedure_report`, which returns a dict:
        `{"edge_id": …}` plus `credentials_withheld` when a credential-shaped span of `summary` or `note` was
        withheld (§4g, R1-05). Both refuse a shape in `source_id` or `evidence_ref` with
        `veracium.credentials.CredentialRefused`, before any write.

        See `record_procedure_report` for the full contract."""
        return self.record_procedure_report(
            user_id, summary, author=author, context=context, relation=relation, note=note, when=when,
            evidence_ref=evidence_ref, source_id=source_id)["edge_id"]

    def record_procedure_report(self, user_id: str, summary: str, *, author: EvidenceAuthor,
                                context: EvidenceContext, relation: str = "follows_procedure",
                                note: Optional[str] = None, when=None,
                                evidence_ref: Optional[str] = None,
                                source_id: Optional[str] = None) -> dict:
        """specs/0037 §4b — record a PROCEDURAL record from the host's own
        declaration (since v16 the extractor path can also record one, behind
        the verbatim-quote gate of §4a-iii). Returns the new edge id.

        `summary` is the host's gloss-level name of the procedure — the ONLY
        stored text `describe_procedures` ever renders; `note` (step-level
        detail, if any) is stored and NEVER rendered. `author` is the
        AUTHORSHIP axis exactly as `remember` takes it; `context` carries the
        DERIVATION axis (`derived_from`) and the BASIS — REQUIRED:
        `EvidenceContext.direct(basis="stated")` (they said they follow it)
        or `basis="observed"` (a pattern they reported observing), or
        `derived(X, basis=…)`. The three axes are independent
        (V-PROVENANCE-AXES). `relation` must be registered `procedural` in
        this Memory's active registry, else `ValueError`
        (`relation_not_procedural`); the record is stamped
        `record_kind="procedural"` at write and read from the stamp ever
        after. Disclosure is DERIVED: quarantine-at-birth for a
        standing-revoked `source_id` (the surface honours revocation), then
        the shipped three-axis rule. Every refusal raises BEFORE any write.
        No episode is written. Procedural records never enter recall's
        context; they are described through `describe_procedures`.

        specs/0055 §4b/§4g: `summary` and `note` are screened before anything reads them (the 512-character cap
        included); a withheld span appears as `[credential withheld: <class>]` and the returned dict's
        `credentials_withheld` names the field and classes. Returns `{"edge_id": …}` plus that key when non-empty."""
        (summary, note), report = self._cred_ingress(
            user_id, "record_procedure", ids=(("source_id", source_id), ("evidence_ref", evidence_ref)),
            free=(("summary", summary), ("note", note)))
        from .graph import apply_supersession
        from .procedures import build_procedure_edge
        edge, revoked_at_birth, birth_digest = build_procedure_edge(
            self.store, self.config.relations, user_id, summary, author=author,
            context=context, relation=relation, note=note, when=when,
            evidence_ref=evidence_ref, source_id=source_id,
            require_source_id=self.config.require_source_id)   # specs/0006 §4 rule 9 (v9)
        counts = apply_supersession(self.store, edge, self.config.relations)
        self._record("record_procedure",
                     {"facts": 1, "basis": edge.provenance.basis,
                      "supersessions": counts.superseded,
                      "reinforcements": counts.reinforced,
                      "quarantined_at_birth": 1 if revoked_at_birth else 0,
                      "birth_revocation_digest": birth_digest}, user_id)
        self._cred_withheld(user_id, "record_procedure", report, source="caller")
        try:
            self.embed_backfill(user_id)
        except Exception:
            pass
        out = {"edge_id": edge.id}
        if report:
            out["credentials_withheld"] = report
        return out

    def describe_procedures(self, user_id: str, *, query: Optional[str] = None,
                            principal=None, limit: Optional[int] = None):
        """specs/0037 §4a-ii — the stage-3 read surface: one `DescribeResult`
        over the VISIBLE procedural records (by their own stamp/basis). Each
        candidate is described or withheld under the first failing conjunct
        of the ordered predicate (stamp consistent → relation registered →
        active → valid_now → not quarantined → not use_only → basis in
        {stated, observed} → summary passes the frozen recognition rule),
        never both and never neither; a HIDDEN record is in neither list
        (indistinguishable from no match); the `note` is rendered nowhere.
        `query` ORDERS `descriptions` (relevance over subject/relation/object
        tokens, then `valid_from` desc, then id) and never filters either
        list — `withheld` is query-blind. `limit` defaults to
        `max_subgraph_edges` and must be an int in [1, that cap]; the
        population is ordered BEFORE the cut and `total_describable` keeps
        it accountable after it. Read-only; `kind_conflict` candidates are
        counted to telemetry."""
        from .procedures import describe_procedures as _describe
        cap = self.config.max_subgraph_edges
        if limit is None:
            limit = cap
        elif isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError(f"limit must be an int, got {type(limit).__name__}")
        elif not 1 <= limit <= cap:
            raise ValueError(f"limit must be in [1, {cap}] (max_subgraph_edges), got {limit}")
        if query is not None:
            if not isinstance(query, str):
                raise TypeError(f"query must be a str or None, got {type(query).__name__}")
            query = " ".join(query.lower().split()) or None
        view = self._scope_view(user_id, principal, None)
        result, conflicts = _describe(self.store, self.config.relations, user_id,
                                      query=query, view=view, limit=limit)
        self._record("describe_procedures",
                     {"described": len(result.descriptions),
                      "total_describable": result.total_describable,
                      "withheld": len(result.withheld), "kind_conflict": conflicts,
                      "truncated": 1 if result.truncated else 0}, user_id)
        return result

    def recall(self, user_id: str, query: Optional[str] = None, *,
               token_budget: Optional[int] = None,
               principal=None, semantic="auto", as_of=None, policy=None,
               render_receipt: bool = False, **filters) -> Recall:
        """Assemble grounded memory context for answering `query`.

        `policy` (specs/0027 v13 §4c): a `PolicyLane` the host built for THIS
        call. Its ranks feed the third RRF lane of §4a Stage 2 — order only,
        never the reserve, never membership — and when the lane FIRES the
        result carries a `PolicyReceipt` recording the counterfactual. With a
        policy the fused construction is used on every path, including
        `semantic=False` (it is byte-identical to the legacy projection with
        the semantic lane empty), so the receipt exists on the non-semantic
        path too. Not combinable with `as_of`.

        `render_receipt` (specs/0031 §4f §4b): off by default, and then nothing about the call changes. On, the
        result's `render_receipt` lists one unit per record the renderer ADMITTED into `context`, built at the
        admission points as each unit is admitted — `{kind, id, text as admitted, partition, annotations}`, with
        `subject` when it is not the user and, under a principal, `mutable` (OWN only). Withheld records are never
        units; wiki text is a unit with no id. The query and no-query paths carry it; `as_of` refuses it.

        Combines the LLM-curated wiki (the grounded, verified working view,
        recompiled after N writes) with a per-query entity-matched subgraph for
        detail — the layered design that won both horizons. Memory is partitioned
        into grounded (assertable) and unverified (third-party claims/reports),
        so the host can apply the abstention gate via `answer()` or its own prompt.

        `token_budget` caps the rendered context in ESTIMATED tokens (chars/4 —
        veracium is tokenizer-agnostic; approximate, not exact). Omitted, the
        validated config default applies (`query_context_budget_tokens`, 4,000)
        — recall is never unbounded; a budget below the envelope-derived floor
        raises `ValueError` (specs/0012 I10e — the old sub-floor best-effort
        rendering is withdrawn). Selection under pressure follows the FROZEN
        0012 §4c(iv) order: contested first, then query-relevant flagged
        warnings, query-matched claim flags, other flagged warnings
        (most-overdue first), dated commitments (nearest first), the wiki
        within its render share, relevance-ranked grounded edges, episodes
        (newest first), the remaining unverified partition, and variants last.
        Truncation is reported in-context (bounded-width counts) and via
        `Recall.truncated`.

        **No query → proactive mode**: a session-start briefing ("what should
        I know before starting?") — dated commitments coming due or overdue,
        possibly-stale facts to confirm when natural, current transient state
        worth a follow-up, recent history. Proactive surfacing is
        *volunteering*, so disclosure gates it: only MENTIONABLE facts appear;
        `use_only` material and quarantined claims never surface unprompted
        (`Recall.unverified` is always empty in this mode). LLM-free and
        deterministic; see `veracium.proactive`.

        **`principal` (specs/0020) — the scope boundary.** Optional; a
        `veracium.scope.Identity` naming the RECALLING party. Omitted
        (`None`), recall is byte-identical to what it has always been over a
        fixed store state — the migration invariant. Supplied, every
        structured carrier (`edges`, `episodes`, `contested`, and each
        group's `exposed`) carries ONLY records the visibility relation
        admits; cross-scope material renders as third-party-shaped testimony
        that is never assertable; UNRESOLVED derivatives are invisible
        (fail-closed); and the store-wide compiled wiki is EXCLUDED (§4d — a
        store-wide LLM re-rendering is a laundering site the scope machinery
        does not control). A principal with no configured policy REFUSES, and
        so does a `source_id`-less one (0006 I13): feature-disabled never
        silently degrades to an unscoped, fully-assertable view.

        The identity is HOST-SUPPLIED and NOT AUTHENTICATED (0006 R7): this
        is honest-host ISOLATION — context bleed, confused deputy,
        cross-agent leakage — never a security boundary against a caller who
        forges an identity.

        `**filters` (specs/0020 §4e) narrow the result WITHIN what is already
        visible — the CLOSED field set `subject`, `relation`,
        `author_of_evidence`, `source_id`, `volatility`, equality only. An
        unknown field raises. Filters SELECT, never STRIP: the narrowest
        result still renders full disclosure, and the contested surface's
        preservation guarantee is never filtered away.

        **`as_of` (specs/0028 §4c) — what did we hold to be true at T.**
        `None` (default) is today's behaviour, byte-identical (V-COMPAT: the
        as-of filter is never invoked). An aware `datetime` T runs the §4a
        resolution as a PRE-FILTER — one injected-clock read, one store
        snapshot, scope before historical eligibility — and normal ranking
        and budgeting run over the candidates it yields; `Recall.as_of`
        carries a resolution per returned edge. T in the future RAISES the
        typed `FutureAsOfRefused`; a naive or non-datetime T raises
        `ValueError` first (V-NORM-FIRST). Under `as_of` the wiki, the
        episodes and the contested block are OMITTED (they are statements
        about now). The proactive path (`query=None`) refuses `as_of`.
        """
        if token_budget is not None and token_budget <= 0:
            raise ValueError("token_budget must be a positive number of tokens")
        from .scope import validate_filters
        filters = validate_filters(filters or None)   # the CLOSED §4e grammar
        with _SITE_ASOF_ON_PROACTIVE.consult():
            if query is None and as_of is not None:
                raise _SITE_ASOF_ON_PROACTIVE.fire(ValueError("as_of is refused on the proactive path: a briefing is a "
                                 "statement about now (specs/0028 §4c)"))
        with _SITE_RECALL_RECEIPT_AS_OF.consult():
            if as_of is not None and render_receipt:
                # specs/0031 §4f §4b defines the render receipt for the query and the proactive paths only: the as_of
                # renderer has no admission points, so a receipt there could not be the units it admitted
                raise _SITE_RECALL_RECEIPT_AS_OF.fire(ValueError(
                    "render_receipt is defined for the query and proactive paths, not as_of (specs/0031 §4b)"))
        try:
            if query is None:
                # proactive is LLM-free; the frame is pushed for uniformity
                # (recall is in the §4b context-entering set) and stays inert.
                with self._usage_operation(user_id, "recall") as (_op_llm, _fin):
                    return self._proactive(user_id, token_budget,
                                           principal=principal, filters=filters,
                                           render_receipt=render_receipt)
            with self._usage_operation(user_id, "recall") as (op_llm, usage_finish):
                return self._recall(user_id, query, token_budget,
                                    op_llm, usage_finish,
                                    principal=principal, filters=filters,
                                    semantic=semantic, as_of=as_of, policy=policy,
                                    render_receipt=render_receipt)
        except Exception as e:
            self._on_error("recall", e, user_id)
            raise

    def facts_valid_at(self, user_id: str, subject: str, relation: str, T, *,
                       principal=None, policy=None) -> list:
        """specs/0028 §4c — the DIRECT lookup: every record of `(subject,
        relation)` held valid at T, each as an `AsOfFact` (the edge and its
        resolution: interval, reason, tag, 0030 status, disclosed cause,
        pointer). It carries the scope inputs it needs because it promises
        recall's decision (R3-3): `principal`/`policy` keyword-only, default
        None — a caller passing neither gets the unscoped view exactly as
        `recall` does; `policy=None` with a principal uses this Memory's
        configured policy, as recall does (V-SCOPE-DIFFERENTIAL). `T` is
        required (`None` is a TypeError); naive → `ValueError`; in the
        future → `FutureAsOfRefused`. Read-only: one clock read, one
        snapshot, no write."""
        if T is None:
            raise TypeError("facts_valid_at requires T (specs/0028 §2c-i)")
        from .asof.resolve import resolve_as_of
        pol = self.scope_policy if policy is None else policy
        answer = resolve_as_of(self.store, user_id, T, principal=principal, policy=pol,
                               subject=subject, relation=relation)
        return list(answer.facts)

    def _proactive(self, user_id: str, token_budget: Optional[int],
                   *, principal=None, filters: Optional[dict] = None, render_receipt: bool = False) -> Recall:
        from . import proactive
        # specs/0012 I10: proactive is ALWAYS budgeted — the config default (1,200)
        # applies when the caller omits token_budget.
        if token_budget is None:
            token_budget = self.config.proactive_default_budget_tokens
        # specs/0020 §4f: the SAME visibility relation, on the SAME code path —
        # the lens is applied to the proactive edge set (and the episode set)
        # BEFORE assembly, so categorization, collapse, budgeting and the
        # returned structured carriers all see only visible records. Unscoped,
        # `view` is None and `assemble` runs exactly as it always has.
        view = self._scope_view(user_id, principal, filters)
        snap = self.store.challenge_snapshot(user_id)          # specs/0047 §4d: the call's ONE snapshot
        # 0003/obligations §4b: the briefing's contested groups, by the ONE refusal-scoped construction and with no
        # query selection, so only mentionable members are named; the briefing's Recall.contested stays empty
        groups, _ = self._build_contested(user_id, [], view)
        from .trust_tools import RenderReceipt
        rr = RenderReceipt(view) if render_receipt else None       # specs/0031 §4b: off by default
        context, edges, episodes, truncated = proactive.assemble(
            self.store, user_id, self.config,
            token_budget=token_budget, est=self._est_tokens,
            visible=(view.lens if view is not None else None), snap=snap,
            contested=[(g.subject, g.relation, [e.id for e in g.exposed]) for g in groups],
            **({} if rr is None else {"receipt": rr}))
        self._record("recall", {"wiki_used": False, "subgraph_edges": len(edges),
                                "grounded_items": len(edges), "unverified_items": 0,
                                "proactive": 1, "trimmed": 1 if truncated else 0},
                     user_id)
        return Recall(context=context, grounded=context, unverified="",
                      edges=edges, episodes=episodes,
                      tokens_estimated=self._est_tokens(context), truncated=truncated,
                      inspection={e.id: snap.inspect(e, visible=(view.visible if view is not None else None),
                                                      cap_tokens=self.config.item_cap_tokens) for e in edges},
                      render_receipt=None if rr is None else rr.units)

    @staticmethod
    def _est_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    def _recall(self, user_id: str, query: str,
                token_budget: Optional[int] = None,
                op_llm=None, usage_finish=dict,
                *, principal=None, filters: Optional[dict] = None,
                semantic="auto", as_of=None, policy=None, render_receipt: bool = False) -> Recall:
        # specs/0017: op_llm is the operation's arming provider proxy (or the
        # raw llm when unmetered); usage_finish merges the token buffer into
        # the terminal _record exactly once.
        if op_llm is None:
            op_llm = self.llm
        # specs/0003 §4c-ii/§4e: the host relation registry flows to BOTH the compiler
        # (so a contested functional group is excluded from the one-value wiki, and the
        # cache binds the registry/policy digest) AND subgraph_for_query (so a functional
        # contention is authority-ordered). A custom registry must reach both, not one.
        # specs/0012 I10: query recall is ALWAYS budgeted — a caller that omits
        # token_budget gets the validated config default (4,000), never unbounded.
        if token_budget is None:
            token_budget = self.config.query_context_budget_tokens
        # I10e at SURFACE BUILD (R-impl4-3): a config mutated after construction
        # cannot smuggle a sub-floor bound past __post_init__ — every mutable
        # recall bound revalidates here, the wiki layer enabled or not.
        from .budgets import MIN_ITEM_ALLOWANCE, validate_budget
        validate_budget("recall", token_budget,
                        self.config.group_heading_allowance_tokens)
        if self.config.item_cap_tokens < MIN_ITEM_ALLOWANCE:
            raise ValueError(
                f"item_cap_tokens {self.config.item_cap_tokens} is below the minimum "
                f"item allowance {MIN_ITEM_ALLOWANCE} (I10e, recall surface build)")
        if not (0 < self.config.wiki_render_share <= 1):
            raise ValueError("wiki_render_share must be in (0, 1]")
        from .budgets import MARKER_RESERVE
        if int(token_budget * self.config.wiki_render_share) < \
                MIN_ITEM_ALLOWANCE + MARKER_RESERVE:
            raise ValueError(
                f"wiki_render_share {self.config.wiki_render_share} of token budget "
                f"{token_budget} leaves "
                f"{int(token_budget * self.config.wiki_render_share)} tokens for the "
                f"wiki slot — below one clamped item + the marker reserve "
                f"({MIN_ITEM_ALLOWANCE + MARKER_RESERVE}) (I10e, recall surface build)")
        if self.config.contested_members_per_line < 2:
            raise ValueError("contested_members_per_line < 2 (I10e, surface build)")
        if self.config.group_heading_allowance_tokens < 16:
            raise ValueError("group_heading_allowance_tokens < 16 (I10e, surface build)")
        # specs/0020 §4f — THE PRINCIPAL BOUNDARY. Built once per call; None
        # when unscoped, and then not one line of scope code runs (V1).
        view = self._scope_view(user_id, principal, filters)
        if policy is not None and not isinstance(policy, PolicyLane):
            raise TypeError("policy must be a veracium.PolicyLane")
        with _SITE_POLICY_WITH_ASOF.consult():
            if policy is not None and as_of is not None:
                raise _SITE_POLICY_WITH_ASOF.fire(ValueError("recall(policy=...) is not combinable with as_of= (specs/0027 v13 §4c: the as-of path carries no receipt)"))
        from .trust_tools import RenderReceipt
        rr = RenderReceipt(view) if render_receipt else None
        if as_of is not None:
            # specs/0028 §4c — the as-of branch: the §4a resolution is the
            # pre-filter; ranking and budget run over its candidates with the
            # branch's own T-predicate. Taken BEFORE the wiki compile (a
            # write; §2c-ii says as-of cannot cause one). `as_of=None` never
            # reaches this line (V-COMPAT).
            from .asof.recall import recall_at
            return recall_at(self, user_id, query, token_budget, as_of=as_of,
                             view=view, principal=principal, filters=filters,
                             semantic=semantic, usage_finish=usage_finish)
        # specs/0020 §4d (V5) — THE WIKI IS EXCLUDED from a principal-bearing
        # response: it is a store-wide LLM re-rendering, i.e. a synthesis path
        # the scope machinery does not control, and every such path is a
        # laundering site (the 0019 F4 precedent). Not filtered — not compiled,
        # not consulted, not rendered. The unscoped surface keeps it.
        # specs/0047 §4d (R-II RII-01): the wiki body and the call's ONE challenge snapshot come from one state —
        # bound_wiki reads the snapshot after the body and serves no body that asserts a fact the snapshot
        # withholds. A principal-bearing call has no wiki and reads the snapshot alone.
        wiki_basis: dict = {}             # specs/0003 §4c-ii v18.7 (C3-01): the served body's basis
        if view is not None:
            wiki, snap = None, None
        else:
            wiki, snap = _compile.bound_wiki(
                self.store, op_llm, user_id,
                self.config.wiki_recompile_after_writes,
                self.config.relations, _out=wiki_basis,
                wiki_input_budget=self.config.wiki_input_budget_tokens,
                variant_cap=self.config.wiki_variant_cap,
                item_cap=self.config.item_cap_tokens)
        # specs/0027 §4a/§4d — the semantic lane and the fused construction.
        # `semantic`: "auto" (default) attempts the lane iff an embedder with
        # id()/dim() is configured; True forces the attempt (degrading the
        # same way, reporting status); False disables it. Every degrade path
        # is a STATUS, never an exception (V6).
        # specs/0047 §4d: the call's ONE challenge snapshot, read before its edge reads (bound_wiki's, when the wiki
        # layer ran)
        if snap is None:
            snap = self.store.challenge_snapshot(user_id)
        sem_status, sm_pairs, sem_meta = "disabled", [], {}
        receipt_raw = None
        if view is None and semantic is False and policy is None:
            # today's path, literally (V10 byte-identity by construction)
            edges = subgraph_for_query(
                self.store, user_id, query,
                max_edges=self.config.max_subgraph_edges,
                coverage_share=self.config.subgraph_coverage_share,
                relations=self.config.relations, snap=snap)
        else:
            # Stage 0-1: one scan, scoped/shaped under the per-call view
            scored, relevant_ids, by_id = _lexical_scored(
                self.store, user_id, query, view=view)
            if semantic is not False:
                sem_status, sm_pairs = self._semantic_lane(
                    user_id, query,
                    visible_ids=set(by_id) if view is not None else None)
            if view is None and sem_status != "ok" and policy is None:
                # §4a degenerate identity: the construction collapses to
                # subgraph_for_query — taken literally, so the no-embedder /
                # invalid-output / no-storage / timeout paths reproduce the
                # legacy projection byte-identically (V3/V10)
                edges = subgraph_for_query(
                    self.store, user_id, query,
                    max_edges=self.config.max_subgraph_edges,
                    coverage_share=self.config.subgraph_coverage_share,
                    relations=self.config.relations, snap=snap)
            else:
                # v13 §4c: with a policy the fused construction runs on EVERY
                # path (the legacy projection is its degenerate identity, V10),
                # so the receipt exists on the non-semantic path too (C1)
                edges, raw_meta, receipt_raw = fused_subgraph_with_receipt(
                    scored, relevant_ids, by_id,
                    sm_pairs if sem_status == "ok" else [],
                    max_edges=self.config.max_subgraph_edges,
                    coverage_share=self.config.subgraph_coverage_share,
                    relations=self.config.relations,
                    policy_rank=(policy.ranks if policy is not None else None),
                    max_displaced=(policy.max_displaced if policy is not None else None),
                    snap=snap)
                sem_meta = {k: RecalledEdge(**v) for k, v in raw_meta.items()}
        # specs/0041 §4b-iii (tranche 4a): a REDACTED record is not returned — structurally present in the
        # store, content absent from every surface recall renders. By the attestation record (the store's
        # `redacted_targets`), never by marker bytes; §4d's existence fact stays in the journal, where it
        # was already disclosed. Applied AFTER retrieval, inside the visible set: a slot a redacted record
        # won is a recall-quality cost, not a disclosure one.
        redacted_edges = self.store.redacted_targets(user_id, "edge")
        redacted_episodes = self.store.redacted_targets(user_id, "episode")
        if redacted_edges:
            edges = [e for e in edges if e.id not in redacted_edges]
            sem_meta = {k: v for k, v in sem_meta.items() if k not in redacted_edges}
        # outcome events are structured records, not narrative — they'd crowd
        # out interaction history for high-volume consumers; their signal
        # reaches recall as counters rendered on the edges themselves
        episodes = [e for e in self.store.episodes(user_id)
                    if e.kind != "outcome" and e.id not in redacted_episodes]
        # THE RELATION, on the structured record sets themselves (§2's carrier
        # row): scope FIRST, then the §4e filters within the visible set (M-2,
        # narrow-only — a filter can never be an oracle for withheld material).
        # `n_visible` is computed inside the visible set too, so the M-3 report
        # never counts anything the principal cannot see.
        #
        # THE STATED RESIDUAL: `max_subgraph_edges` is applied by RETRIEVAL,
        # before this filter, so out-of-scope records can win selection slots
        # and a scoped principal may be handed fewer records than a store
        # holding only its own material would have yielded. That is a recall
        # QUALITY cost, not a disclosure one: the principal observes only a
        # count, never the cap being reached and never a withheld-count, so
        # the shortfall is indistinguishable from "little was relevant".
        # Pushing the relation down into retrieval is a recorded improvement.
        filter_report = ""
        if view is not None:
            # specs/0027 §4a Stage 0: the SELECTION is already scoped and
            # shaped (visibility+shape preceded ranking/collapse/I6 — the
            # deliberate principal-bearing order amendment); re-applying the
            # lens here is a no-op kept out. Episodes keep the existing
            # post-hoc lens below.
            # scope BEFORE the recency slice, never after: slicing first would
            # hand the principal fewer than `max_recent_episodes` whenever the
            # newest episodes were out of scope — a shortfall that is itself a
            # signal that other-scope records exist.
            episodes = view.scoped(episodes)
            n_visible = len(edges)
            edges = view.narrow(edges)
            if filters and not edges and n_visible:
                from .budgets import bounded_count as _bc
                filter_report = (f"(your filter matched 0 of the {_bc(n_visible)} "
                                 f"records visible to you)")
        elif filters:
            from .scope_read import narrow_edges
            edges = narrow_edges(edges, filters)
        episodes = episodes[-self.config.max_recent_episodes:]

        # specs/0003 §4c-ii: the structured contested surface + the de-duplicated
        # Recall.edges union, computed BEFORE rendering so the exposed members render in a
        # deterministic HIGH-priority CONTESTED block rather than the ordinary detail. The
        # exposed higher-authority grounded prior is present even if the query did not
        # select it (the I6a guarantee).
        # specs/0037 §4a (V-RENDER-SITES): the selection already excluded
        # procedural records by their own stamp/basis; this is the render
        # site's own reach to the ONE exclusion, so a future selection path
        # that forgets it cannot render a procedure here
        from .gate import exclude_procedural
        edges, _n_procedural = exclude_procedural(edges)
        contested, exposed_extra = self._build_contested(user_id, edges, view)
        seen = {e.id for e in edges}
        for e in exposed_extra:
            if e.id not in seen:
                edges.append(e)
                seen.add(e.id)
        # Only the GROUNDED (assertable) exposed members move into the grounded CONTESTED
        # block. A fenced exposed member (e.g. a query-selected quarantined challenger — a
        # full member in the STRUCTURED carrier) must stay on the unverified side of the
        # gate, so it is left in detail_edges to route through the unverified channel
        # (partition-preserving, §4c-ii).
        contested_ids = {e.id for g in contested for e in g.exposed if e.assertable}
        detail_edges = [e for e in edges if e.id not in contested_ids]
        # specs/0047 §4c–§4d (INV-R3, R6): a challenged fact, and its active same-value twin (F7), reaches NO
        # assertion surface — withheld from the contested block and from detail at every budget, and COUNTED before
        # any budget selection. The structured carriers keep the record, with its inspection entry.
        withheld_ids = {e.id for e in edges if snap.withheld(e)
                        and (e.assertable or e.quarantined or (e.active and e.use_only))}
        detail_edges = [e for e in detail_edges if not snap.withheld(e)]
        contested_render = [g.model_copy(update={"exposed": [m for m in g.exposed if not snap.withheld(m)]})
                            for g in contested]
        withheld_report = withheld_line(len(withheld_ids)) if withheld_ids else ""

        # the contested surface renders FIRST — HIGH priority, ahead of ordinary query
        # detail — so a refusal never demotes the prior below where it stood before it (the
        # finite-budget form of I6a). It IS budget-gated, not an unbounded surface (round-8
        # blocker 2); truncation is deterministic and flagged. specs/0012 I10: recall is
        # ALWAYS budgeted (the config default applies when the caller omits token_budget).
        # 2026-09-19 (the owner's word): its claim is CAPPED at `contested_render_share` of
        # the budget — first claim on the WHOLE budget starved RELEVANT DETAIL of the very
        # lines recall had ranked first (measured: 99.4% of the context was this block). The
        # first group line stays unconditional inside the renderer (I6a), and what the block
        # does not spend flows to detail below.
        contested_block, spent, c_trunc, c_loss = self._render_contested(
            contested_render, max(1, int(token_budget * self.config.contested_render_share)),
            self._est_tokens, receipt=rr)
        if filter_report:                       # §4e M-3, charged before detail
            spent += self._est_tokens(filter_report)
        if withheld_report:                     # 0047 §4d: charged before detail, never dropped
            spent += self._est_tokens(withheld_report)
        # the block's loss rides into the report as ONE object (I10b, 2026-09-19): the
        # report is emitted on the block's own flag, so `truncated` and the visible
        # line can never disagree about the contested class
        # specs/0003 §4c-ii v18.7 (C3-01): the bind read, after the last store read whose result can reach a response
        # that carries the body (the selection, the redaction sets, the episodes, the contested build) and before
        # rendering. A write for the user since the empty body's basis leaves it out of this one response.
        if _compile.empty_body_unbound(self.store, user_id, wiki, wiki_basis.get("basis")):
            wiki = None
        wiki, detail_grounded, unverified, d_trunc = self._fit_to_budget(
            wiki, detail_edges, episodes, max(0, token_budget - spent), query,
            contested_loss=c_loss, receipt=rr)
        truncated = c_trunc or d_trunc
        if rr is not None and wiki:
            # specs/0031 §4b: wiki-only synthesized text has no record ids; it is a `wiki` unit no verb can aim at,
            # its text the wiki exactly as admitted (clamped, marker kept, by the fitter above)
            rr.admit("wiki", None, wiki, "grounded")

        grounded_parts = []
        if filter_report:
            # §4e M-3: empty-result reporting IS principal-facing — computed
            # WITHIN the visible set, so it discloses nothing about what scope
            # withheld (the §3b line: withholding counts are operator-side).
            grounded_parts.append(filter_report)
        if wiki:
            grounded_parts.append(wiki)
        if contested_block:
            grounded_parts.append(contested_block)
        if detail_grounded:
            grounded_parts.append("## RELEVANT DETAIL\n" + detail_grounded)
        if withheld_report:
            grounded_parts.append(withheld_report)
        # an empty grounded part above unverified claims is "no VERIFIED facts" in this view, never "no memory"
        # (adoption probe 3), and never a claim about the store (SR1-03)
        grounded = "\n\n".join(grounded_parts).strip()
        if not grounded:
            # SR1-03's sibling (research's stage 1, marked A): "no memory yet" is a claim about the STORE, so it is
            # made only where the caller may see the whole user (no principal) and the user holds no record at all;
            # under a principal the line never varies with what the store holds (0020: that difference is the signal)
            if unverified:
                grounded = EMPTY_GROUNDED_BODY
            elif principal is None and not self.store.episodes(user_id, limit=1, include_retired=True) and not \
                    self.store.edges(user_id, active_only=False, include_quarantined=True):    # R2S-1: retired too
                grounded = "(no memory yet for this user)"
            else:
                grounded = EMPTY_VIEW_BODY

        context = grounded
        if unverified:
            context += ("\n\n## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)\n"
                        + unverified)
        self._record("recall", {**usage_finish(),
                                "wiki_used": bool(wiki), "subgraph_edges": len(edges),
                                "grounded_items": sum(1 for e in edges if not e.quarantined),
                                "unverified_items": sum(1 for e in edges if e.quarantined),
                                "trimmed": 1 if truncated else 0}, user_id)
        # V7: recalled_edges covers exactly the ranked query selection that
        # SURVIVED narrowing — an I6a/contention-preserved append has no
        # entry, and a filter-narrowed edge leaves none behind
        _final_ids = {e.id for e in edges}
        sem_meta = {k: v for k, v in sem_meta.items() if k in _final_ids}
        policy_receipt = None
        if receipt_raw is not None:
            policy_receipt = PolicyReceipt(recall_id=uuid4().hex,     # minted here, never by the caller
                                           policy_id=policy.policy_id, policy_version=policy.policy_version,
                                           tags_matched=tuple(policy.tags_matched),
                                           semantic_status=sem_status,
                                           recorded_at=utcnow().isoformat(), **receipt_raw)
            # specs/0027 §4g (v14): the receipt is DURABLE — written to the
            # store before this call returns, as the row the store reads back
            # (V-RECEIPT-DURABLE). A write failure raises out of recall
            # (V-RECEIPT-DURABLE-OR-LOUD): the answer is not returned as if
            # its trace existed.
            self.store.write_policy_receipt(user_id, receipt_row(policy_receipt))
        return Recall(context=context, grounded=grounded, unverified=unverified,
                      edges=edges, episodes=episodes,
                      tokens_estimated=self._est_tokens(context), truncated=truncated,
                      contested=contested,
                      recalled_edges=sem_meta, semantic_status=sem_status,
                      policy_receipt=policy_receipt,
                      inspection={e.id: snap.inspect(e, visible=(view.visible if view is not None else None),
                                                      cap_tokens=self.config.item_cap_tokens) for e in edges},
                      render_receipt=None if rr is None else rr.units)

    def _contested_line(self, g: "ContestedGroup",
                        line_budget: Optional[int] = None, emitted: Optional[list] = None):
        """One deterministic line for a contested group, budget-aware PACKED per
        specs/0012 §4c (I10i): the heading's subject/relation render CONTENT-CLAMPED
        under the group-heading allowance; the withheld marker is reserved FIRST; the
        MANDATORY member — the highest-effective-authority grounded member, which IS the
        preserved grounded prior here (the roles may alias; `0003` orders exposed higher
        authority first) — is emitted with content clamped to the remaining budget;
        further members are admitted only while they fit WHOLE, the emitted count
        reducing dynamically below `contested_members_per_line`; the withheld count
        reflects everything not emitted. A fenced member is NOT shown here — it stays in
        the unverified channel (partition-preserving, §4c-ii). Returns None if the group
        has no assertable member. Returns (line, squeezed, values_withheld) — the
        withheld COUNT rides with the line so the recall report can state it (I10b,
        amended 2026-09-19) from the same computation that wrote the suffix."""
        from .budgets import (MEMBER_FRAMING_COST, MIN_MEMBER_CONTENT,
                              WITHHELD_MARKER_RESERVE, clamp_item, est_tokens)
        grounded = [e for e in g.exposed if e.assertable]
        if not grounded:
            return None, False, 0
        k_cap = self.config.contested_members_per_line
        # specs/0055 §4e: the heading and every member are masked before their clamps
        head = clamp_item(f"{_cred.mask_text(g.subject)} {_cred.mask_text(g.relation)}",
                          self.config.group_heading_allowance_tokens)
        tail = " — CONTESTED (no single current value)"

        def _member(e, content_cap):
            return (f"{clamp_item(_cred.mask_text(e.object), content_cap)} "
                    f"[{e.provenance.author_of_evidence.value}]")

        squeezed = False
        shown = []                                          # (edge, its rendered member text), in line order
        if line_budget is None:
            members = [_member(e, self.config.item_cap_tokens) for e in grounded[:k_cap]]
            shown = list(zip(grounded[:k_cap], members))
            withheld = len(grounded) - len(members)
        else:
            remaining = (line_budget - est_tokens(f"- {head}: {tail}")
                         - WITHHELD_MARKER_RESERVE)
            # the mandatory member, content-clamped to what remains (never dropped)
            # the mandatory ROLES (R-impl3-5): the highest-effective-authority member
            # (grounded[0], authority-sorted) AND the preserved grounded PRIOR —
            # resolved via the group's prior_edge_ids carrier. The roles MAY ALIAS
            # (a USER prior against SYSTEM challengers): then the mandatory set is
            # ONE member and every challenger is optional (fit-whole or withheld).
            prior_ids = set(g.prior_edge_ids or ())
            mandatory = [grounded[0]]
            if prior_ids and grounded[0].id not in prior_ids:
                prior_member = next((m for m in grounded[1:] if m.id in prior_ids), None)
                if prior_member is not None:
                    mandatory.append(prior_member)
            members = []
            for i, m in enumerate(mandatory):
                share = max(1, len(mandatory) - i)
                m_cap = max(MIN_MEMBER_CONTENT,
                            min(self.config.item_cap_tokens,
                                (remaining // share) - MEMBER_FRAMING_COST))
                rendered = _member(m, m_cap)
                squeezed = squeezed or est_tokens(m.object) > m_cap
                members.append(rendered)
                shown.append((m, rendered))
                remaining -= est_tokens(rendered)
            for e in grounded[len(mandatory):]:
                if len(members) >= k_cap:
                    break
                cand = _member(e, self.config.item_cap_tokens)
                if est_tokens(cand) > remaining:           # admit only while it fits WHOLE
                    continue
                members.append(cand)
                shown.append((e, cand))
                remaining -= est_tokens(cand)
            withheld = len(grounded) - len(members)
        squeezed = squeezed or withheld > 0                # I10i: EVERY cause signals
        vals = " / ".join(members)
        wh = f" (+{withheld} more contending values withheld)" if withheld > 0 else ""
        if emitted is not None:
            # specs/0031 §4b: each emitted member is a unit; the group's framing rides with it (round 2's answer 5),
            # as the heading as rendered and the withheld count, never an unadmitted member's value
            # TT-R3-02: the subject rides in that framing as the clamped head rendered it, never the raw field
            from .budgets import rendered_subject
            subj = None if g.subject == "user" else rendered_subject(g.subject, head)
            emitted.extend((e, text, f"contested: {head} — no single current value"
                                     + (f"; {withheld} more contending values withheld" if withheld else ""), subj)
                           for e, text in shown)
        return f"- {head}: {vals}{wh}{tail}", squeezed, withheld

    def _render_contested(self, contested, budget=None, est=None, receipt=None):
        """Render the deterministic CONTESTED FUNCTIONAL FACTS block from the grounded
        exposed members (specs/0003 §4c-ii). Returns (block, tokens_spent, truncated,
        loss). Group lines are walked IN THE ORDER `_build_contested` RETURNS THEM —
        §4c-iii's key (`contention.contested_group_key`: preservation tier, then
        ambiguity, then visible size, then slot) — with a best-effort minimum (the first line is
        unconditional — the higher-authority prior is never dropped); the rest are
        budget-gated so the surface is bounded, and the cut takes that order's tail.
        `loss` is the `ContestedLoss` (whole groups dropped after the cut / contending
        values withheld inside rendered lines / this flag) computed HERE, once, and
        carried to the recall report unchanged (I10b, amended 2026-09-19)."""
        from .budgets import NO_CONTESTED_LOSS, ContestedLoss
        if not contested:
            return "", 0, False, NO_CONTESTED_LOSS
        heading = "## CONTESTED FUNCTIONAL FACTS (no single current value; do not assert one)"
        if budget is None or est is None:
            emitted = [] if receipt is not None else None
            results = [self._contested_line(g, emitted=emitted) for g in contested]
            lines = [ln for ln, _sq, _wh in results if ln]
            if not lines:
                return "", 0, False, NO_CONTESTED_LOSS
            for e, text, framing, subj in (emitted or []):
                receipt.admit("edge", e, text, "contested", [framing] + _trust_edge_annotations(e),
                              subject=None if subj is None else (subj, framing, len("contested: ")))
            # I10i: within-group withholding signals truncation even unbudgeted
            any_sq = any(sq for ln, sq, _wh in results if ln)
            withheld = sum(wh for ln, _sq, wh in results if ln)
            return (heading + "\n" + "\n".join(lines), 0, any_sq,
                    ContestedLoss(0, withheld, any_sq))
        remaining = budget - est(heading + "\n")
        sel, truncated, withheld, dropped = [], False, 0, 0
        for idx, g in enumerate(contested):
            # I10i: each group line is PACKED within what remains — one group can
            # never break the budget (the first line is best-effort unconditional)
            emitted = [] if receipt is not None else None
            line, squeezed, wh = self._contested_line(
                g, line_budget=remaining if sel else max(remaining, 1), emitted=emitted)
            if line is None:
                continue
            truncated = truncated or squeezed             # EVERY cause signals (I10i)
            cost = est(line)
            if cost > remaining and sel:
                truncated = True
                # the cut: this group and every RENDERABLE group after it is dropped
                # whole — counted here, from the same walk, never re-derived later
                dropped = 1 + sum(1 for h in contested[idx + 1:]
                                  if self._contested_line(h)[0] is not None)
                break
            sel.append(line)
            for e, text, framing, subj in (emitted or []):  # admitted: the line made it into the block
                receipt.admit("edge", e, text, "contested", [framing] + _trust_edge_annotations(e),
                              subject=None if subj is None else (subj, framing, len("contested: ")))
            withheld += wh
            remaining -= cost
        if not sel:
            return "", 0, False, NO_CONTESTED_LOSS
        block = heading + "\n" + "\n".join(sel)
        return block, est(block), truncated, ContestedLoss(dropped, withheld, truncated)

    def _build_contested(self, user_id: str, query_edges: list, view=None):
        """Build the structured contested surface for the LIVE refusal contentions of a
        user (specs/0003 §4c-ii). Returns (contested_groups, exposed_edges). A member is
        EXPOSED (full Edge) iff it is grounded/assertable — the preserved higher-authority
        prior AND every same-partition grounded member I6 deterministically renders, even
        one the query did not select (round-11) — OR the query already selected it. The
        unseen fenced CROSS-partition challenger (use_only/quarantined, not selected) is
        content-free linkage only: no query-independent reach on any surface (round-10 A).

        specs/0020 §4c N-2, when `view` is present: supersession/contention STATUS is
        global truth and still renders, but the CONTENT and ATTRIBUTION of an invisible
        party do not. A CROSS-SCOPE (policy-hidden) member degrades to content-free
        `ContestedLinkage` — the 0003 §4c-ii precedent, reused rather than re-derived —
        while an UNRESOLVED member is dropped outright (V13: fail-closed means invisible,
        not "invisible with a pointer"). A group with NO exposed member is dropped
        ENTIRELY, which is what keeps N-1 true: an all-withheld store is
        indistinguishable from an empty one on the full `Recall` value.

        specs/0003 §4c-iii: the groups are returned in `contention.contested_group_key`'s
        order (preservation tier, then ambiguity, then visible size, then slot), not by slot."""
        try:
            refusals = self.store.refusals(user_id)
        except NotImplementedError:
            return [], []
        if not refusals:
            return [], []
        relations = self.config.relations
        redacted = self.store.redacted_targets(user_id, "edge")         # specs/0041 §4b-iii: not returned
        active = {e.id: e for e in self.store.edges(user_id, active_only=True,
                                                    include_quarantined=True) if e.id not in redacted}
        # §4c N-2: the GROUPS are formed over the whole active set — a contention is
        # global lifecycle truth and its existence is not scope's to rewrite — while
        # WHAT EACH MEMBER DISCLOSES is decided by the relation, below.
        dropped: set = set()                    # UNRESOLVED: invisible, no pointer
        withheld: set = set()                   # cross-scope: content-free linkage
        if view is not None:
            shaped = {}
            for eid, e in active.items():
                if view.visible(e):
                    shaped[eid] = view.shape(e)
                elif view.evidence(e) == _SCOPE_UNRESOLVED:
                    dropped.add(eid)
                else:
                    withheld.add(eid)
            active = {**active, **shaped}       # visible members carry the shaping
        selected = {e.id for e in query_edges}
        groups: dict = {}
        group_priors: dict = {}
        retained = retained_refusal_ids(self.store, user_id)          # specs/0044 §4d
        for r in refusals:
            prior, inc = active.get(r.prior_edge_id), active.get(r.incoming_edge_id)
            if is_live_refusal(r, prior, inc, relations, retained):   # the ONE predicate (veracium.contention)
                groups.setdefault((prior.subject, r.relation), set()).update(
                    [prior.id, inc.id])
                group_priors.setdefault((prior.subject, r.relation), set()).add(prior.id)
        result, exposed_all, keys = [], [], {}
        for (subject, relation), member_ids in sorted(groups.items()):
            members = [active[mid] for mid in member_ids if mid not in dropped]
            exposed, linkage, fenced = [], [], set()
            for m in members:
                if m.id in withheld:            # §4c N-2: status, never content
                    linkage.append(ContestedLinkage(
                        edge_id=m.id, partition="unverified",
                        authority=_edge_effective(m)))
                elif m.assertable or m.id in selected:
                    exposed.append(m)
                else:
                    fenced.add(m.id)            # visible, not emitted: in §4c-iii's V
                    linkage.append(ContestedLinkage(
                        edge_id=m.id, partition="unverified",
                        authority=_edge_effective(m)))
            if view is not None and not exposed:
                # N-1: a group with nothing visible does not exist on a
                # principal-facing surface — otherwise the all-withheld store
                # would be distinguishable from the empty one.
                continue
            exposed.sort(key=lambda e: (-_edge_effective(e), e.id))
            linkage.sort(key=lambda x: (-x.authority, x.edge_id))
            # specs/0003 §4c-iii.6 4a, read from the PUBLISHED members (the shaped authorities): R = what the renderer
            # emits, V = every exposed member plus the FENCED linkage, never the withheld (policy-hidden) one
            keys[(subject, relation)] = contested_group_key(
                subject, relation, [_edge_effective(e) for e in exposed if e.assertable],
                [_edge_effective(e) for e in exposed] + [x.authority for x in linkage if x.edge_id in fenced])
            result.append(ContestedGroup(
                subject=subject, relation=relation, exposed=exposed, linkage=linkage,
                prior_edge_ids=sorted(
                    i for i in group_priors.get((subject, relation), ())
                    if i not in dropped)))
            exposed_all.extend(exposed)
        # the group ORDER is applied here, after the loop: `exposed_all` keeps the slot order the loop builds (it feeds
        # the detail candidates, which §4c-iii does not reorder) — do not move this sort into the loop
        result.sort(key=lambda g: keys[(g.subject, g.relation)])
        return result, exposed_all

    def _fit_to_budget(self, wiki: Optional[str], edges, episodes,
                       budget: int, query: str = "", *,
                       assertable=None, claims=None,
                       render=None, contested_loss=None, receipt=None) -> tuple[Optional[str], str, str, bool]:
        """Greedy selection under the token budget in the specs/0012 I10f precedence
        (mirroring the surface order; the contested block was already charged upstream):

        1. query-RELEVANT flagged assertable detail (warnings, most-overdue first);
        2. claim/inference flag lines — safety context, BEFORE the wiki (I10h);
        3. remaining assertable detail (query-relevant first, then unrelated flagged,
           then the rest in relevance order);
        4. the wiki, under its render SHARE of the budget, body clamped with the
           compile marker line kept intact (the framing is never severed);
        5. grounded episodes, newest-first admission, rendered chronologically.

        Every item is clamped at the item cap (framing + content, I10a); the
        truncation report marker is charged from the reserve BEFORE selection and
        reports dropped counts per class, SAFETY distinctly, and the CONTESTED class
        (groups dropped / values withheld) from the `contested_loss` the renderer
        computed upstream — the report is emitted whenever ANY class lost, the
        contested block's own flag included (I10b, amended 2026-09-19); class decides
        priority, the gate decides presentation — classification never moves an
        item across the partition (I10f)."""
        from .budgets import NO_CONTESTED_LOSS, RECALL_REPORT_RESERVE, clamp_item
        c_loss = contested_loss if contested_loss is not None else NO_CONTESTED_LOSS
        est = self._est_tokens
        cap = self.config.item_cap_tokens
        qtok = set(re.findall(r"[a-z0-9]+", (query or "").lower()))
        # specs/0028 §4c — the as-of branch supplies its own assertability
        # and claim predicates (its T-verdict) and its own line renderer, so
        # the budget partition never reads `Edge.assertable` there
        # (V-ONE-CLOCK). Unsupplied: today's predicate and renderer, verbatim.
        is_assertable = assertable if assertable is not None else _asserted_today
        render_fn = render if render is not None else render_edges

        def _rel(e) -> bool:
            etok = set(re.findall(r"[a-z0-9]+",
                                   f"{e.subject} {e.relation} {e.object} {e.note}".lower()))
            return bool(qtok & etok)

        assertable = [e for e in edges if is_assertable(e)]
        flagged_rel = [e for e in assertable if e.needs_confirmation and _rel(e)]
        flagged_rel.sort(key=lambda e: (e.provenance.observed_at, e.id))   # most overdue
        flagged_unrel = [e for e in assertable if e.needs_confirmation and not _rel(e)]
        flagged_unrel.sort(key=lambda e: (e.provenance.observed_at, e.id))
        rest = [e for e in assertable if not e.needs_confirmation]         # relevance order
        # I10f: the full taxonomy — COMMITMENTS (dated, nearest first) rank above plain
        # context; VARIANTS (a further member of a (subject, relation) group already
        # represented) rank LAST, below the wiki. Variancy never demotes the first
        # representative.
        _date_re = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
        commitments = [e for e in rest if _date_re.search(e.object + " " + e.note)]
        commitments.sort(key=lambda e: (_date_re.search(e.object + " " + e.note).group(0),
                                        e.id))                             # nearest first
        commit_ids = {e.id for e in commitments}
        plain, variants, _seen_groups = [], [], set()
        for e in rest:
            if e.id in commit_ids:
                continue
            g = (e.subject, e.relation)
            (variants if g in _seen_groups else plain).append(e)
            _seen_groups.add(g)

        from .budgets import clamp_edge_line

        claim_edges = ([e for e in edges if e.quarantined or (e.active and e.use_only)]
                       if claims is None else [e for e in edges if claims(e)])
        # I10h protects the QUERY-MATCHED claim flag above the wiki; an unmatched claim
        # renders fenced but admits after the wiki (it outranks only variants).
        claims_matched = [e for e in claim_edges if _rel(e)]
        claims_unmatched = [e for e in claim_edges if not _rel(e)]
        # claim lines carry their never-assert label at the FRONT; content still
        # clamps first so the label+content pair stays within the cap (I10c)
        def _claim_lines(es):
            # (record, line) pairs, so an admission can name its record (specs/0031 §4b); the lines are today's
            return [(e, ln) for e, ln in
                    ((e, clamp_edge_line(e, cap, render_fn)) for e in es) if ln]
        # 0023 §4a-iv / N14: the render split runs on the SHARED predicate —
        # assertable to ordinary detail, everything else to the fenced section
        # (fenced, not suppressed: Q5)
        # specs/0055 §4e: a stored summary is masked BEFORE its clamp (a cut never leaves a credential fragment)
        ep_lines = [(e, clamp_item(f"[{e.date}] {_cred.mask_text(e.summary)}", cap)) for e in episodes
                    if is_assertable(e)]
        tp_ep_lines = [(e, clamp_item(f"[{e.date}] {_cred.mask_text(e.summary)}", cap)) for e in episodes
                       if not is_assertable(e)]

        def _unit(record, line, partition):
            if receipt is not None:
                kind = "edge" if isinstance(record, Edge) else "episode"
                # TT-R3-02: the subject as `render_edges` placed it in this line (its format, its prefix constant)
                from .graph import edge_subject_span
                span = edge_subject_span(record) if kind == "edge" else None
                receipt.admit(kind, record, line, partition,
                              _trust_edge_annotations(record) if kind == "edge" else [],
                              subject=None if span is None else (span[0], line, span[1]))

        headers = est("## RELEVANT DETAIL\n") \
            + est("\n\n## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)\n")
        remaining = budget - headers - RECALL_REPORT_RESERVE   # I10b: report reserved first

        n_clamped = 0

        def _admit_edges(es, sel, best_effort_first=False):
            # I10a: the best-effort FIRST item is clamped TO FIT the remaining budget
            # (content-first, so its safety framing survives) — an oversized item is
            # clamped, never emitted whole and never silently dropped; a clamp is a
            # truncation EVENT and is counted, never silent
            dropped = 0
            nonlocal remaining, n_clamped
            for k, e in enumerate(es):
                raw = render_fn([e])
                line = clamp_edge_line(e, cap, render_fn)
                if not line:
                    continue
                if est(raw) > cap:
                    n_clamped += 1
                cost = est(line) + 1                       # +1: the join newline
                if cost > remaining:
                    if best_effort_first and k == 0 and not sel and remaining >= 16:
                        line = clamp_edge_line(e, remaining - 1, render_fn)
                        cost = est(line) + 1
                        if cost <= remaining:
                            n_clamped += 1                 # clamp-to-fit SIGNALS (I10a)
                            sel.append(line)
                            _unit(e, line, "grounded")
                            remaining -= cost
                            continue
                    dropped += 1
                    continue
                sel.append(line)
                _unit(e, line, "grounded")
                remaining -= cost
            return dropped

        def _admit(pairs, sel):
            # every line admitted here lands in the FENCED section (claims and third-party episodes)
            dropped = 0
            nonlocal remaining
            for record, line in pairs:
                cost = est(line) + 1                       # +1: the join newline
                if cost > remaining:
                    dropped += 1
                    continue
                sel.append(line)
                _unit(record, line, "fenced")
                remaining -= cost
            return dropped

        # the FROZEN §4c(iv) recall order: contested (upstream) → query-relevant flagged
        # → query-matched claim flags → other flagged → commitments → the WIKI within its
        # share → relevance-ranked grounded edges → episodes (newest) → the remaining
        # unverified partition → variants LAST.
        sel_edges: list[str] = []
        d_flag_rel = _admit_edges(flagged_rel, sel_edges, best_effort_first=True)
        sel_unv: list[str] = []
        d_safety = _admit(_claim_lines(claims_matched) + tp_ep_lines, sel_unv)
        d_flag_unrel = _admit_edges(flagged_unrel, sel_edges)
        d_commit = _admit_edges(commitments, sel_edges)

        wiki_dropped = False
        if wiki:
            share_cap = int(budget * self.config.wiki_render_share)
            allowance = min(remaining, share_cap)
            if est(wiki) <= allowance:
                remaining -= est(wiki)
            else:
                marker_ln = wiki.splitlines()[-1] if wiki.splitlines() else ""
                keep_marker = marker_ln.startswith("[[veracium-wiki-compile:")
                body_allow = allowance - (est(marker_ln) if keep_marker else 0)
                if body_allow >= 16:                       # clamp the BODY, keep the marker
                    body = "\n".join(wiki.splitlines()[:-1]) if keep_marker else wiki
                    clamped = clamp_item(body, body_allow)
                    wiki = clamped + ("\n" + marker_ln if keep_marker else "")
                    remaining -= est(wiki)
                    wiki_dropped = True                    # counted as clamped in the report
                else:
                    wiki, wiki_dropped = None, True

        d_plain = _admit_edges(plain, sel_edges,           # grounded edges AFTER the wiki
                               best_effort_first=not sel_edges)
        sel_eps: list[str] = []
        d_eps = 0
        for ep, line in reversed(ep_lines):                # episodes: newest first
            cost = est(line) + 1                           # +1: the join newline
            if cost > remaining:
                d_eps += 1
                continue
            sel_eps.append(line)
            _unit(ep, line, "grounded")
            remaining -= cost
        sel_eps.reverse()                                  # render chronologically
        d_safety += _admit(_claim_lines(claims_unmatched), sel_unv)   # remaining partition
        d_variants = _admit_edges(variants, sel_edges)                # variants LAST

        d_detail = d_flag_rel + d_flag_unrel + d_commit + d_plain + d_variants
        truncated = bool(d_detail or d_safety or wiki_dropped or d_eps or n_clamped
                         or c_loss.truncated)
        detail = "\n".join(sel_edges + sel_eps).strip()
        if truncated:                                      # the I10b report, per class,
            from .budgets import recall_report_line        # counts BOUNDED-WIDTH (R9-2);
            detail = (detail + ("\n" if detail else "")    # the grammar lives in budgets
                      + recall_report_line(d_detail, d_safety, c_loss.groups_dropped,
                                           c_loss.values_withheld, n_clamped,
                                           wiki_dropped, d_eps))
        unverified = "\n".join(sel_unv).strip()
        return wiki, detail, unverified, truncated

    def answer(self, user_id: str, query: str, *, principal=None,
               **filters) -> str:
        """Recall + the evidence-grounded abstention gate → a direct answer.

        The convenience path for hosts that want veracium to answer: it answers only
        from grounded memory, refuses to assert unverified third-party claims, and
        abstains ("I don't know") rather than confabulate when memory lacks the
        answer — the finding-23 fix for both confabulation and the episodic
        injection leak.

        `principal` / `**filters` (specs/0020 §2, external F3) are THREADED into
        the internal recall — an answer path that ignored the principal would be
        a public bypass of the whole boundary, so this method never calls recall
        unscoped when it was given a principal (V11). The gate then sees exactly
        the scoped partitions: cross-scope material arrives third-party-shaped on
        the never-assert side, and a scope-blinded answer saying "no record" is
        isolation WORKING, not abstention failing."""
        r = self.recall(user_id, query, principal=principal,
                        **filters)        # already error-guarded; its own context
        t0 = time.perf_counter()
        with self._usage_operation(user_id, "answer") as (op_llm, usage_finish):
            try:
                ans = _gate.answer(op_llm, query, r.grounded, r.unverified)
            except Exception as e:
                self._on_error("answer", e, user_id)
                raise
            self._record("answer", {"abstained": bool(_ABSTAINED.search(ans)),
                                    "ms": int((time.perf_counter() - t0) * 1000),
                                    **usage_finish()}, user_id)
        return ans

    # -- maintenance -------------------------------------------------------
    def maintain(self, user_id: str, *, consolidate: bool = True) -> dict:
        """Run lifecycle maintenance for `user_id` — the "overnight" job.

        Applies volatility-driven expiry (transient facts lapse, durable facts
        get flagged possibly-stale, never silently dropped) and, if enabled,
        consolidates cold episodes into denser records (preserving first failures,
        fixes, illnesses, and dated commitments). Idempotent; call on a schedule."""
        with self._usage_operation(user_id, "maintain") as (op_llm, usage_finish):
            try:
                report = {"expiry": _lifecycle.expire(self.store, user_id, self.config)}
                if consolidate:
                    report["consolidation"] = _lifecycle.consolidate(
                        self.store, op_llm, user_id, self.config)
            except Exception as e:
                self._on_error("maintain", e, user_id)
                raise
            ex, co = report["expiry"], report.get("consolidation", {})
            # specs/0021 §4b — THE AMENDED AUDIT CARDINALITY: one ADDITIVE
            # `consolidate-pool` event per ATTEMPTED pool, then the aggregate
            # `maintain` event PRESERVED as the operation's terminal line. A
            # below-threshold pool was not attempted and emits nothing; it is
            # still reported in the return value, so the result stays the
            # complete picture of the partition while the log stays a record
            # of work done. `error_code` is the CLOSED CONTENT-FREE enum the
            # lifecycle layer produced — never `str(exc)`, because an LLM
            # exception can echo episode text into a sink whose invariant is
            # no-memory-text-ever. (Telemetry has no `consolidate-pool` event,
            # so its whitelist drops these and the shipped `maintain` mapping
            # below is untouched — the preserved-key contract, mechanically.)
            for pool_key, pool in (co.get("pools") or {}).items():
                if pool.get("status") == "below-threshold":
                    continue
                fields = {"pool_key": pool_key, "status": pool["status"],
                          "consolidated": pool["consolidated"],
                          "into": pool["into"]}
                if pool.get("error") is not None:
                    fields["error_code"] = pool["error"]
                self._record("consolidate-pool", fields, user_id)
                # specs/0055 §4c: the consolidation draft's withheld spans (source model_output)
                self._cred_withheld(user_id, "maintain", pool.get("credentials_withheld") or {},
                                    source="model_output")
            self._record("maintain", {"lapsed": ex["lapsed"], "decayed": ex["decayed"],
                                      "flagged": ex["flagged_for_confirmation"],
                                      "consolidated_in": co.get("consolidated", 0),
                                      "consolidated_out": co.get("into", 0),
                                      **usage_finish()}, user_id)
        return report

    # -- self-check --------------------------------------------------------
    def self_check(self, *, record: bool = True) -> dict:
        """Run veracium's load-bearing guarantees (supersession, injection defense,
        abstention) against a fresh throwaway store and return content-free
        pass/fail counters. Uses this Memory's own `llm`; never touches this
        Memory's store. When telemetry is wired and `record` is True, the counters
        are emitted as a content-free `selfcheck` event (see veracium.selfcheck)."""
        from . import selfcheck as _sc
        result = _sc.run(self.llm, relations=self.config.relations)
        if record:
            self._record("selfcheck", result)  # non-scalar keys are dropped by the collector
        return result

    # -- telemetry (opt-in, content-free; see veracium.telemetry) ------------
    def flush_telemetry(self) -> bool:
        """If telemetry is enabled and due, POST the anonymous aggregate. Safe to
        call often (e.g. after each request or on a timer) — it no-ops until the
        interval elapses and never raises. Returns True if a send happened."""
        if self.telemetry is None:
            return False
        from . import telemetry as _t
        return _t.flush_if_due(_t.TelemetryConfig.load(), self.telemetry)

    def telemetry_preview(self) -> Optional[dict]:
        """Exactly what a flush would send right now, or None if telemetry is off."""
        if self.telemetry is None:
            return None
        from . import telemetry as _t
        return _t.preview(_t.TelemetryConfig.load(), self.telemetry)

    # -- diagnostics / error reporting (opt-in; see veracium.diagnostics) -----
    def report_error(self, *, interactive: Optional[bool] = None) -> bool:
        """Send the captured local error log for diagnosis, subject to consent
        (advance permission, or an interactive yes). No-ops if diagnostics is off,
        nothing was captured, or no endpoint is configured; never raises. A host
        that caught an veracium error can call this to offer to report it."""
        if self.diagnostics is None or not self.diagnostics.has_pending():
            return False
        return self.diagnostics.send(interactive=interactive)

    def diagnostics_preview(self) -> Optional[dict]:
        """Exactly what a report would send (redacted if enabled) — the log content
        that would leave the machine — or None if diagnostics is off."""
        if self.diagnostics is None:
            return None
        return self.diagnostics.preview()

    # -- host queries ----------------------------------------------------------
    def list_entities(self) -> list[dict]:
        """Distinct ids that have accumulated memory, with edge/episode counts.
        For hosts deciding what to recall proactively or auditing coverage.
        Host/admin surface — not exposed over MCP by design (cross-user
        enumeration is not an agent tool)."""
        return self.store.list_users()

    def introspect(self, user_id: str, *, mode: str = "summary") -> dict:
        """The formatted transparency view: "what do you know about me, and
        where did it come from?" — counts by relation / evidence author /
        disclosure tier, lifecycle state, retired history by reason, episode
        counts, and `wiki_compile_record` (specs/0012: the cached wiki's
        authoritative compile-drop marker, parsed + verbatim — status
        ok/absent/legacy/malformed; counts int or "999+"; the cached record
        only, never a current-store hypothetical);
        mode="categories" adds the facts themselves grouped by
        relation, rendered with their provenance markers. LLM-free and
        store-only; the complete raw dump remains `export_memory()`, erasure
        remains `forget()`. CLI: `veracium introspect --user X`."""
        from . import introspect as _introspect
        try:
            out = _introspect.report(self.store, user_id, mode=mode,
                                     relations=self.config.relations)
        except Exception as e:
            self._on_error("introspect", e, user_id)
            raise
        self._record("introspect", {"facts": out["facts"],
                                    "claims": out["unverified_claims"],
                                    "episodes": sum(out["episodes"].values())},
                     user_id)
        # specs/0017 §4d/§4f: the local, consent-independent usage view —
        # present only when metered; empty for a forgotten/unseen user;
        # instance-lifetime scope stated in the payload, not implied.
        if self._metered_handle is not None or self._llm_usage.get(user_id):
            with self._usage_lock:
                roles = {role: dict(v)
                         for role, v in self._llm_usage.get(user_id, {}).items()}
            out["llm_usage"] = {"scope": "instance-lifetime", "roles": roles}
        return out

    def edges_since(self, user_id: str, since) -> list[Edge]:
        """Edges *learned* after `since` (ISO date/datetime string, or a
        datetime): learned is the store-minted `recorded_at` of the edge's
        FIRST journal event (specs/0029's transaction-time carrier;
        specs/0049), never the event's own date (`valid_from`,
        `provenance.observed_at`). Includes superseded and quarantined edges;
        filter on `.active` / `.assertable` / provenance as needed. A store that cannot supply
        first-record times REFUSES (`NotImplementedError`), and so does an
        edge with no journal event (`ValueError`): a learned time that cannot
        be read is not guessed. Both reads (the first-record times and the
        edge listing) are ONE snapshot, the store's `read_window`, so a write
        landing during the call is either wholly in the result or wholly out.

        A NEW-RECORD listing, not a change feed: a later confirm, update,
        redaction or reinstatement of an edge does not make it newly learned,
        and a store migrated from before the journal (specs/0029's baseline)
        can only say an edge was learned BY the migration. The cutoff is a
        strict timestamp, not a lossless pagination cursor: two transactions
        may share a `recorded_at`."""
        from datetime import datetime, timezone
        if isinstance(since, str):
            since = datetime.fromisoformat(since)
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        # specs/0049 v2.2 (0049-R1-01): the timestamp map and the edge listing are read in ONE snapshot, the store's
        # read window, so a writer committing between them cannot make a complete journal look incomplete. Under WAL
        # the writer commits and this read keeps its snapshot; under the default journal it waits for the window.
        with self.store.read_window(user_id):
            learned = self.store.first_recorded_at(user_id)
            with _SITE_EDGES_SINCE_NO_JOURNAL.consult():
                if learned is None:
                    raise _SITE_EDGES_SINCE_NO_JOURNAL.fire(NotImplementedError(
                        f"{type(self.store).__name__} cannot supply first-record times (specs/0029's transaction-time "
                        f"journal), so it cannot say when an edge was learned (specs/0049)"), "no-journal")
            out = []
            for e in self.store.edges(user_id, active_only=False, include_quarantined=True):
                at = learned.get(e.id)
                with _SITE_EDGES_SINCE_NO_EVENT.consult():
                    if at is None:
                        raise _SITE_EDGES_SINCE_NO_EVENT.fire(ValueError(
                            f"edge {e.id!r} has no journal event, so when it was learned is unknown (specs/0049)"),
                            "no-event")
                t = datetime.fromisoformat(at)
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                if t > since:
                    out.append(e)
        return out

    # -- user feedback verbs -------------------------------------------------
    def _refuse_attested(self, user_id: str, edge_id: str, op: str) -> None:
        """specs/0041 round 10: dispute, record_outcome and correct each quote the record they act on in a NEW episode;
        on an ATTESTED-redacted record that quote would carry the treated record's marker at best and, read before a
        redaction, its content at worst. Refused by the attestation record, read inside the caller's `atomic()`."""
        with _SITE_FEEDBACK_ATTESTED.consult():
            if edge_id in self.store.redacted_targets(user_id, "edge"):
                raise _SITE_FEEDBACK_ATTESTED.fire(ValueError(
                    f"refused: edge {edge_id!r} is redacted — {op} quotes the record it acts on, and a redacted "
                    f"record is not quoted (specs/0041 §4b-ii, round 10)"), op)

    def _trust_target(self, user_id: str, kind: str, record_id: str):
        """The user's own record by id, of either kind, in any state (inactive and quarantined included), or None.
        Another user's id and an unknown id are both None: the lookup is scoped by the user (specs/0031 §4f, INV-TT7)."""
        if kind == "edge":
            return next((e for e in self.store.edges(user_id, active_only=False, include_quarantined=True)
                         if e.id == record_id), None)
        return next((e for e in self.store.episodes(user_id) if e.id == record_id), None)

    def _trust_scope_gate(self, user_id: str, principal, *, kind: str, record_id: str,
                          writes: bool, source_id: Optional[str] = None):
        """specs/0031 §4f §3b, the decision table under a principal (the owner's TT-R1-04 ruling, "OWN only"), run
        INSIDE the calling verb's own transaction and before anything is written. Returns the principal's view, or
        None when `principal` is None — then no scope code runs at all (0020 V1) and the verb is today's.

        The gates, in §4a's order, each raising `TrustRefused` and writing nothing:
          5. scope configuration: `scope_unconfigured` (no policy), `principal_ungroupable` (no source_id);
          6. the binding's source, for the three verbs that WRITE a membership-bearing record (`writes`): none is
             `source_unbound`; a source the view does not class `OWN` is `source_out_of_scope` — a probe whose only
             membership evidence is that source is classified through `ScopeView.classify_unwritten`;
          7. the target: `OWN` is acted on; `SHARED` and `CROSS_VISIBLE` are `out_of_scope`; `CROSS_HIDDEN`,
             `UNRESOLVED`, another user's id and an unknown id are all `not_found_in_scope`, one response."""
        if principal is None:
            return None
        from .trust_tools import TrustRefused
        from .scope import Identity
        with _SITE_TRUST_SCOPE_GATE.consult():          # every refusal fires with its reason as the label (the trace shows the branch)
            if self.scope_policy is None:
                raise _SITE_TRUST_SCOPE_GATE.fire(TrustRefused("scope_unconfigured"), "scope_unconfigured")
            if isinstance(principal, Identity) and not principal.groupable:
                raise _SITE_TRUST_SCOPE_GATE.fire(TrustRefused("principal_ungroupable"), "principal_ungroupable")
            view = self._scope_view(user_id, principal)  # a non-Identity principal raises ScopeError (a refusal)
            if writes:
                if source_id is None:
                    raise _SITE_TRUST_SCOPE_GATE.fire(TrustRefused("source_unbound"), "source_unbound")
                probe = Episode(id="ep-trust-source-probe", user_id=user_id, date=_today_utc(), summary="",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                      evidence_ref="trust-tools:source-probe", source_id=source_id))
                if view.classify_unwritten(probe) != "OWN":
                    raise _SITE_TRUST_SCOPE_GATE.fire(TrustRefused("source_out_of_scope"), "source_out_of_scope")
            record = self._trust_target(user_id, kind, record_id)
            if record is None:
                raise _SITE_TRUST_SCOPE_GATE.fire(TrustRefused("not_found_in_scope"), "not_found_in_scope")
            cls = view.classification(record)
            if cls == "OWN":
                return view
            if cls in ("SHARED", "CROSS_VISIBLE"):
                raise _SITE_TRUST_SCOPE_GATE.fire(TrustRefused("out_of_scope"), "out_of_scope")
            raise _SITE_TRUST_SCOPE_GATE.fire(TrustRefused("not_found_in_scope"), "not_found_in_scope")

    def _find_edge(self, user_id: str, edge_id: str) -> Edge:
        with _SITE_EDGE_UNKNOWN_TARGET.consult():
            for e in self.store.edges(user_id, active_only=False, include_quarantined=True):
                if e.id == edge_id:
                    return e
            raise _SITE_EDGE_UNKNOWN_TARGET.fire(ValueError(f"no edge {edge_id!r} for user {user_id!r}"))

    def dispute(self, user_id: str, edge_id: str, *, reason: str = "",
                actor: str = "user", principal=None, source_id: Optional[str] = None,
                call_path: Optional[ConfirmationCallPath] = None) -> dict:
        """The user challenges a remembered fact. Non-destructive: the edge is
        invalidated (reason 'disputed') — out of every assertable surface
        immediately, retained as queryable history — and the dispute itself is
        recorded as the user's own episode (kind interaction) with the actor and reason. If the fact
        was actually right, it re-enters the normal way: new evidence via
        `remember()`. Exposed to an agent only under `direct`
        (0031/trust-tools-direct), with the injection residual stated there; an
        agent-callable suppress verb is a prompt-injection target, so a host
        without `direct` wires it to a real user action.

        specs/0031 §4f: `principal`, `source_id` and `call_path` are keyword-only
        and default to absent, and with all three absent the bytes are today's.
        Under a principal the §3b scope gate runs first, inside this transaction
        (`TrustRefused`, writing nothing); the audit episode carries `source_id`
        and the agent `call_path` in provenance, never in its summary.

        specs/0055: `reason` is screened (a credential-shaped span withheld, reported in the result's
        `credentials_withheld`); a shape in `actor` or `source_id` refuses the call (`CredentialRefused`). The audit
        episode's summary quotes the disputed record, so it is masked before it is written (§4c-ii rule 1): a
        legacy credential in the record is never copied into the new row."""
        (reason,), report = self._cred_ingress(user_id, "dispute", ids=(("actor", actor), ("source_id", source_id)),
                                               free=(("reason", reason),))
        derived: dict = {}
        # specs/0041 round 10 (found in sweep A): the record is read, judged and quoted INSIDE one write
        # transaction — a redaction cannot land between the read and the derived episode — and an
        # ATTESTED target is refused before anything is written
        with self.store.atomic():
            self._trust_scope_gate(user_id, principal, kind="edge", record_id=edge_id, writes=True,
                                   source_id=source_id)
            self._refuse_attested(user_id, edge_id, "dispute")
            edge = self._find_edge(user_id, edge_id)
            with _SITE_DISPUTE_INACTIVE.consult():
                if not edge.active:
                    raise _SITE_DISPUTE_INACTIVE.fire(ValueError(f"edge {edge_id!r} is not active (already "
                                     f"{edge.invalidation_reason or 'invalidated'})"))
            today = _today_utc()
            self.store.invalidate_edge(edge_id, utcnow(), "disputed")
            note = f" — {reason}" if reason else ""
            summary, drep = _cred.mask(f"({actor}) disputed the remembered fact "
                                       f"'{edge.relation}: {edge.object}'{note}")
            _cred.merge_report(derived, "summary", drep)
            self.store.add_episode(Episode(
                id=f"ep-{uuid4().hex[:12]}", user_id=user_id, date=today,
                summary=summary,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"dispute:{edge_id}", source_id=source_id,
                                      call_path=_agent_call_path(call_path))))
        self._record("feedback", {"disputed": 1, "confirmed": 0}, user_id)
        self._cred_withheld(user_id, "dispute", report, source="caller")
        self._cred_withheld(user_id, "dispute", derived, source="derived")
        out = {"disputed": edge_id, "relation": edge.relation}
        if report or derived:
            out["credentials_withheld"] = {**report, **derived}
        return out

    def confirm(self, user_id: str, edge_id: str, *,
                date: Optional[str] = None,
                actor: ConfirmationActor = ConfirmationActor.USER,
                call_path: ConfirmationCallPath = ConfirmationCallPath.HOST_API,
                correlation_id: Optional[str] = None, principal=None,
                source_id: Optional[str] = None) -> dict:
        """The user explicitly validates a remembered fact (specs/0008). This is the
        ONLY path that clears `needs_confirmation`; reinforcement no longer does. In
        one atomic store operation it clears the flag, advances liveness
        (`observed_at`) and confidence, writes the confirmation episode, and records
        the mandatory confirmation.

        Only assertable facts can be confirmed: elevating a quarantined claim or a
        third-party inference by 'confirmation' would be a laundering vector — if
        the user affirms a claim, that affirmation is new user-authored evidence and
        belongs in `remember()`.

        `actor` and `call_path` are closed enums (audit metadata; they grant
        nothing — authority is the protected call path, not the label). `confirm()`
        is the host API, and is exposed to an agent only under `direct`
        (0031/trust-tools-direct), with the injection residual stated there: the
        agent tool passes `call_path=mcp_direct` or `adapter_direct`, recorded in
        the confirmations row and in the quoting episode's provenance (a host-API
        call leaves the episode's key absent). `principal` and `source_id` are
        keyword-only and default to absent; under a principal the §3b scope gate
        runs first, inside the confirmation's transaction (`TrustRefused`), and the
        quoting episode carries `source_id`. `correlation_id` (opaque, ≤64
        chars) gives replay protection across an unknown commit outcome; omitted, one
        is generated and there is none to retry against. The return is a mapping:
        `{confirmed, valid_from, confirmed_at, correlation_id, replayed}`."""
        # Closed-enum + charset validation BEFORE any mutation (§6c/C9). A string is
        # accepted only if it names an enum member — a free-form label is rejected,
        # not stored (C2a).
        # specs/0055 §4b: an identifier carrying a credential shape refuses the call before anything else reads it
        self._cred_ingress(user_id, "confirm", ids=(("correlation_id", correlation_id), ("source_id", source_id)))
        actor = ConfirmationActor(actor)
        call_path = ConfirmationCallPath(call_path)
        correlation_id = (validate_correlation_id(correlation_id)
                          if correlation_id is not None
                          else f"auto-{uuid4().hex}")
        # specs/0008 §2a/§6c (INV-Q2), R-A RA-03: NO read of live target state before the store's registry decision —
        # a retry under a held correlation id is replayed, refused as a conflict, or terminal (RequestRedacted)
        # whatever its target, exactly as the store decides it. The target is read only for a NEW request, inside
        # the store; its unknown-edge refusal reaches the caller as the same ValueError this method always raised.
        # The canonical request identity is the CALLER's inputs — never the derived
        # instant — so two date-less retries are the SAME request (§6c). `OMITTED`
        # is a value; `rule_version` guards against a rule change colliding digests.
        caller_date = date if date is not None else "OMITTED"
        # specs/0031 §4f: a binding source is a caller input, so it enters the request identity; absent, the digest
        # input is exactly today's (no new component), so a host retry keeps its digest
        request_digest = hashlib.sha256("\x1f".join(
            [user_id, edge_id, call_path.value, actor.value,
             CONFIRMATION_RULE_VERSION, caller_date]
            + ([f"source_id={source_id}"] if source_id is not None else [])).encode()).hexdigest()
        when = _event_dt(date or _today_utc())
        _scope_kw = {} if (source_id is None and _agent_call_path(call_path) is None) else {
            "episode_source_id": source_id, "episode_call_path": _agent_call_path(call_path)}
        try:
            # specs/0031 §4f §3b: under a principal the scope gate runs inside the confirmation's own transaction,
            # before the registry decision writes anything. With no principal no transaction is opened here, and
            # the call is today's: INV-Q2's registry-first order, the store's own transaction
            with (self.store.atomic() if principal is not None else contextlib.nullcontext()):
                self._trust_scope_gate(user_id, principal, kind="edge", record_id=edge_id, writes=True,
                                       source_id=source_id)
                conf = self.store.confirm_edge(
                    user_id, edge_id, actor=actor, call_path=call_path,
                    correlation_id=correlation_id, request_digest=request_digest,
                    confirmed_at=when, **_scope_kw)
        except UnknownEdge as e:
            with _SITE_CONFIRM_UNKNOWN_TARGET.consult():
                raise _SITE_CONFIRM_UNKNOWN_TARGET.fire(ValueError(f"no edge {edge_id!r} for user {user_id!r}")) from e
        if not conf.replayed:
            self._record("feedback", {"disputed": 0, "confirmed": 1}, user_id)
        # `valid_from` is first-known and immutable, so reading it back is stable on
        # replay; `confirmed_at` comes from the RECORD (the stored instant on replay,
        # never a fresh one). M2 (0.4.5): the return names the confirmation instant
        # and the edge's first-known separately, each meaning what it says.
        edge = self._find_edge(user_id, edge_id)
        return {"confirmed": edge_id,
                "valid_from": edge.valid_from.date().isoformat(),
                "confirmed_at": conf.confirmed_at.date().isoformat(),
                "correlation_id": conf.correlation_id,
                "replayed": conf.replayed}

    def undo_restoration(self, user_id: str, edge_id: str, *,
                         correlation_id: Optional[str] = None) -> dict:
        """Reverse ONE value the data migration restored (specs/0044 §4i), HOST API only — never model-reachable,
        no CLI verb. The edge is retired again with its recorded retirement, field by field (`invalidated_at`, its
        instant normalized as at every retirement, and `invalidation_reason`); every other field is untouched.

        `correlation_id` (≤64 chars of `[A-Za-z0-9._:-]`) is an idempotency key in the SAME per-user id space as
        `confirm()`'s: an id held by another verb is refused naming it, and a retry under the id replays the
        recorded result without reading the edge. Omitted, one is generated (`auto-<hex>`), takes a registry row
        and is returned — there is nothing to retry against. A retry under an id whose edge was later redacted
        raises `RequestRedacted`.

        Returns `{undone, undone_at, correlation_id, replayed, already_undone}`. A replay is always
        `replayed=True, already_undone=False` (it reconstructs a call that wrote); a call on a row already undone
        returns `already_undone=True` with the recorded `undone_at`, writes nothing and holds no id. Refusals raise
        `UndoRefused` with a closed `reason`: `no-outcome`, `not-restored` (withheld under revocation),
        `testimony` (an imported outcome: this store did not restore it), `not-applicable` (the restoration
        ended: a later retirement, redaction or erasure), `edge-unavailable`, `ambiguous-outcome`.

        specs/0055 §4b: a credential-shaped `correlation_id` refuses the call (`CredentialRefused`)."""
        self._cred_ingress(user_id, "undo_restoration", ids=(("correlation_id", correlation_id),))
        correlation_id = (validate_correlation_id(correlation_id)
                          if correlation_id is not None
                          else f"auto-{uuid4().hex}")
        return self.store.undo_restoration(user_id, edge_id, correlation_id=correlation_id)

    def reply(self, user_id: str, edge_id: str, *, kind: str, text: Optional[str] = None,
              target: Optional[str] = None, actor: ReplyActor = ReplyActor.USER,
              correlation_id: Optional[str] = None) -> dict:
        """The subject's RIGHT OF REPLY to a remembered fact (specs/0047): the record stands, and the reply travels
        with it. HOST API only — never an MCP tool, never the extractor or the assistant (INV-R10).

        `kind` is closed: `challenge` ("that's wrong"), `context`, `withdrawn-consent`, or `resolve`, which withdraws
        ONE challenge of the same fact, named by its reply id in `target`. A `resolve` carries no `text`; every other
        kind carries non-empty text and no target. A reply changes nothing about the fact itself (INV-R1): it does not
        retire, supersede, edit or delete it, and it is never ingested as evidence. Replies are append-only: a
        challenge is withdrawn by a resolve, never by an edit. While a challenge is open, `confirm()` refuses the fact
        (INV-R13), and a prior carrying a reply or a confirmation is never absorbed into a later, more specific
        restatement (§4e).

        `actor` is `user` or `host` (the host acting on the user's behalf); it is an unauthenticated LABEL until
        authenticated principals exist. A resolve needs the same user and the same fact as its challenge, and its
        actor may differ from the challenge's: each row records its own (the owner's reading of §4b, 2026-10-19).

        `correlation_id` (≤64 chars of `[A-Za-z0-9._:-]`) is an idempotency key in the SAME per-user id space as
        `confirm()`'s and `undo_restoration()`'s: an id held by another verb is refused naming it; a retry of the
        same request replays the recorded reply without reading the fact; after the fact's redaction a retry raises
        `RequestRedacted`. The request's identity is `(user, fact, kind, target, text)` — `actor` is outside it, so a
        retry under another actor label replays (confirm's identity includes its actor; this one does not). Omitted,
        one is generated, takes a registry row and is returned.

        Returns `{reply_id, edge_id, kind, target, written_at, correlation_id, replayed}`. Refusals raise
        `ReplyRefused` (`veracium.store.base`) with a closed `reason`: `kind`, `actor`, `shape` (a target or text where
        the kind forbids it, empty text, or text that is not valid UTF-8), `marker` (the redaction marker in the
        text), `unknown-edge`, `redacted-edge`, `procedural-edge`, `resolve-target`, `resolve-repeat`.

        While a challenge is open, the fact — and any same-value restatement of it — is withheld from every assertion
        surface (recall, contested groups, proactive, as-of, the wiki) and counted there; `Recall.inspection`,
        `AsOfFact.inspection`, `why` and `introspect` carry the challenge. Only a `resolve` ends it (specs/0047 §4c–§4d).

        specs/0055 §4b: `text` is screened BEFORE the request digest is computed (a credential-shaped span withheld,
        reported in `credentials_withheld`); a shape in `target` or `correlation_id` refuses the call
        (`CredentialRefused`). The request identity is over the screened text."""
        (text,), report = self._cred_ingress(user_id, "reply",
                                             ids=(("target", target), ("correlation_id", correlation_id)),
                                             free=(("text", text),))
        correlation_id = (validate_correlation_id(correlation_id)
                          if correlation_id is not None
                          else f"auto-{uuid4().hex}")
        r = self.store.add_reply(user_id, edge_id, kind=kind, text=text, target=target, actor=actor,
                                 correlation_id=correlation_id)
        if not r.replayed:
            # one content-free audit line per new reply: the closed kind only — never text, target or the fact
            # (research's T10a F6). Telemetry's closed event schema (0015) has no `reply` event and drops it.
            self._record("reply", {"kind": r.kind}, user_id)
            self._cred_withheld(user_id, "reply", report, source="caller")
        out = {"reply_id": r.id, "edge_id": r.edge_id, "kind": r.kind, "target": r.target,
               "written_at": r.written_at.isoformat(), "correlation_id": r.correlation_id, "replayed": r.replayed}
        if report:
            out["credentials_withheld"] = report
        return out

    # -- outcome tracking (engine-written; never MCP) ------------------------
    _OUTCOME_ACTORS = {"user": EvidenceAuthor.USER, "system": EvidenceAuthor.SYSTEM}

    def record_outcome(self, user_id: str, edge_id: str, *, outcome,
                       evidence_ref: str, actor: str = "system",
                       corrected_value: Optional[str] = None,
                       date: Optional[str] = None,
                       context_ref: Optional[str] = None) -> dict:
        """Record that a conclusion built on `edge_id` was used / judged.

        Writes (or upgrades) a `kind="outcome"` episode — the source of truth —
        and maintains the edge's derived counters. The upgrade path is keyed by
        (`edge_id`, `evidence_ref`): a use recorded UNREVIEWED is upgraded in
        place when a judgment arrives for the same use.

        DELIBERATELY NEVER supersedes the fact (the platform's edge-blind
        clarification): one run's evidence_ref touches every fact it consulted,
        so upgrading a *use* to `corrected` must not invalidate supporting
        facts — `corrected_value` here is recorded as the decision's true value
        only. Fact-level correction is the explicit `correct()` verb.
        `challenged` sets the existing needs-confirmation flag; nothing else
        touches gate placement — counters are information, not gating.

        specs/0055 §4b: `corrected_value` is free text written only into the outcome episode's summary, so a
        credential-shaped span is withheld (reported in `credentials_withheld`); a shape in `evidence_ref` or
        `context_ref` refuses the call (`CredentialRefused`). The summary quotes the judged record, so it is masked
        before it is written (§4c-ii rule 1)."""
        (corrected_value,), report = self._cred_ingress(
            user_id, "record_outcome", ids=(("evidence_ref", evidence_ref), ("context_ref", context_ref)),
            free=(("corrected_value", corrected_value),))
        derived: dict = {}
        from .schema import Outcome
        outcome = Outcome(outcome)
        author = self._OUTCOME_ACTORS.get(actor)
        with _SITE_OUTCOME_ACTOR.consult():
            if author is None:
                raise _SITE_OUTCOME_ACTOR.fire(ValueError(f"actor must be 'user' or 'system', not {actor!r}"))
        with _SITE_OUTCOME_HUMAN.consult():
            if outcome in (Outcome.CONFIRMED, Outcome.CORRECTED) and actor != "user":
                raise _SITE_OUTCOME_HUMAN.fire(ValueError(f"{outcome.value} is a human judgment (actor='user')"))
        with _SITE_OUTCOME_SYSTEM.consult():
            if outcome in (Outcome.CHALLENGED, Outcome.CONCURRED) and actor != "system":
                raise _SITE_OUTCOME_SYSTEM.fire(ValueError(f"{outcome.value} is a system judgment (actor='system')"))
        # specs/0041 round 10 (found in sweep A): the record is read, judged and quoted INSIDE one write
        # transaction — a redaction cannot land between the read and the derived episode — and an
        # ATTESTED target is refused before anything is written
        with self.store.atomic():
            self._refuse_attested(user_id, edge_id, "record_outcome")
            edge = self._find_edge(user_id, edge_id)
            date = _event_dt(date or _today_utc()).date().isoformat()

            # specs/0009: NEVER mutate a prior judgment — append a new chain link.
            # The head is the max-`seq` outcome episode for (edge_id, evidence_ref);
            # `append_outcome_if_head` CAS-appends and retries if the head moved. The
            # `[prior judgment was …]` note is rebuilt against the WINNING head, and
            # `upgraded` reflects the successful attempt (H11, round-5 Correction A).
            val = f" (true value: {corrected_value})" if corrected_value else ""
            while True:
                head = self._outcome_head(user_id, edge_id, evidence_ref)
                summary = (f"({actor}) {outcome.value}: use of "
                           f"'{edge.relation}: {edge.object}'{val}")
                if head is not None:
                    was = head.provenance.author_of_evidence
                    if was != author:
                        summary += f" [prior judgment was {was.value}-authored]"
                summary, drep = _cred.mask(summary)
                derived = _cred.merge_report({}, "summary", drep)
                draft = OutcomeJudgmentDraft(
                    author=author, event_timestamp=date, outcome=outcome,
                    summary=summary, context_ref=context_ref)
                appended = self.store.append_outcome_if_head(
                    user_id, edge_id, evidence_ref,
                    head.id if head is not None else None, draft)
                if appended is not HEAD_MOVED:
                    break                                    # committed
            upgraded = head is not None                      # revised an existing chain

            # Counters are DERIVED from chain heads (H6), recomputed rather than
            # mutated in place — the denormalisation the M4 defect was.
            times_used, counts = self._edge_outcome_aggregates(user_id, edge_id)
            edge.times_used = times_used
            edge.outcome_counts = counts
            # last_outcome / last_outcome_at are DEPRECATED (Option A) — best-effort,
            # no cross-chain guarantee.
            edge.last_outcome = outcome
            edge.last_outcome_at = _event_dt(date)
            if outcome is Outcome.CHALLENGED:
                edge.needs_confirmation = True   # "confirm before relying" — existing surface
            self.store.add_edge(edge)
        self._record("outcome", {"new": 0 if upgraded else 1,
                                 "upgraded": 1 if upgraded else 0}, user_id)
        self._cred_withheld(user_id, "record_outcome", report, source="caller")
        self._cred_withheld(user_id, "record_outcome", derived, source="derived")
        out = {"edge_id": edge_id, "outcome": outcome.value, "upgraded": upgraded,
               "times_used": times_used}
        if report or derived:
            out["credentials_withheld"] = {**report, **derived}
        return out

    def _outcome_head(self, user_id: str, edge_id: str, evidence_ref: str):
        """The head (max-`seq`) of the `(edge_id, evidence_ref)` outcome chain, or
        None — derived, never materialised (specs/0009 H-Q2)."""
        head = None
        for ep in self.store.episodes(user_id):
            if (ep.kind == "outcome" and ep.edge_id == edge_id
                    and ep.provenance.evidence_ref == evidence_ref):
                if head is None or (ep.seq or 0) > (head.seq or 0):
                    head = ep
        return head

    def _edge_outcome_aggregates(self, user_id: str, edge_id: str):
        """`(times_used, outcome_counts)` for an edge, DERIVED from chain heads
        (specs/0009 H6): one chain per `(edge_id, evidence_ref)` use, its head the
        max-`seq` link. `times_used` = distinct chains; `outcome_counts` = the head
        outcome of each chain. A five-judgment chain about one use is still one use."""
        heads: dict = {}
        for ep in self.store.episodes(user_id):
            if ep.kind == "outcome" and ep.edge_id == edge_id:
                key = ep.provenance.evidence_ref
                cur = heads.get(key)
                if cur is None or (ep.seq or 0) > (cur.seq or 0):
                    heads[key] = ep
        counts: dict = {}
        for ep in heads.values():
            if ep.outcome is not None:
                counts[ep.outcome.value] = counts.get(ep.outcome.value, 0) + 1
        return len(heads), counts

    def correct(self, user_id: str, edge_id: str, corrected_value: str, *,
                actor: str = "user", evidence_ref: Optional[str] = None,
                date: Optional[str] = None, principal=None, source_id: Optional[str] = None,
                call_path: Optional[ConfirmationCallPath] = None) -> dict:
        """Explicit FACT-level correction: the remembered value itself was wrong.
        Supersedes the edge with `invalidation_reason="corrected"` (distinguishable
        at recall from natural change) and records the corrected value as a new
        user-authored assertable edge. This — and only this — invalidates a fact;
        `record_outcome(outcome="corrected")` judges a *decision* and never
        touches the facts it consulted. Exposed to an agent only under `direct`
        (0031/trust-tools-direct), with the injection residual stated there.

        specs/0011 §4e (E5): the correction reaches storage only through the
        atomic plan machinery with a `CorrectionAuthorisation` verified inside
        the transaction — an integrity binding, NOT authentication: `actor` is
        a caller-supplied principal and this is a PROTECTED HOST API; the host
        authenticates the principal and establishes intent before calling, and
        never exposes this on a surface a model can reach with a caller-chosen
        principal (the agent tool fixes `actor` to the user, 0031 §4f). §4b
        applies to corrections: a bare self-assertion cannot retire an
        OTHER-subject prior — that raises `graph.CorrectionRefused` after the
        durable refusal row commits.

        specs/0031 §4f: `principal`, `source_id` and `call_path` are keyword-only
        and default to absent, and with all three absent the bytes are today's.
        Under a principal the §3b scope gate runs first, inside this transaction
        (`TrustRefused`, writing nothing). The replacement edge carries
        `source_id`; the audit episode carries `source_id` and the agent
        `call_path`, in provenance.

        specs/0055: `corrected_value` becomes the edge's object verbatim, so it is an IDENTIFIER: a credential shape
        refuses the call (`CredentialRefused`), as one in `actor`, `evidence_ref` or `source_id` does. The
        replacement copies the prior's `subject` and `relation` (its identity, which supersession joins on): if
        either carries a shape the correction is refused (§4c-ii row 8), and 0041 redaction is the remedy. The
        copied `note` is masked BEFORE `graph.plan_correction`, so the plan, its `raw_request` and every
        supersession digest see the masked note (§4c-ii rule 1); the audit episode's summary is masked too."""
        self._cred_ingress(user_id, "correct", ids=(("corrected_value", corrected_value), ("actor", actor),
                                                    ("evidence_ref", evidence_ref), ("source_id", source_id)))
        derived: dict = {}
        from . import authority, graph
        from .schema import CorrectionAuthorisation, correction_digest
        from .store.base import PLAN_STALE
        date = date or _today_utc()
        when = _event_dt(date)
        date = when.date().isoformat()          # normalise once, as confirm()
        # specs/0011 §4e (E5, closes M7-correct): storage is reached ONLY
        # through the atomic plan machinery, with a CorrectionAuthorisation
        # bound to (store origin, prior id, replacement digest, kind,
        # principal) and verified INSIDE the transaction. The CAS retry loop
        # is apply_supersession's own shape: PlanStale → re-read, recompute.
        # specs/0041 round 10 (found in sweep A): the record is read, judged and quoted INSIDE one write
        # transaction — a redaction cannot land between the read and the derived episode — and an
        # ATTESTED target is refused before anything is written
        with self.store.atomic():
            self._trust_scope_gate(user_id, principal, kind="edge", record_id=edge_id, writes=True,
                                   source_id=source_id)
            self._refuse_attested(user_id, edge_id, "correct")
            for _ in range(graph._MAX_PLAN_ATTEMPTS):
                edge = self._find_edge(user_id, edge_id)
                with _SITE_CORRECT_INACTIVE.consult():
                    if not edge.active:
                        raise _SITE_CORRECT_INACTIVE.fire(ValueError(f"edge {edge_id!r} is not active (already "
                                         f"{edge.invalidation_reason or 'invalidated'})"))
                # specs/0026 §3b at the THIRD establishment boundary
                # (research's implementation red-team: correct() preserved
                # the note at default-MENTIONABLE with no floor and no
                # record, reopening B02/B07 for corrected facts): the
                # corrected edge's preserved note + new value pass through
                # the SAME restrict-only floor and the ONE derivation site
                # as ingest and import — a correction updates the VALUE,
                # never launders the relay out of the note
                from . import agreement as _agreement
                # specs/0037 v19 (V-NO-CORRECTION-OF-PROCEDURES; research's red team): a
                # correction mints a successor whose OBJECT is the host's text, so
                # inheriting the stamp would attribute that text to the user, and
                # dropping it rendered the record. Neither is honest: a procedural
                # record is not corrected — it is retired and restated through the
                # producer that can attest it (record_procedure, or the user again).
                with _SITE_CORRECT_PROCEDURAL.consult():
                    if is_procedural(edge):
                        from .procedures import ProcedureValueError
                        raise _SITE_CORRECT_PROCEDURAL.fire(ProcedureValueError(
                            "correction_of_procedure",
                            f"edge {edge_id!r} is a procedural record; correct() does not mint a successor for one "
                            "(specs/0037 §4a-iii, V-NO-CORRECTION-OF-PROCEDURES) — retire it and restate the procedure"))
                # specs/0055 §4c-ii row 8: the prior's identity is copied unchanged, so a shaped one refuses;
                # the copied note is free text and is masked here, before plan_correction hashes the plan
                self._refuse_shaped_identity(user_id, edge)
                copied_note, nrep = _cred.mask(edge.note) if edge.note else (edge.note, {})
                derived = _cred.merge_report({}, "note", nrep)
                _disc = Disclosure.MENTIONABLE
                # the relay reads the raw note: its output is a closed vocabulary of markers, never a carrier
                if _agreement.relay_markers(edge.note, corrected_value):
                    _disc = Disclosure.USE_ONLY
                new = Edge(
                    id=f"e-{uuid4().hex[:12]}", user_id=user_id, subject=edge.subject,
                    relation=edge.relation, object=corrected_value, note=copied_note,
                    volatility=edge.volatility, valid_from=when,
                    agreement=_agreement.derive_record(
                        edge.note, corrected_value, _disc,
                        relation=edge.relation),
                    provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                          evidence_ref=evidence_ref or f"correct:{edge_id}",
                                          disclosure=_disc,
                                          observed_at=when, source_id=source_id))
                plan, refused = graph.plan_correction(
                    self.store, edge, new, op_id=f"corr-{new.id}")
                auth = None if refused else CorrectionAuthorisation(
                    origin=self.store.local_origin(), prior_edge_id=edge_id,
                    replacement_digest=correction_digest(corrected_value),
                    kind="corrected", principal=actor)
                result = self.store.apply_supersession_plan(
                    plan, authorisation=auth, acting_principal=actor)
                if result is not PLAN_STALE:
                    break
            else:
                raise RuntimeError(
                    f"correction of {edge_id!r} kept returning PlanStale after "
                    f"{graph._MAX_PLAN_ATTEMPTS} attempts (specs/0003 §4f)")
            if not refused:
                summary, srep = _cred.mask(f"({actor}) corrected '{edge.relation}: {edge.object}' "
                                           f"to '{corrected_value}'")
                _cred.merge_report(derived, "summary", srep)
                self.store.add_episode(Episode(
                    id=f"ep-{uuid4().hex[:12]}", user_id=user_id, date=date,
                    summary=summary,
                    provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                          evidence_ref=evidence_ref or f"correct:{edge_id}",
                                          observed_at=when, source_id=source_id,
                                          call_path=_agent_call_path(call_path))))
        # the refusal is raised AFTER the atomic scope: raised inside it, the scope would roll back the durable
        # refusal row the plan just wrote — and specs/0011 §4b requires that row to commit
        with _SITE_CORRECT_REFUSED.consult():
            if refused:
                # the durable refusal row committed with the plan; the correction
                # itself is loud (specs/0011 §4b applies to corrections)
                raise _SITE_CORRECT_REFUSED.fire(graph.CorrectionRefused(edge_id, authority.RULE_VERSION))
        self._record("feedback", {"disputed": 0, "confirmed": 0, "corrected": 1}, user_id)
        self._cred_withheld(user_id, "correct", derived, source="derived")
        out = {"corrected": edge_id, "replacement": new.id}
        if derived:
            out["credentials_withheld"] = derived
        return out

    # -- compliance erasure --------------------------------------------------
    def forget(self, user_id: str) -> dict:
        """Irreversibly erase everything stored for `user_id`: all edges
        (superseded history and quarantined claims included), all episodes,
        the wiki cache, and counters, with the user's confirmations, replies and source revocations. Returns
        {"edges": n, "episodes": n, "confirmations": n, "replies": n}.

        This is the data-subject right ("right to be forgotten"), deliberately
        distinct from lifecycle: `maintain()` never deletes, `forget()` never
        preserves. There is no undo — export first (`export_memory`) if a
        recoverable copy is wanted. Confirmation is the host's responsibility."""
        r = self.store.forget_user(user_id)
        return self._after_forget(user_id, r)

    def _after_forget(self, user_id: str, r: dict) -> dict:
        """The post-store steps of an erase, run after its commit (today's order; specs/0031 §4e step 5 keeps it)."""
        # specs/0017 §4d transition 5: delete the user's accumulator entry AND
        # cancel every active registry entry for the user — ONE critical
        # section, so a concurrent terminal merge either completed before us
        # (we delete what it merged) or observes cancelled and discards.
        with self._usage_lock:
            self._llm_usage.pop(user_id, None)
            for entry in self._usage_registry.values():
                if entry["user_id"] == user_id:
                    entry["cancelled"] = True
        self._record("forget", {"edges": r["edges"], "episodes": r["episodes"]}, user_id)
        return r

    def forget_everything_preview(self, user_id: str, *, issuer, principal=None) -> dict:
        """specs/0031 §4f §4e, the FIRST of the whole-user erase's two steps (the agent tool
        `forget_everything_preview`; a host may call it too). Writes nothing. In ONE read snapshot it reads the user's
        keys in the four tables the preview shows (edges, episodes, confirmations, replies); the counts are those
        lists' lengths and the digest binds the same lists (INV-TT20). Returns `{counts, expires_at, preview_token,
        warning}`: counts only, never row content (INV-TT10).

        `issuer` is a `trust_tools.PreviewTokenIssuer`, passed EXPLICITLY — there is no process-global default — and
        its context must be this store and this user. Any `principal` is refused as `principal_scoped`: an erase is
        user-wide and a principal sees only its scope (§3b). Raises `trust_tools.TrustRefused`."""
        from . import trust_tools as _tt
        with _SITE_TRUST_ERASE_PREVIEW.consult():
            if principal is not None:
                raise _SITE_TRUST_ERASE_PREVIEW.fire(_tt.TrustRefused("principal_scoped"), "principal_scoped")
        with _SITE_TRUST_ERASE_PREVIEW_CONTEXT.consult():
            if (issuer.store_identity, issuer.user_id) != (self.store.local_origin(), user_id):
                raise _SITE_TRUST_ERASE_PREVIEW_CONTEXT.fire(_tt.TrustRefused("preview_unknown"), "issuer-context")
        keys = self.store.erase_preview_snapshot(user_id)
        t = issuer.now()
        return {"counts": {tbl: len(keys[tbl]) for tbl in _tt.ERASE_PREVIEW_TABLES},
                "expires_at": _tt.expires_at(t),
                "preview_token": issuer.issue(_tt.snapshot_digest(user_id, keys), t),
                "warning": _tt.ERASE_WARNING}

    def forget_everything_confirm(self, user_id: str, preview_token, *, issuer, principal=None) -> dict:
        """specs/0031 §4f §4e, the SECOND step: verify the preview's token and erase. The token is parsed strictly,
        checked against the issuer's context (this store and user) and its MAC, then its time (valid iff
        t <= now < t + 600); `forget_user` then re-derives the four tables' digest INSIDE its own write transaction
        and erases only if it equals the token's, rolling the whole erase back on any failure (INV-TT9). Refusals
        raise `trust_tools.TrustRefused` (`principal_scoped`, `preview_unknown`, `preview_expired`, `store_changed`)
        with nothing erased, and each is counted on the operator's discard counter, by reason, through `_record`,
        with no content. Replay is key-set equality, not one use (TT-R2-04). Returns `forget`'s counts."""
        from . import trust_tools as _tt
        try:
            with _SITE_TRUST_ERASE_CONFIRM.consult():
                if principal is not None:
                    raise _SITE_TRUST_ERASE_CONFIRM.fire(_tt.TrustRefused("principal_scoped"), "principal_scoped")
            digest = issuer.verify(preview_token, store_identity=self.store.local_origin(), user_id=user_id)
            r = self.store.forget_user(user_id, expected_digest=digest)
        except _tt.TrustRefused as refusal:
            self._record("erase_refused", {"reason": refusal.reason}, user_id)
            raise
        return self._after_forget(user_id, r)

    # -- specs/0022 §4g: source revocation, the HOST API (library only: no CLI verb, no MCP tool — R14) ---------------
    def revoke_source(self, user_id: str, origin: Optional[str], source_id: str, reason: str, *,
                      dry_run: bool = False) -> dict:
        """Revoke a source this host no longer trusts, for one user (specs/0022). Every record that came from it is
        retired or recomputed from the evidence that survives it; nothing is deleted, and `unrevoke_source` reverses
        it by the same computation. `origin=None` means THIS store's own records (0006 §4 rule 6); pass a foreign
        origin as it is stored on an imported record. `reason` is one of
        `redaction.SOURCE_REVOCATION_REASONS`. Returns the completeness statement (§4c: the records affected, by
        completeness class, and whether the sweep was `complete`); `dry_run=True` returns the identical statement
        and writes nothing (§4e). A record with no `source_id` has no source identity and is not revocable by
        source. Not exposed over MCP or the CLI: a revocation is a trust decision, and a surface the model can
        reach is one it can be talked into (§3b)."""
        return self._source_revocation(user_id, origin, source_id, reason, "revoke", dry_run)

    def unrevoke_source(self, user_id: str, origin: Optional[str], source_id: str, reason: str, *,
                        dry_run: bool = False) -> dict:
        """Lift a revocation (specs/0022 §4f): appends a lifting row and recomputes every affected record's state from
        the new standing set, so a record another standing revocation still condemns stays retired. `reason` is one
        of `redaction.SOURCE_LIFT_REASONS`. Returns the completeness statement; `dry_run=True` writes nothing."""
        return self._source_revocation(user_id, origin, source_id, reason, "lift", dry_run)

    def source_revocations(self, user_id: str) -> dict:
        """The operator's audit view of one user's revocations (specs/0022 §4g): `standing`, the identity digests
        revoked now (latest action per digest, by append order alone, §4a), and `history`, every revoke and lift
        row in append order (`seq`, `identity_digest`, `action`, `at`, `reason`)."""
        from .store import revocation as _rv
        if not isinstance(self.store, SqliteStore):
            raise NotImplementedError(f"{type(self.store).__name__} does not support source revocation "
                                      f"(specs/0022 is implemented by SqliteStore)")
        history = _rv.revocation_history(self.store, user_id)
        return {"standing": sorted(self.store.standing_revocations(user_id)), "history": history}

    def _d3_legacy_source_or_refuse(self, user_id: str, origin, source_id, op: str) -> None:
        """specs/0055 §4b-ii D3. When `origin` or `source_id` carries a credential shape, look for a stored edge or
        episode OF THIS USER whose provenance carries exactly that `source_id` under the RESOLVED origin (the same
        pair the digest frames). None: `CredentialRefused`. One: return, and the call proceeds (legacy resolution;
        the identity digest is the declared exception). The lookup writes, logs and echoes nothing; it is an
        existence oracle, acceptable because revocation is host-only (no MCP tool or adapter reaches it)."""
        shaped = [(f, _cred.first_class(v)) for f, v in (("origin", origin), ("source_id", source_id))
                  if isinstance(v, str) and v]
        shaped = [(f, c) for f, c in shaped if c is not None]
        if not shaped:
            return
        local = self.store.local_origin()
        want = (origin if origin is not None else local, source_id)

        def _matches(prov) -> bool:
            return (prov is not None and prov.source_id is not None
                    and (prov.origin if prov.origin is not None else local, prov.source_id) == want)
        for e in self.store.edges(user_id, active_only=False):
            if _matches(e.provenance):
                return
        for ep in self.store.episodes(user_id):
            if _matches(ep.provenance):
                return
        field_name, cls = shaped[0]
        raise self._cred_refused(user_id, op, field_name, cls)

    def _source_revocation(self, user_id: str, origin: Optional[str], source_id: str, reason: str,
                           action: str, dry_run: bool) -> dict:
        from .store import revocation as _rv
        from .store.revocation_sweep import KIND_SYNTHESIZED, digest_of
        if not isinstance(self.store, SqliteStore):
            raise NotImplementedError(f"{type(self.store).__name__} does not support source revocation "
                                      f"(specs/0022 is implemented by SqliteStore)")
        if not isinstance(dry_run, bool):
            raise TypeError(f"dry_run must be a bool, got {type(dry_run).__name__}")
        # specs/0055 §4b-ii D3, BEFORE the reason check and before any digest: a credential-shaped origin or
        # source_id is either a legacy source this user's records already carry (revocation must stay possible:
        # proceed, under the declared digest exception) or new text (refused, nothing digested)
        self._d3_legacy_source_or_refuse(user_id, origin, source_id,
                                         "unrevoke_source" if action == "lift" else "revoke_source")
        _rv.check_reason(action, reason)        # specs/0055 D3: the reason, too, before the digest
        digest = digest_of(origin, source_id, self.store.local_origin())
        if digest is None:
            raise ValueError("source_id is required: a record with no source_id has no source identity and is not "
                             "revocable by source (specs/0006's absence rule, specs/0022 §4g)")
        statement = _rv.revoke_source(self.store, user_id, digest, action, reason, _rv._iso_z(utcnow()),
                                      dry_run=dry_run)
        if not dry_run:
            # specs/0022 §7a / Q6: ONE audit event per revocation and per lift — the durable record of the statement.
            # Content-free by construction: the digest, the action, the class counts, `complete`, and the effect
            # counts with the synthesized retirements split out (§4c); never a record id, a reason or any text.
            retired = [e for e in statement["effects"] if e["verb"] == "retire"]
            self._record("unrevoke_source" if action == "lift" else "revoke_source", {
                "identity_digest": digest,
                "action": action,
                "complete": statement["complete"],
                **{k.replace("-", "_"): v for k, v in statement["counts"].items()},
                "retired": len(retired),
                "retired_synthesized": sum(1 for e in retired
                                           if statement["kinds"].get(f"{e['type']}:{e['id']}") == KIND_SYNTHESIZED),
                "recomputed": sum(1 for e in statement["effects"] if e["verb"] == "recompute"),
                "reinstated": sum(1 for e in statement["effects"] if e["verb"] == "reinstate"),
            }, user_id)
        return statement

    # -- specs/0041 §4a: targeted redaction (tranche 3) -----------------------
    def redact(self, user_id: str, *, edge_id: Optional[str] = None, episode_id: Optional[str] = None,
               reason: str, principal=None):
        """Remove one record's CONTENT while keeping its structure (specs/0041): every carrier in the
        treatment map is replaced by the marker, cleared, or deleted in ONE store transaction; the journal
        is tombstoned and a `redacted` event appended; a redaction record ATTESTS the fields, and an ordinary
        write may not repopulate them (INV-11). Exactly one of `edge_id` / `episode_id`; `reason` is one of
        `redaction.ORIGINATING_REASONS` (a closed vocabulary — the reason is not a content channel, INV-6;
        `imported_notice` is refused: only an imported notice writes it, specs/0041 §11.2).
        Idempotent by content: a second call returns the original receipt with `repeated=True`. Returns a
        `RedactionReceipt`, which never carries a content digest and names the derived records that may
        still carry the content (F6) and the receipt domains it cannot vouch for (§4f). Not a deletion and
        not an entitlement operation (§4d): use `forget` for erasure.

        specs/0031 §4f §4d: `principal` is keyword-only and defaults to absent, and with it absent this is today's
        call and today's receipt, `surviving_derived` whole. Under a principal the §3b scope gate runs first, in the
        redaction's own transaction (`TrustRefused`, writing nothing), and the result is the PRINCIPAL-FACING
        PROJECTION (`principal_receipt`), computed by the same view in the same transaction. A repeat passes the
        same fresh gate as a first call (TT-R2-01)."""
        if principal is None:
            r = self.store.redact(user_id, edge_id=edge_id, episode_id=episode_id, reason=reason)
            self._record("redact", {"kind": r.redacted_kind, "fields": len(r.fields_cleared), "repeated": r.repeated}, user_id)
            return r
        if (edge_id is None) == (episode_id is None):
            # the store's own refusal, raised before the gate reads anything: there is no single target to scope
            return self.store.redact(user_id, edge_id=edge_id, episode_id=episode_id, reason=reason)
        kind, rid = ("edge", edge_id) if edge_id is not None else ("episode", episode_id)
        with self.store.atomic():
            view = self._trust_scope_gate(user_id, principal, kind=kind, record_id=rid, writes=False)
            r = self.store.redact(user_id, edge_id=edge_id, episode_id=episode_id, reason=reason)
            projection = self._principal_receipt(user_id, view, r)
        self._record("redact", {"kind": r.redacted_kind, "fields": len(r.fields_cleared), "repeated": r.repeated}, user_id)
        return projection

    #: specs/0031 §4f §4d (TT-R2-01): the ONLY receipt fields a principal is shown. DEFAULT-DENY: a field added to the
    #: host receipt later is omitted unless this tuple names it.
    PRINCIPAL_RECEIPT_FIELDS = ("redacted_kind", "target_id", "reason", "marker_version", "repeated", "recorded_at")

    def _principal_receipt(self, user_id: str, view, receipt) -> dict:
        """specs/0031 §4f §4d: the principal-facing projection of a `RedactionReceipt`. The six named fields, exactly;
        `surviving_derived` filtered to the entries whose record THIS view classes `OWN`, `SHARED` or `CROSS_VISIBLE`,
        each with its class; and the unconditional label `scope: "this principal's view"`, so the list is never
        presented as complete. No hidden count, no hidden id, no conditional "hidden records exist" indicator.
        `fields_cleared` is omitted: it names side-table carriers only when they were treated, so a hidden descendant
        changes it (round 2's witness)."""
        whole = receipt.model_dump(mode="json")
        out = {k: whole[k] for k in self.PRINCIPAL_RECEIPT_FIELDS}
        listed = []
        with _SITE_TRUST_RECEIPT_FILTER.consult():
            for entry in receipt.surviving_derived:
                record = self._trust_target(user_id, entry.get("kind"), entry.get("id"))
                if record is None:
                    continue
                cls = view.classification(record)
                if cls in ("OWN", "SHARED", "CROSS_VISIBLE"):
                    listed.append({**entry, "class": cls})
            out["surviving_derived"] = listed
            out["scope"] = "this principal's view"
            # the withheld entries are not visible in the value, so the decline is stated: fewer listed than held
            return _SITE_TRUST_RECEIPT_FILTER.fire(out, "withhold",
                                                   declined=len(listed) < len(receipt.surviving_derived))

    def pending_notices(self, user_id: str) -> list:
        """specs/0041 §11.6.6 (T4): the user's PENDING redaction notices — another store's testimony that it redacted a
        record THIS store holds, recorded by an import and never applied on the file's word. Each is
        `{notice_id, target_kind, target_id, reason, origin, source_user, recorded_at}`, oldest first; `reason` is
        why it waits (`held-target`, `record-not-in-file`, `standing-arrival`). The claimed source is UNAUTHENTICATED
        testimony (0006 Q4). Read-only; `confirm_notice` applies one."""
        return self.store.pending_notices(user_id)

    def confirm_notice(self, user_id: str, notice_id: str):
        """specs/0041 §11.6.6 (T4): the user confirms a PENDING notice (from `pending_notices`), and it is applied as a
        redaction BY THIS STORE — total over the record's carriers, exactly as `redact` is, the notice's own body kept.
        The only way a notice from an untrusted import changes held content. Returns a `RedactionReceipt`; an already
        applied notice returns its original receipt with `repeated=True`. Refuses an unknown or another user's id
        (one refusal), a STANDING notice, and a notice whose record no longer exists. Host API only, never MCP."""
        r = self.store.confirm_notice(user_id, notice_id)
        self._record("redact", {"kind": r.redacted_kind, "fields": len(r.fields_cleared), "repeated": r.repeated}, user_id)
        return r

    # -- portability (see veracium.portability for the format) --------------
    # -- specs/0027 §4g (v14): reading the durable receipts -------------------
    def policy_receipts(self, user_id: str, *, limit: Optional[int] = None) -> list:
        """The user's stored `PolicyReceipt`s, newest first — every recall in
        which a policy lane fired on this store, exactly as each was returned
        (the row's verbatim JSON, parsed back; V-RECEIPT-DURABLE). Not part of
        the export (the receipt is deployment audit, not memory) and erased
        with the user (V-RECEIPT-ERASE)."""
        return [receipt_from_row(r) for r in self.store.policy_receipts(user_id, limit=limit)]

    def policy_receipt(self, user_id: str, recall_id: str) -> Optional["PolicyReceipt"]:
        """One stored receipt by the `recall_id` `recall` minted, or `None`."""
        row = self.store.policy_receipt(user_id, recall_id)
        return None if row is None else receipt_from_row(row)

    def export_memory(self, user_id: str, path) -> dict:
        """Write `user_id`'s complete memory to `path` as portable JSONL —
        full provenance/disclosure/history included, nothing summarized.
        The inverse of `import_memory`; see `docs/api.md` and the trust note
        in `veracium.portability`."""
        from . import portability
        r = portability.export_memory(self.store, user_id, path)
        self._record("export", {"edges": r["edges"], "episodes": r["episodes"]}, user_id)
        return r

    def import_memory(self, path, *, user_id: Optional[str] = None,
                      restore: bool = False, withhold_credentials: bool = False) -> dict:
        """Load a Veracium JSONL export into this store. Idempotent (existing
        ids are skipped, never overwritten); `user_id` remaps the records.

        Trust note (specs/0005): the DEFAULT import caps every record's trust
        — nothing imported is assertable or grounded as this user's own
        testimony, whatever the file claims. ``restore=True`` (mutually
        exclusive with ``user_id``) preserves the file's trust fields exactly
        and is the operator's assertion that the file is this store's own
        history; use it only on files you exported yourself or have
        independently verified. The returned dict carries ``capped``; the
        audit record deliberately keeps its shipped field set (§7a).

        specs/0055 §4h: the file is screened for credential shapes before any write. A plain import withholds free
        text and refuses a record whose identifier carries a shape (and the records linking to it); the result names
        them by locator and class, never a value. A restore that carries a shape refuses whole
        (`portability.CredentialImportRefused`) unless ``withhold_credentials=True`` is passed and only free text
        carries one; then the free text is withheld and the result lists the affected records."""
        from . import portability
        try:
            r = portability.import_memory(self.store, path, user_id=user_id,
                                          restore=restore, withhold_credentials=withhold_credentials,
                                          relations=self.config.relations)   # specs/0037: the RECEIVING registry's kinds
        except portability.CredentialImportRefused as exc:
            self._record("credential_refused", _cred.audit_fields(
                "import_memory", "file", source="import", classes={"records": len(exc.records)}), user_id or "")
            raise
        self._cred_withheld(r["user_id"], "import_memory", r.get("credentials_withheld") or {}, source="import")
        for rec in r.get("credential_refused_records") or ():
            self._record("credential_refused", _cred.audit_fields("import_memory", rec["field"], source="import",
                                                                  cls=rec["class"]), r["user_id"])
        self._record("import", {"edges": r["edges"], "episodes": r["episodes"],
                                "skipped": r["skipped"]}, r["user_id"])
        return r

    def close(self) -> None:
        # specs/0017 §4d transition 8 (close-deactivate, LINEARIZED per R9-1):
        # ONE critical section sets listener_active False AND cancels every
        # active entry — closure is forget-everything at the attribution
        # level — BEFORE any unsubscribe attempt. A retained callback may
        # still be INVOKED afterwards (a dead call); attribution is impossible
        # because listener step 6 and the terminal merge observe this state
        # under the same lock. Unsubscribe runs in its own try: a raising or
        # absent remove_usage_listener NEVER prevents store closure.
        with self._usage_lock:
            self._listener_active = False
            for entry in self._usage_registry.values():
                entry["cancelled"] = True
        if self._metered_handle is not None:
            try:
                remove = getattr(self.llm, "remove_usage_listener", None)
                if remove is not None:
                    remove(self._metered_handle)
            except Exception:
                pass
            self._metered_handle = None
        self.store.close()


# specs/0016 D2: the D1 package deprecation surface (the lazy `SourceType`
# __getattr__/__dir__) is RESOLVED by removal — the name is gone.
