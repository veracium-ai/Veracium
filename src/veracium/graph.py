"""Graph operations: functional supersession and entity-matched subgraph render.

Pure logic over the store — no LLM, no I/O beyond the store handle — so this is
the offline-testable heart of memory correctness (supersession-with-history is
the category the research found the industry worst at, and where veracium's design
scored best).
"""

from __future__ import annotations

from dataclasses import dataclass as _dataclass

import re
from datetime import datetime
from typing import Optional

from . import authority
from .schema import (DEFAULT_RELATIONS, ContributionDraft, Edge, EvidenceAuthor,
                     Relation, SupersessionPlan, SupersessionRefusalDraft)
from .store.base import (PLAN_STALE, ReceiptSchemaBoundaryError,
                         SupersessionIntegrityError)


# Filler words that never change a value's meaning. Deliberately tiny: a false
# "same" here silently merges two distinct facts, so anything that can carry
# meaning (prepositions, verbs, qualifiers) stays. my/our/their are kept as
# filler only because edge values are read relative to the edge's subject, so
# first-person and singular-they possessives are redundant; his/her can point
# at a third party ("his assistant" vs "her assistant") and therefore stay
# meaningful — they are NOT filler.
_VALUE_FILLER = {"a", "an", "the", "my", "our", "their", "named", "called"}


def _value_key(text: str) -> tuple[str, ...]:
    """Order-preserving normalization for value equivalence: paraphrases like
    'dog named Ollie' / 'dog Ollie' / 'a dog called Ollie.' compare equal, while
    order-sensitive values ('tea over coffee' vs 'coffee over tea') stay distinct."""
    toks = tuple(w for w in re.findall(r"[a-z0-9]+", text.lower())
                 if w not in _VALUE_FILLER)
    return toks or (text.strip().lower(),)


# T1 absorption bound: the fuller form may carry at most this many tokens beyond
# the shorter one ("cat Miso" over "Miso"). Two genuinely distinct values rarely
# differ by so few tokens while containing each other in order; anything wider
# is left to accumulate (visible, recoverable) rather than risk a false merge.
_ABSORB_MAX_EXTRA = 2


def _subsumes(longer: tuple[str, ...], shorter: tuple[str, ...]) -> bool:
    """True if `shorter` is an ordered subsequence of `longer` with 1..2 extra
    tokens. Ordered, not bag-subset, so the order-sensitivity contract of
    _value_key ('tea over coffee' ≠ 'coffee over tea') survives absorption."""
    if not 0 < len(longer) - len(shorter) <= _ABSORB_MAX_EXTRA:
        return False
    it = iter(longer)
    return all(t in it for t in shorter)


@_dataclass(frozen=True)
class SupersessionCounts:
    """specs/0015: the content-free per-call outcome summary. Computed ONLY
    from a fresh commit (replays are zero — the work was not performed in
    this call); `superseded` counts the committed plan's 'superseded'
    invalidations; `reinforced` is 1 iff the PLANNER took the reinforcement
    branch (the committed plan shape cannot distinguish it — I5)."""
    superseded: int = 0
    reinforced: int = 0
    replayed: bool = False


def subject_class(user_id: str, subject) -> str:
    """specs/0011 §4a (E1): "SELF" | "OTHER" — TOTAL, with OTHER the
    default. SELF iff the canonical subject equals the user under the
    0024 §4a predicate (whole-string strip().casefold() equality with
    the canonical "user" slot). Consumes the STORED subject — the
    str()-converted slot — never the note, never the relation (a
    relation cannot tell you whose fact it is). `user_id` is unused by
    the v1 predicate and part of the interface: research's E-Q1
    widening (aliases, entity refs) lands behind it without a signature
    change."""
    return "SELF" if str(subject).strip().casefold() == "user" else "OTHER"


def apply_supersession(store, edge: Edge, relations: dict[str, Relation]) -> "SupersessionCounts":
    """Persist a new edge with supersession, reinforcement, and absorption:

    - Reinforcement (specs/0012, Design 1): if an active same-class edge already
      asserts the same (subject, relation, object), the incoming restatement is
      PERSISTED as its own edge with its own provenance, and the prior is left
      byte-untouched — reinforcement transfers NOTHING (not `observed_at`, not
      `confidence`, not `valid_from`). The fact stays live *through the new
      edge* (each edge ages against its own `observed_at`), the persisted edge
      IS the attribution of the contributing source (closes finding M9), and a
      restatement can no longer silently renew a fact's currency or raise its
      confidence (the measured 0012 §1 bypass). "Same" is normalized-token
      equality (see _value_key); a *less* specific restatement of a value we
      already hold ("Miso" after "cat Miso") is the same evidentiary event and
      takes this branch too — it must never fall through to absorption or
      functional contention (0012 I6).
    - Absorption (T1): a *more* specific form of a prior value ("cat Miso"
      after "Miso", see _subsumes) wins — the shorter prior retires reversibly
      (reason 'absorbed_duplicate', note carries the winner's id). Identity,
      not change: no `supersedes` pointer, and render_edges never shows an
      absorbed value as history. Validity/confidence take the max of the pair;
      the winner keeps its own provenance.
    - Supersession: for a *functional* relation, a new value invalidates the
      prior active value (retained, reason 'superseded'), so history stays queryable.
    - Non-functional relations otherwise accumulate.

    Absorption fires at write time — fresh evidence just arrived — which is why
    it may mutate the absorbed prior; maintain-time bookkeeping never may.
    Reinforcement mutates NOTHING (accepted specs/0012 Design 1): it persists
    the restatement and leaves the prior byte-untouched — it neither refreshes
    validity nor touches needs_confirmation (only confirm() clears the flag,
    specs/0008).

    Identity merges never cross trust classes: both loops consider only priors
    in the same disclosure class as the incoming edge. Otherwise a third-party
    use_only restatement could retire a user-asserted fact out of assertable
    recall (or refresh its liveness, clear its staleness flag, and inherit its
    confidence) — dedup must not make trust decisions. Cross-class
    restatements accumulate as separate edges, each carrying its own trust;
    the explicit upgrade path for corroborated third-party material is
    confirm()/remember() by the user. (Different-value supersession is
    unaffected: a changed value superseding across classes is correct — the
    old value is stale regardless of who reported the new one.)
    """
    # specs/0003 §4f: the WHOLE outcome is applied as one atomic, CAS-linearized plan.
    # `apply_supersession` computes a plan from a store READ; the Store revalidates the
    # scope `expected_state` inside the transaction and applies all-or-nothing, or returns
    # PLAN_STALE (a concurrent write changed the state the plan assumed) and we recompute.
    op_id = f"sup-{edge.id}"
    # specs/0014 §4b — PHASE 1, the PUBLIC pre-plan receipt lookup, THREE
    # branches (R10-2). The snapshot is captured from the RAW submitted edge
    # BEFORE any planning; the digest construction is the store's own frozen
    # one (no caller assertion — R7-1).
    from .contribution import raw_request_snapshot, receipt_request_matches
    snapshot = raw_request_snapshot(edge)
    receipt = store.supersession_receipt(edge.user_id, op_id)
    if receipt is not None:
        # specs/0016 D2 — the receipt ERA boundary, BEFORE every branch: a
        # receipt stamped below version 4 committed over the deleted
        # source_type field's snapshot; no historical projection is
        # computable, so it refuses UNCONDITIONALLY ON SIGHT — no digest is
        # computed (the request_digest call below is never reached), no
        # comparison branch exists (0019 rider A2; 0003 §4f as amended).
        # An ABSENT version cannot come from a conforming store (0014 read
        # validation rejects it) — if a non-validating backend surfaces one,
        # the receipt is unclassifiable and takes the same conservative
        # refusal (fail closed, never fail open into a digest comparison).
        stored_ver = receipt.get("outcome_digest_version")
        if stored_ver is None or stored_ver < 4:
            raise ReceiptSchemaBoundaryError(
                f"operation_id {op_id!r} for user {edge.user_id!r} committed "
                f"under a pre-D2 receipt era (outcome_digest_version "
                f"{stored_ver}): its digest basis included the deleted "
                f"source_type field, so this resubmission is not replay-"
                f"verifiable across the removal — refused on sight, no digest "
                f"computed, a legitimate retry indistinguishable from a "
                f"different request (specs/0016 D2; 0003 §4f as amended)")
        stored_rd = receipt.get("request_digest")
        # specs/0025 §4b-v: the cross-era decision matrix — the stored
        # domain selects the comparison (NULL = migrated → dual-domain;
        # a valid domain → that domain only; fail-closed cells raise
        # ReceiptDomainError from the matrix itself). The pre-D2 boundary
        # above PRECEDES this, so no digest is computed for stored_ver < 4.
        matches = receipt_request_matches(
            stored_rd, receipt.get("request_digest_domain"), snapshot)
        if matches is not None:
            if matches:
                # branch 1: REPLAY — the recorded response stands in for the
                # committed op; NO re-planning occurs (the post-commit re-plan
                # is never computed, so no outcome comparison can reject a
                # legitimate lost-response retry — the R5-2 live defect closed).
                # specs/0015 I2: a replay performs no work in THIS call.
                return SupersessionCounts(replayed=True)
            # branch 2: a truly different resubmission reusing an op id
            raise SupersessionIntegrityError(
                f"operation_id {op_id!r} already committed a DIFFERENT request "
                f"for user {edge.user_id!r} (specs/0014 §4b phase 1)")
        # branch 3: NULL stored digest (either legal NULL form) — request
        # identity UNAVAILABLE, never "different": continue to planning and
        # phase 2, where the version-selected outcome comparison governs.
    for _ in range(_MAX_PLAN_ATTEMPTS):
        plan, is_reinforcement = _build_supersession_plan(store, edge, relations, op_id)
        plan.raw_request = snapshot
        result = store.apply_supersession_plan(plan)
        if result is not PLAN_STALE:
            # specs/0015: count ONLY the committing attempt (I3); phase-2
            # replays are zero (I2); classification comes from the planner
            # branch + the plan's invalidation reasons, never plan shape (I5).
            if result.replayed:
                return SupersessionCounts(replayed=True)
            return SupersessionCounts(
                superseded=sum(1 for _, _, r in plan.prior_invalidations
                               if r == "superseded"),
                reinforced=1 if is_reinforcement else 0)
    raise RuntimeError(
        f"apply_supersession_plan kept returning PlanStale for edge {edge.id!r} after "
        f"{_MAX_PLAN_ATTEMPTS} attempts — the (user, subject, relation) scope is being "
        f"mutated faster than one supersession can commit (specs/0003 §4f)")


_MAX_PLAN_ATTEMPTS = 16


def _absorption_scope_gate(store, edge: Edge):
    """specs/0021 §4c / W2 — the same-SCOPE half of the absorption candidate
    rule, as a lazily-built predicate over priors.

    The membership answer is the SHARED `MembershipResolver` (the read half's
    own resolver, 0020 §4a-iii): read-time and write-time must never disagree
    about which scope a record is in, and the only way to guarantee that is to
    ask the same object. Nothing here consults a `ScopePolicy` — §2's ruling
    is that identity partitioning is policy-independent.

    The rule, per prior:

    - the incoming's own evidence UNRESOLVED → it absorbs nothing (fail
      closed; a legacy-shaped incoming is the reachable case);
    - the prior's evidence UNRESOLVED, or differing from the incoming's →
      NOT a candidate (`SHARED` equals `SHARED`, so the host-produced
      unidentified population still merges among itself);
    - a prior whose CLOSURE is None is UNRESOLVED and "never absorbs or is
      absorbed" (§4c) — the flattening plan is that closure, so demanding it
      here is the same gate the write step depends on, asked before the
      decision rather than after.

    Nothing is computed until a value-subsumption candidate actually appears:
    the overwhelmingly common ingest does no ledger work at all."""
    from .scope import UNRESOLVED
    from .scope_read import MembershipResolver
    if not hasattr(store, "local_origin"):
        # a backend with no 0006 store identity has no identities to
        # partition BY — every record is unidentified, which is one shared
        # pool and today's behaviour exactly (§5's identity-free regime),
        # reached honestly rather than by an AttributeError. The same
        # treatment `lifecycle.partition_cold` gives the maintain side.
        return lambda prior: True
    state: dict = {}

    def same_scope(prior) -> bool:
        if "resolver" not in state:
            r = MembershipResolver(store, edge.user_id)
            state["resolver"] = r
            # the incoming is a NEW row: its evidence is its own shape with
            # NO ledger rows. Asked through the same method the atomic
            # primitive re-derives it with, so planner and store cannot
            # answer this differently.
            state["incoming"] = r.evidence_of_unwritten(edge)
        r, inc = state["resolver"], state["incoming"]
        if inc == UNRESOLVED:
            return False
        if r.evidence(prior) != inc:
            return False              # cross-scope, or the prior UNRESOLVED
        return r.flattening_plan("edge", prior.id) is not None

    return same_scope


# specs/0011 §4f (E6): THE one history vocabulary — five labels, first-match.
# Readers that meet a quarantined or contested edge use this instead of each
# inventing a rendering; totality holds by the row-5 catch-all and exclusivity
# by first-match, both by construction rather than enumeration.
HISTORY_LABELS = ("RETIRED_HISTORY", "QUARANTINED_CLAIM", "CONTESTED_CURRENT",
                  "UNVERIFIED_CURRENT", "GROUNDED_CURRENT")


def history_label(edge: Edge, *, contested: bool) -> str:
    """specs/0011 §4f (E6): label one edge with exactly one of the five
    HISTORY_LABELS. `contested` is DERIVED by the caller from the live
    refusal contentions (specs/0003's refusal-scoped notion — the shipped
    `Recall.contested` predicate; there is NO stored carrier). Precedence is
    a claim in itself: quarantine outranks contention (a quarantined edge's
    dispute is moot until it leaves quarantine); contention outranks
    ungroundedness (a contested value must not render as merely
    unverified-but-current). READS disclosure-derived properties, never
    writes them (S7 — the 0023 N2 single-writer sweep covers this file)."""
    if not edge.active:
        return "RETIRED_HISTORY"
    if edge.quarantined:
        return "QUARANTINED_CLAIM"
    if contested:
        return "CONTESTED_CURRENT"
    if edge.ungrounded or edge.use_only:
        return "UNVERIFIED_CURRENT"
    return "GROUNDED_CURRENT"


class CorrectionRefused(Exception):
    """specs/0011 §4e/§4b: the requested correction may not retire its prior —
    the durable refusal row IS recorded (like every refused supersession)
    before this is raised, and nothing else is written. Carries `prior_edge_id`
    and `rule_version` so a host can attribute the refusal."""

    def __init__(self, prior_edge_id: str, rule_version: str):
        self.prior_edge_id = prior_edge_id
        self.rule_version = rule_version
        super().__init__(
            f"correction of edge {prior_edge_id!r} refused under "
            f"{rule_version}: a bare self-assertion cannot retire this prior "
            f"(specs/0011 §4b applies to corrections exactly as to "
            f"extractor-driven supersession)")


def plan_correction(store, prior: Edge, replacement: Edge,
                    op_id: str) -> tuple[SupersessionPlan, bool]:
    """specs/0011 §4e (E5): the plan for one DIRECTED correction — the named
    prior retires as 'corrected' and the replacement is inserted, atomically,
    through exactly the machinery extractor supersession uses. Pure: reads and
    returns; the Store applies (and verifies the CorrectionAuthorisation)
    in-transaction. Returns (plan, refused).

    §4b applies to corrections exactly as to extractor supersession: the
    subject cell and the authority ladder are checked against the NAMED prior,
    and a refused correction produces a refusal-only plan (nothing retired,
    nothing inserted, the durable refusal row recorded)."""
    if (replacement.subject != prior.subject
            or replacement.relation != prior.relation
            or replacement.user_id != prior.user_id):
        raise ValueError(
            "a correction replaces a value IN PLACE: the replacement must "
            "share the prior's (user, subject, relation)")
    scope = store.edges(prior.user_id, subject=prior.subject,
                        relation=prior.relation, active_only=True,
                        include_quarantined=True)
    if not any(p.id == prior.id for p in scope):
        # the prior was retired between the caller's read and this plan: a
        # corrected retirement may only target an edge the CAS fingerprint
        # PINS AS ACTIVE — otherwise the commit would double-retire it and
        # overwrite its recorded reason (the diff-scan race, closed here)
        raise ValueError(
            f"edge {prior.id!r} is not active in its (user, subject, "
            f"relation) scope — a correction cannot retire a prior the CAS "
            f"token does not pin (specs/0011 §4e)")
    expected = authority.scope_fingerprint(scope)
    draft = SupersessionRefusalDraft(
        prior_edge_id=prior.id, incoming_edge_id=replacement.id,
        relation=prior.relation,
        prior_effective=authority.edge_effective(prior),
        incoming_effective=authority.edge_effective(replacement))
    refused = (
        (subject_class(prior.user_id, prior.subject) == "OTHER"
         and authority.self_assertion(
             replacement.provenance.author_of_evidence,
             replacement.provenance.derived_from))
        or not authority.permitted(
            prior.provenance.author_of_evidence,
            prior.provenance.derived_from,
            replacement.provenance.author_of_evidence,
            replacement.provenance.derived_from))
    if refused:
        return SupersessionPlan(
            incoming_edge=replacement, insert_incoming=False,
            operation_id=op_id, expected_state=expected,
            refusals=[draft]), True
    replacement.supersedes = prior.id
    return SupersessionPlan(
        incoming_edge=replacement, insert_incoming=True,
        operation_id=op_id, expected_state=expected,
        prior_invalidations=[(prior.id, replacement.valid_from,
                              "corrected")]), False


def _build_supersession_plan(store, edge: Edge, relations: dict[str, Relation],
                             op_id: str) -> tuple[SupersessionPlan, bool]:
    """Compute the plan for one incoming edge from a store read (specs/0003 §4f). Pure —
    it reads and returns a plan, it does not mutate; the Store applies it atomically."""
    same = _value_key(edge.object)
    # The scope the plan reasons about and the CAS token it carries: ALL active edges of
    # this (user, subject, relation), incl. quarantined — the same set the Store recomputes.
    scope = store.edges(edge.user_id, subject=edge.subject, relation=edge.relation,
                        active_only=True, include_quarantined=True)
    expected = authority.scope_fingerprint(scope)
    same_class = [p for p in scope
                  if p.id != edge.id
                  and p.provenance.disclosure == edge.provenance.disclosure]

    # 0023 N3–N5/N7: THE STANDING-REVOCATION GUARD, one predicate for all
    # three branches below. Keyed on RESOLVED IDENTITY against the standing
    # set — not on disclosure — because the quarantine floor is a read-side
    # verdict and these branches decide what the store COMBINES. The fast
    # path (`not standing`) is N12's byte-identity promise: a store with no
    # standing revocation takes exactly the pre-0023 code path.
    standing = store.standing_revocations(edge.user_id)

    def _src_revoked(e) -> bool:
        if not standing or not hasattr(store, "local_origin"):
            return False
        from .scope_linkage import identity_digest_of
        d = identity_digest_of(e.provenance.origin, e.provenance.source_id,
                               store.local_origin())
        return d is not None and d in standing

    inc_revoked = _src_revoked(edge)

    # Reinforcement (specs/0012 §4a, Design 1): an active same-class prior asserts the
    # same-or-subsuming value. The branch KEEPS its guard predicate and position (before
    # absorption, before the functional branch — deleting it would mis-route a SUBSUMED
    # value like "Miso" after "cat Miso" into functional contention, 0012 I6) but its
    # ACTION is persist-incoming-untouched: the restatement is stored with byte-unchanged
    # provenance (I1), the prior is not read-modified-written (I2 — the old max() transfers
    # are deleted, not relocated; a restatement can no longer renew currency or raise
    # confidence, 0012 §1/I5), and nothing else happens — no upsert, no invalidation, no
    # refusal, no supersedes pointer (I6). needs_confirmation is untouched trivially
    # (specs/0008 — only confirm() clears; the prior is not written at all, I4). The
    # persisted edge is the attribution of the contributing source (M9, I7).
    for prior in same_class:
        if inc_revoked or _src_revoked(prior):
            continue          # N3: a revoked source's restatement is not
                              # COUNTED as reinforcement; it accumulates plain
        pk = _value_key(prior.object)
        if pk == same or _subsumes(pk, same):
            return SupersessionPlan(incoming_edge=edge, insert_incoming=True,
                                    operation_id=op_id, expected_state=expected), True

    incoming = edge.model_copy(deep=True)
    upserts: list[Edge] = []
    invalidations: list[tuple] = []
    refusals: list[SupersessionRefusalDraft] = []
    absorbed: set[str] = set()
    contribution_drafts: list[ContributionDraft] = []
    # specs/0014 §4b (R3-1): the absorption pre-image — the incoming's ORIGINAL
    # values over the closed §4a field set, snapshotted BEFORE any inheritance
    # mutation below. The survivor IS the incoming (a NEW row), so this snapshot
    # is the only place its pre-state exists; it becomes the `base` side of every
    # absorption payload and enters the v2 outcome digest. `derived_from` is
    # OMITTED when None (never null) — the canonical §4a form.
    from .contribution import json_datetime
    pre_image = {
        "observed_at": json_datetime(incoming.provenance.observed_at),
        "confidence": incoming.provenance.confidence,
        "valid_from": json_datetime(incoming.valid_from),
        "disclosure": incoming.provenance.disclosure.value,
    }
    if incoming.provenance.derived_from is not None:
        pre_image["derived_from"] = incoming.provenance.derived_from.value

    # Absorption (T1): a MORE specific same-class form of a prior value wins — the shorter
    # prior retires reversibly (absorbed_duplicate; note carries the winner's id), and the
    # winner inherits the earliest valid_from / max observed_at+confidence. Identity, not
    # change — no supersedes pointer.
    #
    # specs/0021 §4c — THE ABSORPTION PARTITION, extending the shipped
    # same-class idiom: a candidate must ALSO present the same SCOPE
    # membership evidence. A cross-scope or UNRESOLVED prior is not a
    # candidate; it accumulates as a separate edge, which is exactly today's
    # cross-CLASS behaviour extended one axis. The gate is POLICY-INDEPENDENT
    # (§2): no host's configuration reaches it, because policy is a read-side
    # concept and this decides what the store MERGES.
    same_scope = _absorption_scope_gate(store, edge)
    for prior in same_class:
        if inc_revoked or _src_revoked(prior):
            continue          # N4: neither side of an absorption may be a
                              # revoked source — both records persist
                              # separately. N7 rides on this refusal: the
                              # max(observed_at)/max(confidence) inheritance
                              # below is the ONE seam where currency survives
                              # (M2: there is no renewal verb), so refusing
                              # candidacy IS refusing renewal
        if _subsumes(same, _value_key(prior.object)) and same_scope(prior):
            incoming.valid_from = min(incoming.valid_from, prior.valid_from)
            incoming.provenance.observed_at = max(incoming.provenance.observed_at,
                                                  prior.provenance.observed_at)
            incoming.provenance.confidence = max(incoming.provenance.confidence,
                                                 prior.provenance.confidence)
            # specs/0019 §4d (R2-3/R2-4): the winner's flag is the N-ary OR
            # over {incoming} ∪ absorbed — accumulated per contributor here,
            # order-independent, computed PRE-PERSIST before the survivor row
            # exists. A merge never launders the signal; once ungrounded, the
            # surviving representation stays flagged.
            incoming.ungrounded = incoming.ungrounded or prior.ungrounded
            noted = prior.model_copy(deep=True)
            noted.note = ((f"{noted.note}; " if noted.note else "")
                          + f"absorbed_by:{incoming.id} (restated as {incoming.object!r})")
            upserts.append(noted)
            invalidations.append((prior.id, incoming.valid_from, "absorbed_duplicate"))
            absorbed.add(prior.id)
            # specs/0014 §4b: one reference-only draft per absorbed prior — the
            # store enforces EXACT SET EQUALITY with the absorbed_duplicate
            # invalidations (R5-1) and derives the payload itself (R2-1).
            contribution_drafts.append(ContributionDraft(
                site="absorption", survivor_type="edge", survivor_id=incoming.id,
                contributor_type="edge", contributor_id=prior.id))

    # Supersession (§4a): for a FUNCTIONAL relation, a differing value retires the prior —
    # but ONLY when the incoming edge's recorded effective authority is >= the prior's
    # (the reported defect was the unconditional retirement). Otherwise the retirement is
    # REFUSED: the prior stays active, the incoming edge is stored, both are visible (§4b),
    # and a durable content-free refusal is recorded. Reads ALL classes (a cross-class
    # differing value is exactly the attack); a same-value prior of another class is left
    # alone; an already-absorbed prior is skipped.
    rel = relations.get(edge.relation)
    if rel and rel.functional:
        for prior in scope:
            if prior.id == edge.id or prior.id in absorbed:
                continue
            if _value_key(prior.object) == same:
                continue
            if inc_revoked:
                # N5: a revoked-source incoming may not retire a standing
                # record, WHATEVER its recorded authority says — the prior
                # stays active and a durable content-free refusal is
                # recorded. The REVERSE still works: `prior` being revoked
                # changes nothing here, so a live incoming retires a
                # revoked-source prior exactly as before.
                refusals.append(SupersessionRefusalDraft(
                    prior_edge_id=prior.id, incoming_edge_id=incoming.id,
                    relation=edge.relation,
                    prior_effective=authority.edge_effective(prior),
                    incoming_effective=authority.edge_effective(incoming)))
            elif (subject_class(edge.user_id, prior.subject) == "OTHER"
                  and authority.self_assertion(
                      incoming.provenance.author_of_evidence,
                      incoming.provenance.derived_from)):
                # specs/0011 §4b (E2): the SUBJECT axis, a refusal
                # WIDENING over the author ladder — a user statement on
                # their own authority cannot retire ANY OTHER-subject
                # prior, sourced or not (R2-1: the rule reads no
                # source_id; that is the point, not an omission). Both
                # edges stay visible; the refusal row is durable, and
                # rule_version v2 stamps which policy refused.
                refusals.append(SupersessionRefusalDraft(
                    prior_edge_id=prior.id, incoming_edge_id=incoming.id,
                    relation=edge.relation,
                    prior_effective=authority.edge_effective(prior),
                    incoming_effective=authority.edge_effective(incoming)))
            elif authority.permitted(prior.provenance.author_of_evidence,
                                    prior.provenance.derived_from,
                                    incoming.provenance.author_of_evidence,
                                    incoming.provenance.derived_from):
                invalidations.append((prior.id, incoming.valid_from, "superseded"))
                incoming.supersedes = prior.id
            else:
                refusals.append(SupersessionRefusalDraft(
                    prior_edge_id=prior.id, incoming_edge_id=incoming.id,
                    relation=edge.relation,
                    prior_effective=authority.edge_effective(prior),
                    incoming_effective=authority.edge_effective(incoming)))

    return SupersessionPlan(incoming_edge=incoming, insert_incoming=True,
                            operation_id=op_id, expected_state=expected,
                            prior_upserts=upserts, prior_invalidations=invalidations,
                            refusals=refusals,
                            contribution_drafts=contribution_drafts,
                            absorption_pre_image=(pre_image if contribution_drafts
                                                  else None)), False


_STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on",
         "for", "and", "or", "s", "does", "did", "what", "who", "when", "where",
         "how", "which", "with", "her", "his", "their", "they", "do", "have",
         # "user" is the implicit owner of a per-user store: it appears in most
         # questions AND is the subject of most edges, so counting it as a match
         # makes every edge look equally relevant — which is precisely how
         # ranking collapsed at scale.
         "user"}

# Crude suffix folding so a question's wording reaches a stored relation:
# "work" must match `works_for`, "pets" must match `has_pet`, "deadlines" must
# match the `deadline` relation. Not a stemmer — just enough morphology to stop
# exact-token matching from failing on ordinary plurals, applied to both sides.
# Deliberately excludes "es": stripping it maps "deadlines"->"deadlin" and so
# stops matching "deadline", i.e. the rule breaks more matches than it makes.
# Known and accepted misses: doubled consonants ("running"/"run") and words
# whose stem ends in s ("address"/"addresses").
_SUFFIXES = ("ing", "ed", "s")


def _stem(w: str) -> str:
    """Fold to a fixed point, never below a 3-character stem.

    Iterating matters: a single pass would map 'addresses'->'address' but
    'address'->'addres', so the two forms would stop matching — a stemmer that
    breaks matches is worse than none. Converging both to 'addre' keeps the
    relation symmetric, which is the only property this needs to have.
    """
    while True:
        for suf in _SUFFIXES:
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                w = w[: -len(suf)]
                break
        else:
            return w


def _tokens(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())
            if w not in _STOP and len(w) > 2}


def _permute_contention_groups(edges: list[Edge],
                               relations: dict[str, Relation]) -> list[Edge]:
    """specs/0003 §4e: within an active functional-contention group — the active edges
    sharing a `(subject, relation)` key whose relation is functional and which hold >1
    DISTINCT value — recorded effective authority dominates, ahead of relevance and
    recency. It is a PERMUTATION, not a global sort: only the positions a group's members
    already occupy are reordered; every unrelated edge keeps its position (I6b). Conservative
    in the same direction as the guard — it can only prefer higher-authority evidence."""
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for i, e in enumerate(edges):
        rel = relations.get(e.relation)
        if e.active and rel and rel.functional:
            groups[(e.subject, e.relation)].append((i, e))
    out = list(edges)
    for members in groups.values():
        if len({_value_key(e.object) for _, e in members}) <= 1:
            continue                                   # same value → not a contention
        positions = [i for i, _ in members]            # the exact slots to permute within
        # authority DESC, then original relevance (position) ASC, then recency DESC
        ordered = sorted(members, key=lambda ie: (
            -authority.edge_effective(ie[1]), ie[0],
            -ie[1].provenance.observed_at.timestamp()))
        for pos, (_orig, e) in zip(positions, ordered):
            out[pos] = e
    return out


def _lexical_scored(store, user_id: str, query: str, view=None):
    """specs/0027 §2 — the extracted per-edge lexical scan (the shipped
    `subgraph_for_query` loop, byte-identical for `view=None`; the frozen V10
    oracle pins that). Returns `(scored, relevant_ids, by_id)`:

    - `scored`: `[(score, overlap, edge)]` for every edge entering the lexical
      lane (`base > 0`), sorted `(-score, -observed_at)` — exactly today's
      pre-collapse ranking, the eligibility floor riding it (a user-subject
      edge is eligible at overlap 0);
    - `relevant_ids`: the `overlap > 0` ids (the I6 relevance set);
    - `by_id`: EVERY visible (and, under a view, SHAPED — §3b Stage 0) edge by
      id, including base-0 entity edges — the semantic lane's candidate pool
      and the fused construction's edge lookup.

    Under a `view` each candidate passes visibility THEN shaping BEFORE
    scoring (0027 §4a Stage 0-1): every edge any later stage sees is the
    principal-facing record, so the I6 reserve reads shaped assertability."""
    q = _tokens(query)
    scored: list[tuple[int, int, Edge]] = []
    relevant_ids: set[str] = set()
    by_id: dict[str, Edge] = {}
    for e in store.edges(user_id, active_only=False):
        if view is not None:
            if not view.visible(e):
                continue
            e = view.shape(e)
        by_id[e.id] = e
        overlap = len(_tokens(f"{e.subject} {e.relation} {e.object} {e.note}") & q)
        if overlap:
            relevant_ids.add(e.id)
        if e.subject == "user":
            base = 1 + 2 * overlap      # eligible always; ranked by relevance
        else:
            base = 3 * overlap          # entity edges must match to enter at all
        if base:
            # prefer active over superseded, and closer matches
            scored.append((base + (1 if e.active else 0), overlap, e))
    scored.sort(key=lambda t: (-t[0], -t[2].provenance.observed_at.timestamp()))
    return scored, relevant_ids, by_id


def subgraph_for_query(store, user_id: str, query: str, *, max_edges: int = 40,
                       coverage_share: float = 0.25,
                       relations: Optional[dict[str, Relation]] = None) -> list[Edge]:
    """Entity-matched neighborhood: every edge off the user node, plus edges whose
    tokens appear in the query, ranked by how well they match it. This is
    veracium's primary retrieval (the research found it beat similarity search on
    every question type). Includes superseded edges (rendered as history) and
    quarantined edges (rendered flagged) so the caller can show provenance.

    User-subject edges are always *eligible* — that is the "everything off the
    user node" contract, and for a small store they all fit under `max_edges`
    anyway — but eligibility is not ranking. Until 0.4.2 they carried a constant
    score, so once a store grew past `max_edges` the truncation returned
    whichever ones the store listed first (i.e. the oldest), and the query was
    ignored entirely for the subject that owns most facts. On a 1.7k-fact store
    that made recall effectively query-blind; widening the cap only returned
    more old facts. Relevance now decides which ones survive truncation, with
    recency as the tiebreak, and `relation` counts as matchable text so "pet"
    can reach `has_pet`.
    """
    # specs/0003 §4e: the relation registry decides which relations are functional (and so
    # which groups are contentions). Additive with a defined default — a host that has
    # customised `MemoryConfig.relations` MUST pass it (exactly as it must to `ingest`),
    # else a relation it made functional is treated as ordinary and its contention is not
    # authority-ordered (round-6 correction C).
    relations = relations if relations is not None else DEFAULT_RELATIONS
    # specs/0001 I6 (candidate, R10-1): the relevance bit is carried FROM
    # scoring — a user-subject edge is ELIGIBLE at baseline score with zero
    # overlap, and eligibility is not relevance; the reserve below protects
    # only query-RELEVANT assertable records. specs/0027 §2: the scan itself
    # is the extracted `_lexical_scored` (unscoped here — this function IS the
    # legacy `principal=None` path the V10 oracle freezes); its recency
    # tiebreak reads observed_at — "most recently recorded", not "became true
    # earliest" (valid_from is the first-known axis).
    scored3, relevant_ids, _by_id = _lexical_scored(store, user_id, query)
    scored = [(sc, e) for sc, _ov, e in scored3]
    # specs/0012 I8: collapse strictly-redundant ACTIVE duplicates AFTER scoring
    # (a query-matching note-bearer already surfaces via the suppression predicate)
    # and BEFORE truncation, so suppressed members never consume max_edges slots.
    surfaced, _info = collapse_for_render([e for _, e in scored])
    surfaced_ids = {e.id for e in surfaced}
    scored = [(sc, e) for sc, e in scored if e.id in surfaced_ids]
    if len(scored) <= max_edges:
        ordered = [e for _, e in scored]
    else:
        # specs/0001 I6 (candidate): reserve assertable slots on the FULL
        # scored post-collapse set BEFORE truncation — a record _cover has
        # already discarded cannot be recovered downstream (R5-2). Reserved
        # records seed covered-day state; the coverage budget runs over the
        # post-reserve remainder; backfill stays deterministic (R6-4).
        # R10-1: the reserved set is the query-RELEVANT assertable
        # records (spec: count_relevant_assertable) — an assertable edge
        # seated only by user-subject eligibility must not displace a
        # relevant record (the reviewer's executed counterexample:
        # 'bananas' reserved first, a relevant fact dropped)
        assertable = [e for _, e in scored
                      if e.assertable and e.id in relevant_ids]
        reserve_n = min(len(assertable), -(-max_edges // 4))
        reserved = assertable[:reserve_n]
        rid = {e.id for e in reserved}
        rest_scored = [(sc, e) for sc, e in scored if e.id not in rid]
        rest = _cover(rest_scored, max_edges - len(reserved),
                      coverage_share,
                      seed_days={e.valid_from.date() for e in reserved})
        # R9-1: the output is CONSTRUCTED as reserved + remainder — the
        # previous filter over the globally scored list preserved global
        # rank, so with a NON-functional relation (no authority
        # permutation to mask it) a reserved assertable record surfaced
        # last, violating "reserved records are placed first". Both
        # segments keep their scored order internally.
        rest_ids = {e.id for e in rest}
        ordered = reserved + [e for _, e in scored if e.id in rest_ids]
    # authority permutation WITHIN functional-contention groups; unrelated order unchanged
    return _permute_contention_groups(ordered, relations)


RRF_K = 60          # specs/0027 §4a Stage 2 — fixed, not tunable


def semantic_duplicate_of(m: Edge, survivor: Edge) -> bool:
    """specs/0027 §4a Stage 3 — the COMPLETE suppression predicate for a
    semantic-only candidate against an already-kept edge (R6-1).
    `_strictly_redundant` alone is a within-group test and returns true for
    unrelated default-metadata edges, so ALL five conjuncts must hold:

    1. both ACTIVE — never suppress against, or as, inactive history;
    2. identical collapse envelope (subject, relation, disclosure, author,
       derived_from) — the I8f authority envelope;
    3. exact value-equivalence — a SUBSUMING semantic value is DISTINCT and
       is added, not suppressed;
    4. strictly redundant (no carrier-visible information beyond the
       survivor);
    5. warning-carrier preservation — `m` carries no flag the survivor lacks
       (suppressing it would drop a warning from the surface)."""
    if not (m.active and survivor.active):
        return False
    if (m.subject, m.relation, m.provenance.disclosure,
            m.provenance.author_of_evidence, m.provenance.derived_from) != \
       (survivor.subject, survivor.relation, survivor.provenance.disclosure,
            survivor.provenance.author_of_evidence,
            survivor.provenance.derived_from):
        return False
    if _value_key(m.object) != _value_key(survivor.object):
        return False
    if not _strictly_redundant(m, survivor):
        return False
    if m.needs_confirmation and not survivor.needs_confirmation:
        return False
    if m.ungrounded and not survivor.ungrounded:
        return False
    return True


def fused_subgraph(scored, relevant_ids, by_id, sm, *, max_edges: int = 40,
                   coverage_share: float = 0.25,
                   relations: Optional[dict[str, Relation]] = None):
    """specs/0027 §4a Stages 2-5 — the one total ordered retrieval-and-budget
    construction, over prepared inputs: `scored`/`relevant_ids`/`by_id` from
    `_lexical_scored` (Stage 0-1, already scoped/shaped), `sm` the semantic
    lane's `(edge_id, cosine)` list (Stage 1, already visibility-filtered and
    fresh — or empty/None when the lane did not run).

    Returns `(ordered_edges, meta)` where `meta` maps each SELECTED edge id to
    its recall-provenance dict ({lexical_overlap, semantic_cosine, fused_rank,
    fused_score, route}) — exactly the ranked query selection, nothing else
    (V7: contention/I6a additions downstream get no entry).

    Degenerate identity (V10): with `sm` empty this reduces to the legacy
    construction — fused_score is strictly decreasing in lexical rank, Stage 3
    keeps exactly `collapse_for_render(Lx)` in lexical order, and Stages 4-5
    receive byte-identical input to `subgraph_for_query`'s."""
    relations = relations if relations is not None else DEFAULT_RELATIONS
    lx_edges = [e for _sc, _ov, e in scored]
    lx_rank = {e.id: i + 1 for i, e in enumerate(lx_edges)}       # 1-indexed
    overlap_by = {e.id: ov for _sc, ov, e in scored}
    sm = [(eid, cos) for eid, cos in (sm or []) if eid in by_id]
    sm_rank = {eid: i + 1 for i, (eid, _c) in enumerate(sm)}
    sm_cos = dict(sm)

    # Stage 2 — RRF fusion. Absence from a lane contributes NO term (never a
    # max-rank penalty); order (-fused, -observed_at, edge_id) — the shipped
    # recency tiebreak, then id for full determinism. fused_rank is recorded
    # HERE and is immutable thereafter (Stage 5 permutes position only).
    fused_score: dict[str, float] = {}
    for eid in set(lx_rank) | set(sm_rank):
        f = 0.0
        if eid in lx_rank:
            f += 1.0 / (RRF_K + lx_rank[eid])
        if eid in sm_rank:
            f += 1.0 / (RRF_K + sm_rank[eid])
        fused_score[eid] = f
    fused_ids = sorted(fused_score, key=lambda i: (
        -fused_score[i], -by_id[i].provenance.observed_at.timestamp(), i))
    fused_order = [by_id[i] for i in fused_ids]
    fused_rank = {eid: i + 1 for i, eid in enumerate(fused_ids)}
    # the EXTENDED relevance set: a semantic hit counts as relevance for the
    # I6 reserve, not just eligibility (§4a Stage 2)
    rel_ext = set(relevant_ids) | set(sm_rank)

    # Stage 3 — collapse: MEMBERSHIP from lexical, ORDER from fused (R6-1).
    lx_ids = set(lx_rank)
    survivors, _info = collapse_for_render(lx_edges)
    kept = {e.id for e in survivors}
    kept_edges = list(survivors)
    for e in fused_order:
        if e.id in lx_ids:
            continue                       # lexical membership already decided
        if any(semantic_duplicate_of(e, k) for k in kept_edges):
            continue                       # a pure duplicate of a kept edge
        kept_edges.append(e)
        kept.add(e.id)
    stage3 = [e for e in fused_order if e.id in kept]

    # Stage 4 — the SINGLE I6 reserve, byte-for-byte today's construction over
    # the fused order and the extended relevance set.
    if len(stage3) <= max_edges:
        ordered = stage3
    else:
        assertable = [e for e in stage3 if e.assertable and e.id in rel_ext]
        reserve_n = min(len(assertable), -(-max_edges // 4))
        reserved = assertable[:reserve_n]
        rid = {e.id for e in reserved}
        rest_pairs = [(0, e) for e in stage3 if e.id not in rid]
        rest = _cover(rest_pairs, max_edges - len(reserved), coverage_share,
                      seed_days={e.valid_from.date() for e in reserved})
        rest_ids = {e.id for e in rest}
        ordered = reserved + [e for e in stage3 if e.id in rest_ids]

    # Stage 5 — functional-contention permutation, unchanged; position only.
    ordered = _permute_contention_groups(ordered, relations)

    meta = {}
    for e in ordered:
        eid = e.id
        route = ("both" if eid in lx_rank and eid in sm_rank
                 else "semantic" if eid in sm_rank else "lexical")
        meta[eid] = {"edge_id": eid,
                     "lexical_overlap": overlap_by.get(eid, 0),
                     "semantic_cosine": sm_cos.get(eid),
                     "fused_rank": fused_rank[eid],
                     "fused_score": fused_score[eid],
                     "route": route}
    return ordered, meta


def _cover(scored: list[tuple[int, Edge]], max_edges: int,
           coverage_share: float, seed_days: set | None = None) -> list[Edge]:
    """Fill most of the budget by pure relevance, reserve the tail for time
    coverage.

    Pure top-k has no coverage term, so when many facts share vocabulary the
    selection collapses onto whichever period dominates — a question spanning
    months can be answered from a single day's records, and a question about an
    interval gets one endpoint. Reserving a slice of the budget for periods not
    already represented costs a few of the least-relevant head slots and buys
    the ability to see across time.

    Clustering is on `valid_from` (the day a fact became true), because that is
    the only temporal key always available: session identity is a host concept
    that most callers never supply, so a session-based rule would be
    unimplementable outside a benchmark harness.

    Deliberately conservative, with one edge that is NOT conservative and is
    stated here because measurement found it (R2, 2026-08-01):
      * the head is filled by relevance alone, so the TOP-RANKED facts are never
        displaced by coverage — but the head SHRINKS by the reserve, so
        candidates ranked between `max_edges - reserve` and `max_edges` ARE
        displaced, by construction. **Relevance rank is not answer-bearingness.**
        In R2 an item whose single answer-bearing fact ranked 34/40 lost it
        entirely at share=0.25 (head 30), taking its hit rate from 1.000 to
        0.000. Across that sample 8 of 30 items had exactly ONE answer-bearing
        turn, so "costs a few of the least-relevant head slots" can mean
        "costs the whole answer" and is not a rare shape;
      * coverage only spends the reserved tail, and only on candidates that
        already passed the relevance filter;
      * with fewer candidates than the budget this never runs at all, so small
        stores behave exactly as before.

    It optimizes *coverage*, not distinct-day count — the day spread is a
    diagnostic of the problem, and selecting to maximise it would be selecting
    to look good on the diagnostic.
    """
    reserve = int(max_edges * coverage_share)
    head, tail = max_edges - reserve, []
    chosen = [e for _, e in scored[:head]]
    # specs/0001 I6 (candidate): reserved records count as covered days
    seen_days = {e.valid_from.date() for e in chosen} | (seed_days or set())
    rest = scored[head:]
    # first pass: highest-scoring candidate from each period not yet present
    for _, e in rest:
        if len(chosen) + len(tail) >= max_edges:
            break
        day = e.valid_from.date()
        if day not in seen_days:
            tail.append(e)
            seen_days.add(day)
    # backfill any unused reserve by relevance, so coverage never costs volume
    if len(chosen) + len(tail) < max_edges:
        picked = {id(e) for e in tail}
        for _, e in rest:
            if len(chosen) + len(tail) >= max_edges:
                break
            if id(e) not in picked:
                tail.append(e)
    return chosen + tail


def _outcome_note(e: Edge) -> str:
    """Outcome aggregates rendered as information for the reader — never
    gating: '(in use: 5×, 2 confirmed, 1 corrected)'. Unreviewed uses show
    only in the total (completion is not confirmation)."""
    if not e.times_used:
        return ""
    reviewed = [f"{n} {k}" for k, n in sorted(e.outcome_counts.items())
                if k != "unreviewed" and n > 0]
    detail = (", " + ", ".join(reviewed)) if reviewed else ""
    return f" (in use: {e.times_used}×{detail})"


# Origin labels for `use_only` material. Derived from provenance rather than
# hardcoded, because the string reaches the model as context and a CONFIDENTLY
# WRONG origin is worse than a missing one.
#
# Output is byte-identical to the previous hardcoded string for every author
# that can reach `use_only` today (THIRD_PARTY-authored, and USER/SYSTEM content
# capped by derived_from=THIRD_PARTY — in both cases the claim originates with a
# third party, so "third-party-reported" is accurate).
#
# It exists because a FOURTH author class is proposed (spec 0001,
# EvidenceAuthor.ASSISTANT, deferred). Under that spec every assistant edge sits
# at use_only, and the old hardcoded string would have told the model
# "third-party-reported" about assistant-generated text — an affirmatively false
# origin, in the one release whose entire purpose is stopping hosts from
# mislabelling assistant content. `_ORIGIN_LABELS` has no entry for a new author
# class, and `tests/test_render_origin.py` fails loudly if one appears without
# one. That converts a note in a deferred spec into a tripwire.
# specs/0001 I12 (candidate, R7-1): the §4b DECISION ORDER verbatim — the
# capping axis first, no author class inheriting another's label. The
# round-7 review executed the divergence: the first patch returned
# "third-party-reported" for the derived case the spec spells
# "third-party-derived", and kept USER/SYSTEM inheriting a label.
_ORIGIN_LABELS: dict[EvidenceAuthor, str] = {
    EvidenceAuthor.THIRD_PARTY: "third-party-reported",
    EvidenceAuthor.ASSISTANT: "assistant-generated",
}


def _origin_label(e: Edge) -> str:
    """Who this unverified material came from, in the model's words.

    specs/0001 I12 (candidate, Q5's ruling): the PAIR keys the label — the
    capping axis first. assistant+derived_from=THIRD_PARTY is a third
    party's claim relayed by the assistant, and must say so."""
    if e.provenance.derived_from == EvidenceAuthor.THIRD_PARTY:
        return "third-party-derived"
    label = _ORIGIN_LABELS.get(e.provenance.author_of_evidence)
    if label is None:
        # Fail SAFE, not confidently: an unlabelled author class must not
        # inherit another class's origin string.
        return "unverified-origin"
    return label


# --------------------------------------------------------------------------- #
# specs/0012 I8 — the read-path collapse. Render/selection-time ONLY (the O-Q2
# rule): the store keeps every edge; these functions choose what SURFACES.
# The governing principle (0012 §4c): suppress ONLY STRICT REDUNDANCY — never
# synthesize a representative, never guess between incomparable values, never
# hide a member that carries information any consumer reads.
# --------------------------------------------------------------------------- #

def _collapse_survivor_order(e: Edge):
    """The §4c total order: note-bearing → most specific value → freshest
    `observed_at` → lexicographic edge id (I8j — store-order invariance)."""
    return (0 if e.note else 1, -len(_value_key(e.object)),
            -e.provenance.observed_at.timestamp(), e.id)


def _strictly_redundant(m: Edge, survivor: Edge) -> bool:
    """True iff `m` adds NO carrier-visible information beyond the survivor
    (0012 §4c suppression predicate). The flag is handled by the caller's
    one-warning-carrier rule, not here."""
    return ((m.note == "" or m.note == survivor.note)
            and m.volatility == survivor.volatility
            and (m.times_used == 0 or m.times_used == survivor.times_used)
            and (not m.outcome_counts or m.outcome_counts == survivor.outcome_counts)
            and (m.last_outcome is None or m.last_outcome == survivor.last_outcome))


def value_groups(members: list[Edge]) -> dict:
    """UNIQUE-ANCHOR value grouping over one authority-envelope bucket (0012 §4c /
    I8d/I8e/I8i), shared by the render collapse AND the wiki compiler's group
    construction (R-impl3-2): anchors are the maximal values; a non-maximal value
    joins its anchor ONLY when exactly one anchor subsumes it; ambiguous (≥2) and
    zero-anchor values form their own groups. Returns {group_value_key: [edges]}."""
    by_vk: dict[tuple, list[Edge]] = {}
    for e in members:
        by_vk.setdefault(_value_key(e.object), []).append(e)
    vks = list(by_vk)
    anchors = [vk for vk in vks
               if not any(o != vk and _subsumes(o, vk) for o in vks)]
    groups: dict[tuple, list[Edge]] = {a: list(by_vk[a]) for a in anchors}
    for vk in vks:
        if vk in groups:
            continue
        holding = [a for a in anchors if _subsumes(a, vk)]
        if len(holding) == 1:                        # the only collapsing cell
            groups[holding[0]].extend(by_vk[vk])
        else:                                        # 0 or ≥2 → its own group
            groups[vk] = list(by_vk[vk])
    return groups


def collapse_for_render(edges: list[Edge]) -> tuple[list[Edge], dict]:
    """Collapse strictly-redundant ACTIVE duplicates for a model-facing surface
    (specs/0012 I8). Inactive/quarantined-history members pass through verbatim
    (I8b — history is never collapsed). Returns `(surfaced, info)`:

    - `surfaced`: the input list minus suppressed members, INPUT ORDER PRESERVED
      (the surfaced SET is store-order invariant, I8j; ordering is the caller's).
    - `info`: survivor edge id → {"since": earliest group `valid_from`,
      "hidden": suppressed count, "flagged_hidden": suppressed-flagged count} —
      the ONE permitted presentation-level aggregate (truthful render-time
      labels; nothing is mutated).

    Grouping (0012 §4c): key = (subject, relation, disclosure, author,
    derived_from) — the COMPLETE effective-authority envelope (I8f); within a
    key, UNIQUE-ANCHOR value grouping over `_value_key`/`_subsumes` with all
    three anchored-by cells {0 → alone, 1 → joins, ≥2 → alone} (I8d/I8e/I8i).
    Warning carrier: the survivor if flagged, else the freshest flagged member —
    exactly ONE per group per recall (I8h); other flagged-but-redundant members
    are suppressed and counted.
    """
    actives = [e for e in edges if e.active]
    suppressed: set[str] = set()
    info: dict[str, dict] = {}

    by_key: dict[tuple, list[Edge]] = {}
    for e in actives:
        k = (e.subject, e.relation, e.provenance.disclosure,
             e.provenance.author_of_evidence, e.provenance.derived_from)
        by_key.setdefault(k, []).append(e)

    for members in by_key.values():
        if len(members) < 2:
            continue
        groups = value_groups(members)

        for group in groups.values():
            if len(group) < 2:
                continue
            survivor = min(group, key=_collapse_survivor_order)
            flagged = [m for m in group if m.needs_confirmation]
            carrier = (survivor if survivor.needs_confirmation else
                       (max(flagged, key=lambda m:
                            (m.provenance.observed_at, m.id)) if flagged else None))
            hidden = flagged_hidden = 0
            for m in group:
                if m is survivor or m is carrier:
                    continue
                if m.needs_confirmation:
                    if _strictly_redundant(m, survivor):
                        suppressed.add(m.id)         # the ×N pin (I8h)
                        hidden += 1
                        flagged_hidden += 1
                    # a flagged member with distinct info surfaces (I8g)
                elif _strictly_redundant(m, survivor):
                    suppressed.add(m.id)
                    hidden += 1
            if hidden:
                info[survivor.id] = {
                    "since": min(m.valid_from for m in group),
                    "hidden": hidden, "flagged_hidden": flagged_hidden}

    if not suppressed:
        return list(edges), info
    return [e for e in edges if e.id not in suppressed], info


def render_edges(edges: list[Edge], since: Optional[dict] = None) -> str:
    """Render edges as provenance-carrying lines for a prompt. Quarantined claims
    are fenced with an explicit never-assert marker; superseded edges show their
    validity range so history is visible without polluting the current value.
    `since` (specs/0012 I8): optional {edge_id: datetime} of collapse-group
    earliest `valid_from`s — the truthful render-time label for a survivor whose
    suppressed duplicates include an earlier first-known date; mutates nothing."""
    lines = []
    for e in edges:
        if e.invalidation_reason == "absorbed_duplicate":
            # an absorbed value is the SAME fact as its active winner, not a
            # prior value of it — rendering it as history would show identity
            # as change. Still queryable via the store/Recall.edges.
            continue
        who = "" if e.subject == "user" else f"{e.subject} "
        note = f" — {e.note}" if e.note else ""
        # specs/0019 §4c: the marker rides EVERY branch a flagged fact renders
        # through (never severed — the 0012 clamp rule); the model sees the
        # doubt exactly where it sees the fact. The render layer's own
        # placement is the only authoritative one (N1) — marker text inside
        # event content is data and renders as content.
        ug = " [possible extraction error]" if e.ungrounded else ""
        if e.quarantined:
            lines.append(f"[UNVERIFIED third-party claim, never assert as fact] "
                         f"{e.subject} claims: {e.relation} {e.object}{ug}{note} ({e.valid_from.date()})")
        elif not e.active:
            lines.append(f"{who}{e.relation}: {e.object}{ug}{note} "
                         f"(SUPERSEDED {e.valid_from.date()}→{e.invalidated_at.date() if e.invalidated_at else '?'})")
        else:
            stale = " [possibly stale — confirm before relying on it]" if e.needs_confirmation else ""
            tp = f" [{_origin_label(e)}; unconfirmed]" if e.use_only else ""
            since_dt = (since or {}).get(e.id, e.valid_from)
            lines.append(f"{who}{e.relation}: {e.object}{ug}{note} (since {since_dt.date()})"
                         f"{_outcome_note(e)}{tp}{stale}")
    return "\n".join(lines)
